import dbus

from interfaces import TemperatureReceiver, FuelLevelReceiver, FuelLevelReceiver
from rpi_ble.service import GattService, GattCharacteristic, GATT_CHRC_IFACE


class ObdGattService(GattService, TemperatureReceiver, FuelLevelReceiver):
    """
    Send gps data on a frequent basis
    """
    # todo : get a real UUID for this
    OBD_UUID = '0000180d-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index):
        GattService.__init__(self, bus, index, self.GPS_UUID, True)
        self.engine_temp_characteristic = EngineTempObdChrc(bus, 0, self)
        self.fuel_level_characteristic = FuelLevelObdChrc(bus, 1, self)
        self.add_characteristic(self.engine_temp_characteristic)
        self.add_characteristic(self.fuel_level_characteristic)
        self.energy_expended = 0

    def set_temp_f(self, temperature: int) -> None:
        self.engine_temp_characteristic.set_temp_f(temperature)

    def set_fuel_percent_remaining(self, percent: int) -> None:
        self.fuel_level_characteristic.set_fuel_percent_remaining(percent)

class EngineTempObdChrc(GattCharacteristic, TemperatureReceiver):
    # TODO : get a real UUID
    ENGINE_TEMP_UUID = '00002a37-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, service):
        GattCharacteristic.__init__(
            self, bus, index,
            self.ENGINE_TEMP_UUID,
            ['notify'],
            service)
        self.notifying = False
        self.hr_ee_count = 0

    def set_temp_f(self, temperature: int):
        value = []
        value.append(dbus.UInt32(int))
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

class FuelLevelObdChrc(GattCharacteristic, FuelLevelReceiver):
    # TODO : get a real UUID
    FUEL_LEVEL_UUID = '00002a37-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, service):
        GattCharacteristic.__init__(
            self, bus, index,
            self.FUEL_LEVEL_UUID,
            ['notify'],
            service)
        self.notifying = False
        self.hr_ee_count = 0

    def set_fuel_percent_remaining(self, percent: int):
        value = []
        # todo : whats the ox06 for?
        #  0x06 means there's one value following
        #  0x0E means there's another 2 bytes as well
        value.append(dbus.Byte(0x06))

        value.append(dbus.UInt32(percent))

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

