import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys
import time

# Mock all the Linux-specific modules before importing
sys.modules['gi.repository'] = Mock()
sys.modules['gi.repository.GLib'] = Mock()
sys.modules['dbus'] = Mock()
sys.modules['dbus.service'] = Mock()
sys.modules['dbus.mainloop.glib'] = Mock()
sys.modules['dbus.exceptions'] = Mock()

# Mock all service modules
sys.modules['rpi_ble.device_status_gatt_service'] = Mock()
sys.modules['rpi_ble.gps_gatt_service'] = Mock()
sys.modules['rpi_ble.obd_gatt_service'] = Mock()
sys.modules['rpi_ble.service'] = Mock()
sys.modules['rpi_ble.constants'] = Mock()
sys.modules['rpi_ble.utils'] = Mock()

from rpi_ble.gatt_application import GattApplication

class TestConnectionManagement(unittest.TestCase):

    def setUp(self):
        self.mock_bus = Mock()
        self.mock_glib = Mock()
        sys.modules['gi.repository'].GLib = self.mock_glib
        
        # Create the application - services are already mocked
        self.app = GattApplication(self.mock_bus)

    def test_initial_state(self):
        """Test that application starts with no connections and no advertising"""
        self.assertEqual(len(self.app.connected_devices), 0)
        self.assertFalse(self.app.is_advertising)
        self.assertIsNone(self.app.advertisement)

    def test_signal_receiver_setup(self):
        """Test that signal receiver is properly configured"""
        self.mock_bus.add_signal_receiver.assert_called_once()
        call_args = self.mock_bus.add_signal_receiver.call_args
        
        # Check callback function
        self.assertEqual(call_args[0][0], self.app._properties_changed)
        
        # Check parameters
        kwargs = call_args[1]
        self.assertEqual(kwargs['dbus_interface'], 'org.freedesktop.DBus.Properties')
        self.assertEqual(kwargs['signal_name'], 'PropertiesChanged')
        self.assertIn('path_keyword', kwargs)

    def test_set_advertisement(self):
        """Test setting advertisement object"""
        mock_ad = Mock()
        self.app.set_advertisement(mock_ad)
        self.assertEqual(self.app.advertisement, mock_ad)

class TestAdvertisingBehavior(unittest.TestCase):

    def setUp(self):
        self.mock_bus = Mock()
        self.mock_glib = Mock()
        sys.modules['gi.repository'].GLib = self.mock_glib
        
        # Create the application - services are already mocked
        self.app = GattApplication(self.mock_bus)
        
        self.mock_advertisement = Mock()
        self.app.set_advertisement(self.mock_advertisement)

    def test_start_advertising_success(self):
        """Test successful advertising start"""
        self.app.start_advertising()
        
        self.mock_advertisement.register.assert_called_once_with(self.mock_bus)
        self.assertTrue(self.app.is_advertising)

    def test_start_advertising_already_running(self):
        """Test that start_advertising does nothing when already advertising"""
        self.app.is_advertising = True
        self.app.start_advertising()
        
        self.mock_advertisement.register.assert_not_called()

    def test_start_advertising_no_advertisement(self):
        """Test start_advertising with no advertisement set"""
        self.app.advertisement = None
        self.app.start_advertising()
        
        self.assertFalse(self.app.is_advertising)

    @patch('rpi_ble.gatt_application.logger')
    def test_start_advertising_error(self, mock_logger):
        """Test start_advertising handles errors gracefully"""
        self.mock_advertisement.register.side_effect = Exception("Registration failed")
        
        self.app.start_advertising()
        
        mock_logger.error.assert_called_once()
        self.assertFalse(self.app.is_advertising)

    @patch('rpi_ble.gatt_application.find_adapter')
    @patch('rpi_ble.gatt_application.dbus.Interface')
    def test_stop_advertising_success(self, mock_interface, mock_find_adapter):
        """Test successful advertising stop"""
        mock_find_adapter.return_value = "/org/bluez/hci0"
        mock_ad_manager = Mock()
        mock_interface.return_value = mock_ad_manager
        
        self.app.is_advertising = True
        self.app.stop_advertising()
        
        mock_ad_manager.UnregisterAdvertisement.assert_called_once_with(
            self.mock_advertisement.get_path()
        )
        self.assertFalse(self.app.is_advertising)

    def test_stop_advertising_not_running(self):
        """Test stop_advertising does nothing when not advertising"""
        self.app.is_advertising = False
        
        with patch('rpi_ble.gatt_application.find_adapter') as mock_find_adapter:
            self.app.stop_advertising()
            mock_find_adapter.assert_not_called()

    @patch('rpi_ble.gatt_application.find_adapter')
    @patch('rpi_ble.gatt_application.logger')
    def test_stop_advertising_error(self, mock_logger, mock_find_adapter):
        """Test stop_advertising handles errors gracefully"""
        mock_find_adapter.side_effect = Exception("Adapter error")
        self.app.is_advertising = True
        
        self.app.stop_advertising()
        
        mock_logger.error.assert_called_once()

