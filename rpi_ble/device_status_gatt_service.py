import dbus
import logging

from gi.repository import GLib

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
        self.update_pending = False
        OBDConnectedEvent.register_handler(self)
        OBDDisconnectedEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == OBDConnectedEvent:
            self.obd_connected = True
        elif event == OBDDisconnectedEvent:
            self.obd_connected = False
        else:
            logger.warning("unknown event")
        # Schedule D-Bus call on main thread to avoid blocking
        # Only schedule if no update is already pending
        if not self.update_pending:
            self.update_pending = True
            GLib.idle_add(self._notify_property_changed)

    def _notify_property_changed(self):
        value = self.ReadValue(None)
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
        self.update_pending = False
        return False  # Don't repeat this idle callback

    def StartNotify(self):
        if self.notifying:
            logger.info('Already notifying, nothing to do')
            return

        self.notifying = True

    def StopNotify(self):
        if not self.notifying:
            logger.info('Not notifying, nothing to do')
            return

        self.notifying = False

    def ReadValue(self, options):
        return [dbus.Byte(1 if self.obd_connected else 0)]

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
        self.update_pending = False
        GPSConnectedEvent.register_handler(self)
        GPSDisconnectedEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == GPSConnectedEvent:
            self.gps_connected = True
        elif event == GPSDisconnectedEvent:
            self.gps_connected = False
        else:
            logger.warning("unknown event")
        # Schedule D-Bus call on main thread to avoid blocking
        # Only schedule if no update is already pending
        if not self.update_pending:
            self.update_pending = True
            GLib.idle_add(self._notify_property_changed)

    def _notify_property_changed(self):
        value = self.ReadValue(None)
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
        self.update_pending = False
        return False  # Don't repeat this idle callback

    def StartNotify(self):
        logger.info("StartNotify called")
        if self.notifying:
            logger.info('Already notifying, nothing to do')
            return

        self.notifying = True

    def StopNotify(self):
        logger.info("StopNotify called")
        if not self.notifying:
            logger.info('Not notifying, nothing to do')
            return

        self.notifying = False

    def ReadValue(self, options):
        return [dbus.Byte(1 if self.gps_connected else 0)]

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







