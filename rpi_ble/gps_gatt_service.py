from json import JSONEncoder
from os import fdopen
from tokenize import String

import dbus

from rpi_ble.constants import GPS_SERVICE_UUID, GPS_DATA_CHRC_UUID, GPS_DATA_DESCRIPTOR_UUID
from rpi_ble.interfaces import GpsReceiver
from rpi_ble.service import GattService, GattCharacteristic, GATT_CHRC_IFACE, Descriptor, NotifyDescriptor

class GpsGattService(GattService, GpsReceiver):
    """
    Send gps data on a frequent basis
    """

    def __init__(self, bus, index):
        GattService.__init__(self, bus, index, GPS_SERVICE_UUID, True)
        self.gps_characteristic = GpsChrc(bus, 0, self)
        self.add_characteristic(self.gps_characteristic)
        self.energy_expended = 0

    def set_gps_position(self, lat: float, long: float, heading: float, tstamp: float,
                         speed: int, gdop: float, pdop: float) -> None:
        self.gps_characteristic.set_gps_position(lat, long, heading, tstamp, speed, gdop, pdop)

class GpsChrc(GattCharacteristic, GpsReceiver):
    # this is a general sensor

    def __init__(self, bus, index, service):
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

    def set_gps_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int, gdop: float, pdop: float):
        self.gps_pos = GpsPos(lat, long, heading, tstamp, speed, gdop, pdop)
        value = self.ReadValue(None)

        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True

    def StopNotify(self):
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
            'tstamp': self.tstamp,
            'spd': self.speed,
            'gdop': self.gdop,
            'pdop': self.pdop,
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


