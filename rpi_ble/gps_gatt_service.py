from json import JSONEncoder
from tokenize import String
import logging

from gi.repository import GLib

import dbus
from math import isnan

from rpi_ble.constants import GPS_SERVICE_UUID, GPS_DATA_CHRC_UUID, GPS_DATA_DESCRIPTOR_UUID
from rpi_ble.gps_reader import GpsReader
from rpi_ble.interfaces import GpsReceiver
from rpi_ble.service import GattService, GattCharacteristic, GATT_CHRC_IFACE, Descriptor, NotifyDescriptor

logger = logging.getLogger(__name__)

class GpsGattService(GattService, GpsReceiver):
    """
    Send gps data on a frequent basis
    """

    def __init__(self, bus, index):
        GattService.__init__(self, bus, index, GPS_SERVICE_UUID, True)
        self.gps_characteristic = GpsChrc(bus, 0, self)
        self.add_characteristic(self.gps_characteristic)
        self.gps_thread = None
        self.gps_connected = False

    def set_gps_position(self, lat: float, long: float, heading: float, tstamp: float,
                         speed: int, gdop: float, pdop: float) -> None:
        self.gps_characteristic.set_gps_position(lat, long, heading, tstamp, speed, gdop, pdop)

    def set_gps_connected(self):
        self.gps_connected = True

    def start_gps_thread(self) -> None:
        if self.gps_connected and not self.gps_thread:
            self.gps_thread = GLib.Thread.new("gps-thread", run_gps_thread, self)

    def stop_gps_thread(self) -> None:
        pass

class GpsChrc(GattCharacteristic, GpsReceiver):
    # this is a general sensor

    def __init__(self, bus, index, service: GpsGattService):
        GattCharacteristic.__init__(
            self,
            bus,
            index,
            GPS_DATA_CHRC_UUID,
            ['notify', 'read'],
            service)
        self.add_descriptor(GpsDescriptor(bus, 0, self))
        self.add_descriptor(NotifyDescriptor(bus, 1, self))
        self.notifying = False
        self.gps_pos = GpsPos(0, 0, 0, 0, 0, 0, 0)
        self.service = service

    def set_gps_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int, gdop: float, pdop: float):
        self.gps_pos = GpsPos(lat, long, heading, tstamp, speed, gdop, pdop)
        value = self.ReadValue(None)

        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

        return self.notifying

    def StartNotify(self):
        logger.info("StartNotify called")
        if self.notifying:
            print('Already notifying, nothing to do')
            return
        else:
            self.service.start_gps_thread()

        self.notifying = True

    def StopNotify(self):
        logger.info("StopNotify called")
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False

    def ReadValue(self, options):
        value = []
        gps_str = self.gps_pos.toJSON()
        for c in gps_str:
            value.append(dbus.Byte(c.encode()))
        return value

class GpsPos:

    def __init__(self, lat: float, long: float, heading: float, tstamp: float,
                 speed: int, gdop: float, pdop: float ):
        self.lat = lat
        self.long = long
        self.heading = heading
        self.tstamp = tstamp
        self.speed = speed
        self.gdop = gdop
        self.pdop = pdop

    def __eq__(self, other):
        if isinstance(other, GpsPos):
            return self.toJSON() == other.toJSON()
        return False

    def toJSON(self) -> String:
        fields = {
            'lat': self.lat,
            'long': self.long,
            'hdg': self.heading,
            'tstamp': int(self.tstamp * 1000),
            'spd': self.speed,
            'gdop': 0.0 if isnan(self.gdop) else self.gdop,
            'pdop': 0.0 if isnan(self.pdop) else self.pdop,
        }
        return JSONEncoder().encode(fields)

class GpsDescriptor(Descriptor):
    GPS_DESCRIPTOR_VALUE = "GPS Position"

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
            self,
            bus,
            index,
            GPS_DATA_DESCRIPTOR_UUID,
            ["read"],
            characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.GPS_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

def run_gps_thread(service: GpsGattService):
    GpsReader(service).run()