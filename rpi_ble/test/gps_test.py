import time
import unittest
from json import JSONDecoder
from unittest.mock import Mock

import sys

import dbus
import math

sys.modules['gi.repository'] = Mock()
sys.modules['gpiozero'] = Mock()

from rpi_ble.service import GattCharacteristic, Descriptor

from rpi_ble.gps_gatt_service import GpsGattService, GpsChrc, GpsPos


class TestGps(unittest.TestCase):

    def test_construction(self) :
        bus = Mock()
        service = GpsGattService(bus, 0)
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

    def test_gps_serialization(self):
        bus = Mock()
        service = GpsGattService(bus, 0)
        now = time.time()
        service.set_gps_position(32.2, -32.2, 0.5, now, 10, 1.2, 1.5)
        expected = GpsPos(32.2, -32.2, 0.5, now, 10, 1.2, 1.5)
        gps_chr: GpsChrc = service.characteristics[0]
        self.assertEqual(expected, gps_chr.gps_pos)
        gps_ser = gps_chr.ReadValue(None)
        result_str = ''.join(str(byte_string) for byte_string in gps_ser)
        result = JSONDecoder().decode(result_str)
        print(result)

    def test_gps_serialization2(self):
        bus = Mock()
        service = GpsGattService(bus, 0)
        now = time.time()
        service.set_gps_position(32.2, -32.2, 0.5, now, 10, math.nan, math.nan)
        expected = GpsPos(32.2, -32.2, 0.5, now, 10, 0.0, 0.0)
        gps_chr: GpsChrc = service.characteristics[0]
        self.assertEqual(expected, gps_chr.gps_pos)
        gps_ser = gps_chr.ReadValue(None)
        result_str = ''.join(str(byte_string) for byte_string in gps_ser)
        result = JSONDecoder().decode(result_str)
        print(result)