class TestConnectionEvents(unittest.TestCase):

    def setUp(self):
        self.mock_bus = Mock()
        self.mock_glib = Mock()
        sys.modules['gi.repository'].GLib = self.mock_glib
        
        with patch('rpi_ble.gatt_application.DeviceStatusGattService'), \
             patch('rpi_ble.gatt_application.GpsGattService'), \
             patch('rpi_ble.gatt_application.ObdGattService'):
            self.app = GattApplication(self.mock_bus)
        
        self.mock_advertisement = Mock()
        self.app.set_advertisement(self.mock_advertisement)
        self.device_path = "/org/bluez/hci0/dev_12_34_56_AB_CD_EF"

    @patch('rpi_ble.gatt_application.logger')
    def test_client_connection_stops_advertising(self, mock_logger):
        """Test that client connection stops advertising"""
        self.app.is_advertising = True
        
        with patch.object(self.app, 'stop_advertising') as mock_stop:
            self.app._properties_changed(
                "org.bluez.Device1",
                {"Connected": True},
                [],
                self.device_path
            )
        
        mock_stop.assert_called_once()
        self.assertIn(self.device_path, self.app.connected_devices)
        mock_logger.info.assert_called_with(f"BLE client connected: {self.device_path}")

    @patch('rpi_ble.gatt_application.logger')
    def test_client_disconnection_triggers_readvertising(self, mock_logger):
        """Test that client disconnection triggers re-advertising"""
        # Setup: client is connected
        self.app.connected_devices.add(self.device_path)
        
        self.app._properties_changed(
            "org.bluez.Device1",
            {"Connected": False},
            [],
            self.device_path
        )
        
        self.assertNotIn(self.device_path, self.app.connected_devices)
        mock_logger.info.assert_any_call(f"BLE client disconnected: {self.device_path}")
        mock_logger.info.assert_any_call("Client disconnected, restarting advertising")
        
        # Verify GLib timeout was set
        self.mock_glib.timeout_add.assert_called_once_with(1000, self.app._restart_advertising)

    def test_restart_advertising_when_no_clients(self):
        """Test _restart_advertising only advertises when no clients connected"""
        self.app.connected_devices.clear()
        
        with patch.object(self.app, 'start_advertising') as mock_start:
            result = self.app._restart_advertising()
        
        mock_start.assert_called_once()
        self.assertFalse(result)  # Should return False to not repeat timeout

    def test_restart_advertising_with_connected_clients(self):
        """Test _restart_advertising skips when clients still connected"""
        self.app.connected_devices.add(self.device_path)
        
        with patch.object(self.app, 'start_advertising') as mock_start:
            result = self.app._restart_advertising()
        
        mock_start.assert_not_called()
        self.assertFalse(result)

    @patch('rpi_ble.gatt_application.logger')
    def test_multiple_client_connections(self, mock_logger):
        """Test handling multiple client connections (single client enforcement)"""
        device1 = "/org/bluez/hci0/dev_12_34_56_AB_CD_E1"
        device2 = "/org/bluez/hci0/dev_12_34_56_AB_CD_E2"
        
        # First client connects
        self.app._properties_changed("org.bluez.Device1", {"Connected": True}, [], device1)
        self.assertEqual(len(self.app.connected_devices), 1)
        
        # Second client connects (should be tracked but advertising already stopped)
        self.app._properties_changed("org.bluez.Device1", {"Connected": True}, [], device2)
        self.assertEqual(len(self.app.connected_devices), 2)

    @patch('rpi_ble.gatt_application.logger')
    def test_partial_disconnection(self, mock_logger):
        """Test that re-advertising only happens when ALL clients disconnect"""
        device1 = "/org/bluez/hci0/dev_12_34_56_AB_CD_E1"
        device2 = "/org/bluez/hci0/dev_12_34_56_AB_CD_E2"
        
        # Connect two clients
        self.app.connected_devices.add(device1)
        self.app.connected_devices.add(device2)
        
        # First client disconnects
        self.app._properties_changed("org.bluez.Device1", {"Connected": False}, [], device1)
        
        # Should not trigger re-advertising since device2 still connected
        self.mock_glib.timeout_add.assert_not_called()

    @patch('rpi_ble.gatt_application.logger')
    def test_non_connection_property_changes(self, mock_logger):
        """Test that non-connection property changes are logged but ignored"""
        self.app._properties_changed(
            "org.bluez.Device1",
            {"RSSI": -45},
            [],
            self.device_path
        )
        
        mock_logger.debug.assert_called_with(
            f"Device property changed on {self.device_path}: {{'RSSI': -45}}"
        )
        self.assertEqual(len(self.app.connected_devices), 0)

    @patch('rpi_ble.gatt_application.logger')
    def test_non_device_interface_changes(self, mock_logger):
        """Test that non-device interface changes are logged appropriately"""
        self.app._properties_changed(
            "org.bluez.Adapter1",
            {"Powered": True},
            [],
            "/org/bluez/hci0"
        )
        
        mock_logger.debug.assert_called_with(
            "Property changed: org.bluez.Adapter1 on /org/bluez/hci0: {'Powered': True}"
        )

if __name__ == '__main__':
    unittest.main()