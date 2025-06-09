import dbus
import logging

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

    def __init__(self, bus, index):
        GattService.__init__(self, bus, index, OBD_SERVICE_UUID, True)
        self.engine_temp_characteristic = EngineTempObdChrc(bus, 0, self)
        self.fuel_level_characteristic = FuelLevelObdChrc(bus, 1, self)
        self.add_characteristic(self.engine_temp_characteristic)
        self.add_characteristic(self.fuel_level_characteristic)
        self.obd_thread = None
        self.obd_connected = False

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

    def set_temp_f(self, temperature: int):
        self.temp_f = temperature
        value = []
        value.append(dbus.Int32(self.temp_f))
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

        return self.notifying

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
        strtemp = str(self.temp_f)
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))
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
        self.fuel_level = 0
        self.service = service

    def set_fuel_percent_remaining(self, percent: int):
        self.fuel_level = percent
        value = self.ReadValue(None)
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return
        else:
            self.service.start_obd_thread()

        self.notifying = True

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False

    def ReadValue(self, options):
        value = []
        strtemp = str(self.fuel_level)
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))
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
    ObdReader(service).run()



