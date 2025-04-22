import unittest
from unittest.mock import Mock

import sys

sys.modules['gi.repository'] = Mock()
sys.modules['gpiozero'] = Mock()

from rpi_ble.service import GattCharacteristic, Descriptor

from rpi_ble.temp_gatt_service import ThermometerGattService


class TestThermometer(unittest.TestCase):

    def test_construction(self) :
        bus = Mock()
        service = ThermometerGattService(bus, 0)
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

        char1: GattCharacteristic = service.get_characteristics()[1]
        self.assertEqual("/org/bluez/lemonpi/service0/char1", char1.get_path())
        self.assertListEqual(["read", "write"], char1.flags)
        self.assertEqual(bus, char1.bus)
        self.assertEqual(service, char1.service)
        desc1: Descriptor = char1.descriptors[0]
        self.assertEqual("/org/bluez/lemonpi/service0/char1/desc0", desc1.get_path())
        self.assertListEqual(["read"], desc1.flags)
        self.assertEqual(bus, desc1.bus)
        self.assertEqual(char1, desc1.chrc)