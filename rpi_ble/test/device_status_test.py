import time
import unittest
from json import JSONDecoder
from unittest.mock import Mock

import sys

import dbus

from rpi_ble.event_defs import OBDConnectedEvent, GPSConnectedEvent, OBDDisconnectedEvent, GPSDisconnectedEvent

sys.modules['gi.repository'] = Mock()
sys.modules['gpiozero'] = Mock()

from rpi_ble.service import GattCharacteristic, Descriptor, GATT_CHRC_IFACE

from rpi_ble.device_status_gatt_service import DeviceStatusGattService


class TestDeviceStatus(unittest.TestCase):

    def test_construction(self) :
        bus = Mock()
        service = DeviceStatusGattService(bus, 0)
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

    def test_connected_serialization(self):
        bus = Mock()
        service = DeviceStatusGattService(bus, 0)
        obd = service.get_characteristics()[0]
        gps = service.get_characteristics()[1]
        obd.PropertiesChanged = Mock()
        gps.PropertiesChanged = Mock()
        self.assertEqual(False, obd.obd_connected)
        self.assertEqual(False, gps.gps_connected)
        OBDConnectedEvent.emit()
        obd.PropertiesChanged.assert_called_with(GATT_CHRC_IFACE, {'Value': [dbus.Byte(1)]}, [] )
        self.assertEqual(True, obd.obd_connected)
        self.assertEqual(False, gps.gps_connected)
        GPSConnectedEvent.emit()
        gps.PropertiesChanged.assert_called_with(GATT_CHRC_IFACE, {'Value': [dbus.Byte(1)]}, [] )
        self.assertEqual(True, obd.obd_connected)
        self.assertEqual(True, gps.gps_connected)
        OBDDisconnectedEvent.emit()
        obd.PropertiesChanged.assert_called_with(GATT_CHRC_IFACE, {'Value': [dbus.Byte(0)]}, [] )
        self.assertEqual(False, obd.obd_connected)
        self.assertEqual(True, gps.gps_connected)
        GPSDisconnectedEvent.emit()
        gps.PropertiesChanged.assert_called_with(GATT_CHRC_IFACE, {'Value': [dbus.Byte(0)]}, [] )
        self.assertEqual(False, obd.obd_connected)
        self.assertEqual(False, gps.gps_connected)

