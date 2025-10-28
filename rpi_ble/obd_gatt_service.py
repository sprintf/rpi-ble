import dbus
import logging
import threading

from gi.repository import GLib

from rpi_ble.constants import OBD_SERVICE_UUID, ENGINE_TEMP_CHRC_UUID, FUEL_LEVEL_CHRC_UUID
from rpi_ble.interfaces import TemperatureReceiver, FuelLevelReceiver, FuelLevelReceiver
from rpi_ble.obd_reader import ObdReader
from rpi_ble.service import GattService, GattCharacteristic, GATT_CHRC_IFACE, Descriptor, NotifyDescriptor

logger = logging.getLogger(__name__)

class ObdGattService(GattService, TemperatureReceiver, FuelLevelReceiver):
    """
    Send obd data on a frequent basis
    """

    def __init__(self, bus, index, test_mode=False):
        GattService.__init__(self, bus, index, OBD_SERVICE_UUID, True)
        self.engine_temp_characteristic = EngineTempObdChrc(bus, 0, self)
        self.fuel_level_characteristic = FuelLevelObdChrc(bus, 1, self)
        self.add_characteristic(self.engine_temp_characteristic)
        self.add_characteristic(self.fuel_level_characteristic)
        self.obd_thread = None
        self.obd_connected = False
        self.test_mode = test_mode

    def set_temp_f(self, temperature: int) -> None:
        self.engine_temp_characteristic.set_temp_f(temperature)

    def set_fuel_percent_remaining(self, percent: int) -> None:
        self.fuel_level_characteristic.set_fuel_percent_remaining(percent)

    def set_obd_connected(self):
        self.obd_connected = True

    def start_obd_thread(self) -> None:
        if self.obd_connected and not self.obd_thread:
            self.obd_thread = GLib.Thread.new("obd-thread", run_obd_thread, self)

    def stop_obd_thread(self) -> None:
        pass


class EngineTempObdChrc(GattCharacteristic, TemperatureReceiver):

    def __init__(self, bus, index, service: ObdGattService):
        GattCharacteristic.__init__(
            self, bus, index,
            ENGINE_TEMP_CHRC_UUID,
            ['notify', 'read'],
            service)
        self.add_descriptor(EngineTempObdDescriptor(bus, 0, self))
        self.add_descriptor(NotifyDescriptor(bus, 1, self))
        self.notifying = False
        self.temp_f = 0
        self.service = service
        self.update_pending = False

    def set_temp_f(self, temperature: int):
        self.temp_f = temperature
        # Only schedule if no update is already pending
        if not self.update_pending:
            self.update_pending = True
            logger.debug("Queueing engine temperature property change notification to GLib main loop")
            GLib.idle_add(self._notify_property_changed)
        return self.notifying

    def _notify_property_changed(self):
        logger.info("Executing engine temperature property change notification")
        logger.info("doing it")
        value = self.ReadValue(None)
        self.update_pending = False
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
        return False  # Don't repeat this idle callback

    def StartNotify(self):
        logger.info("StartNotify called")
        if self.notifying:
            print('Already notifying, nothing to do')
            return
        else:
            self.service.start_obd_thread()

        self.notifying = True

    def StopNotify(self):
        logger.info("StopNotify called")
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False

    def ReadValue(self, options):
        value = []
        value.append(dbus.Int32(self.temp_f))
        return value

class FuelLevelObdChrc(GattCharacteristic, FuelLevelReceiver):

    def __init__(self, bus, index, service):
        GattCharacteristic.__init__(
            self, bus, index,
            FUEL_LEVEL_CHRC_UUID,
            ['notify'],
            service)
        self.add_descriptor(FuelLevelObdDescriptor(bus, 0, self))
        self.add_descriptor(NotifyDescriptor(bus, 1, self))
        self.notifying = False
        # self.lock = threading.Lock()
        self.fuel_level = 0
        self.service = service
        self.update_pending = False

    def set_fuel_percent_remaining(self, percent: int):
        self.fuel_level = percent
        # Only schedule if no update is already pending
        if not self.update_pending:
            self.update_pending = True
            logger.debug("Queueing fuel level property change notification to GLib main loop")
            GLib.idle_add(self._notify_property_changed)
        return self.notifying

    def _notify_property_changed(self):
        logger.info("Executing fuel level property change notification")
        logger.info("doing it")
        value = self.ReadValue(None)
        self.update_pending = False
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
        return False  # Don't repeat this idle callback

    def StartNotify(self):
        if self.notifying:
            logger.info('Already notifying, nothing to do')
            return
        else:
            self.service.start_obd_thread()

        self.notifying = True

    def StopNotify(self):
        if not self.notifying:
            logger.info('Not notifying, nothing to do')
            return

        self.notifying = False

    def ReadValue(self, options):
        value = []
        value.append(dbus.Int32(self.fuel_level))
        return value

class EngineTempObdDescriptor(Descriptor):
    TEMP_DESCRIPTOR_UUID = "2901"
    TEMP_DESCRIPTOR_VALUE = "Engine Temperature"

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
            self,
            bus,
            index,
            self.TEMP_DESCRIPTOR_UUID,
            ["read"],
            characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.TEMP_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


class FuelLevelObdDescriptor(Descriptor):
    FUEL_LEVEL_DESCRIPTOR_UUID = "2901"   # I made this up
    FUEL_LEVEL_DESCRIPTOR_VALUE = "Fuel Level"

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
            self,
            bus,
            index,
            self.FUEL_LEVEL_DESCRIPTOR_UUID,
            ["read"],
            characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.FUEL_LEVEL_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

def run_obd_thread(service: ObdGattService):
    if service.test_mode:
        from rpi_ble.synthetic_obd_reader import SyntheticObdReader
        logger.info("Starting synthetic OBD reader thread")
        SyntheticObdReader(service).run()
    else:
        ObdReader(service).run()



