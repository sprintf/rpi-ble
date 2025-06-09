import dbus
import logging

from rpi_ble.constants import DEVICE_STATUS_SERVICE_UUID, OBD_CONNECTED_CHRC_UUID, GPS_CONNECTED_CHRC_UUID, \
    OBD_CONNECTED_DESCRIPTOR_UUID, GPS_CONNECTED_DESCRIPTOR_UUID
from rpi_ble.event_defs import OBDConnectedEvent, OBDDisconnectedEvent, GPSDisconnectedEvent, GPSConnectedEvent
from rpi_ble.events import EventHandler
from rpi_ble.service import GattService, GattCharacteristic, GATT_CHRC_IFACE, Descriptor, NotifyDescriptor

logger = logging.getLogger(__name__)

class DeviceStatusGattService(GattService):
    """
    Send status on what devices are connected and operating
    """

    def __init__(self, bus, index):
        GattService.__init__(self, bus, index, DEVICE_STATUS_SERVICE_UUID, True)
        self.add_characteristic(ObdConnectedChrc(bus, 0, self))
        self.add_characteristic(GpsConnectedChrc(bus, 1, self))


class ObdConnectedChrc(GattCharacteristic, EventHandler):

    def __init__(self, bus, index, service):
        GattCharacteristic.__init__(
            self, bus, index,
            OBD_CONNECTED_CHRC_UUID,
            ['notify', 'read'],
            service)
        self.add_descriptor(ObdConnectedDescriptor(bus, 0, self))
        self.add_descriptor(NotifyDescriptor(bus, 1, self))
        self.notifying = False
        self.obd_connected: bool = False
        OBDConnectedEvent.register_handler(self)
        OBDDisconnectedEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == OBDConnectedEvent:
            self.obd_connected = True
        elif event == OBDDisconnectedEvent:
            self.obd_connected = False
        else:
            logger.warning("unknown event")
        value = self.ReadValue(None)
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

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
        connected = chr(int(self.obd_connected))
        value.append(dbus.Byte(connected.encode()))
        return value

class GpsConnectedChrc(GattCharacteristic, EventHandler):

    def __init__(self, bus, index, service):
        GattCharacteristic.__init__(
            self, bus, index,
            GPS_CONNECTED_CHRC_UUID,
            ['notify', 'read'],
            service)
        self.add_descriptor(GpsConnectedDescriptor(bus, 0, self))
        self.add_descriptor(NotifyDescriptor(bus, 1, self))
        self.notifying = False
        self.gps_connected: bool = False
        GPSConnectedEvent.register_handler(self)
        GPSDisconnectedEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == GPSConnectedEvent:
            self.gps_connected = True
        elif event == GPSDisconnectedEvent:
            self.gps_connected = False
        else:
            logger.warning("unknown event")
        value = self.ReadValue(None)
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

    def StartNotify(self):
        logger.info("StartNotify called")
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True

    def StopNotify(self):
        logger.info("StopNotify called")
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False

    def ReadValue(self, options):
        value = []
        connected = chr(int(self.gps_connected))
        value.append(dbus.Byte(connected.encode()))
        return value

class ObdConnectedDescriptor(Descriptor):
    OBD_CONNECTED_DESCRIPTOR_VALUE = "OBD Connection Status"

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
            self,
            bus,
            index,
            OBD_CONNECTED_DESCRIPTOR_UUID,
            ["read"],
            characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.OBD_CONNECTED_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

class GpsConnectedDescriptor(Descriptor):
    GPS_CONNECTED_DESCRIPTOR_VALUE = "GPS Connection Status"

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
            self,
            bus,
            index,
            GPS_CONNECTED_DESCRIPTOR_UUID,
            ["read"],
            characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.GPS_CONNECTED_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value







