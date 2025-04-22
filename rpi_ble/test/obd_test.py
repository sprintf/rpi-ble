import unittest
from unittest.mock import Mock

import sys

import dbus

sys.modules['gi.repository'] = Mock()
sys.modules['gpiozero'] = Mock()

from rpi_ble.service import GattCharacteristic, Descriptor

from rpi_ble.obd_gatt_service import ObdGattService, EngineTempObdChrc, FuelLevelObdChrc


class TestObd(unittest.TestCase):

    def test_construction(self) :
        bus = Mock()
        service = ObdGattService(bus, 0)
        self.assertEqual(bus, service.bus)
        self.assertEqual("/org/bluez/lemonpi/service0", service.get_path())
        char0: GattCharacteristic = service.get_characteristics()[0]
        self.assertEqual("/org/bluez/lemonpi/service0/char0", char0.get_path())
        self.assertListEqual(["notify", "read"], char0.flags)
        self.assertEqual(bus, char0.bus)
        self.assertEqual(service, char0.service)
        desc0: Descriptor = char0.descriptors[0]
        self.assertEqual("/org/bluez/lemonpi/service0/char0/desc0", desc0.get_path())
        self.assertListEqual(["read"], desc0.flags)
        self.assertEqual(bus, desc0.bus)
        self.assertEqual(char0, desc0.chrc)
        desc1: Descriptor = char0.descriptors[1]
        self.assertEqual("/org/bluez/lemonpi/service0/char0/desc1", desc1.get_path())
        self.assertListEqual(["read"], desc0.flags)
        self.assertEqual(bus, desc0.bus)
        self.assertEqual(char0, desc0.chrc)

    def test_engine_temp_serialization(self):
        bus = Mock()
        service = ObdGattService(bus, 0)
        service.set_temp_f(32)
        engine_temp_chr: EngineTempObdChrc = service.characteristics[0]
        self.assertEqual(32, engine_temp_chr.temp_f)
        self.assertListEqual( [dbus.Byte(51), dbus.Byte(50)], engine_temp_chr.ReadValue(None))

        service.set_temp_f(250)
        self.assertEqual(250, engine_temp_chr.temp_f)
        self.assertListEqual([dbus.Byte(50), dbus.Byte(53), dbus.Byte(48)], engine_temp_chr.ReadValue(None))

        service.set_temp_f(350)
        self.assertEqual(350, engine_temp_chr.temp_f)
        self.assertListEqual([dbus.Byte(51), dbus.Byte(53), dbus.Byte(48)], engine_temp_chr.ReadValue(None))

    def test_fuel_level_serialization(self):
        bus = Mock()
        service = ObdGattService(bus, 0)
        service.set_fuel_percent_remaining(100)
        fuel_level_chr: FuelLevelObdChrc = service.characteristics[1]
        self.assertEqual(100, fuel_level_chr.fuel_level)
        self.assertListEqual( [dbus.Byte(49), dbus.Byte(48), dbus.Byte(48)], fuel_level_chr.ReadValue(None))

        service.set_fuel_percent_remaining(50)
        self.assertEqual(50, fuel_level_chr.fuel_level)
        self.assertListEqual([dbus.Byte(53), dbus.Byte(48)], fuel_level_chr.ReadValue(None))

        service.set_fuel_percent_remaining(10)
        self.assertEqual(10, fuel_level_chr.fuel_level)
        self.assertListEqual([dbus.Byte(49), dbus.Byte(48)], fuel_level_chr.ReadValue(None))

