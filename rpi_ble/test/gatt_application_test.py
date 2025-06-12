import unittest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock all the Linux-specific modules
sys.modules['gi.repository'] = Mock()
sys.modules['gi.repository.GLib'] = Mock()
sys.modules['dbus'] = Mock()
sys.modules['dbus.service'] = Mock()
sys.modules['dbus.mainloop.glib'] = Mock()

from rpi_ble.gatt_application import GattApplication, properties_changed

class TestGattApplication(unittest.TestCase):

    def setUp(self):
        self.mock_bus = Mock()
        
    @patch('rpi_ble.gatt_application.DeviceStatusGattService')
    @patch('rpi_ble.gatt_application.ObdGattService') 
    @patch('rpi_ble.gatt_application.GpsGattService')
    def test_signal_receiver_setup(self, mock_gps, mock_obd, mock_status):
        app = GattApplication(self.mock_bus)
        
        # Verify signal receiver was registered
        self.mock_bus.add_signal_receiver.assert_called_once()
        call_args = self.mock_bus.add_signal_receiver.call_args
        
        # Check the callback function
        self.assertEqual(call_args[0][0], properties_changed)
        
        # Check the parameters
        kwargs = call_args[1]
        self.assertEqual(kwargs['dbus_interface'], 'org.freedesktop.DBus.Properties')
        self.assertEqual(kwargs['signal_name'], 'PropertiesChanged')
        self.assertIn('path_keyword', kwargs)

    def test_properties_changed_connect(self):
        # Test connection event
        with patch('rpi_ble.gatt_application.logger') as mock_logger:
            properties_changed(
                'org.bluez.Device1', 
                {'Connected': True}, 
                [], 
                '/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF'
            )
            mock_logger.info.assert_called_with(
                'BLE client connected: /org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF'
            )

    def test_properties_changed_disconnect(self):
        # Test disconnection event
        with patch('rpi_ble.gatt_application.logger') as mock_logger:
            properties_changed(
                'org.bluez.Device1', 
                {'Connected': False}, 
                [], 
                '/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF'
            )
            mock_logger.info.assert_called_with(
                'BLE client disconnected: /org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF'
            )

    def test_properties_changed_other_property(self):
        # Test other property changes
        with patch('rpi_ble.gatt_application.logger') as mock_logger:
            properties_changed(
                'org.bluez.Device1', 
                {'RSSI': -45}, 
                [], 
                '/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF'
            )
            mock_logger.debug.assert_called_with(
                'Device property changed on /org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF: {\'RSSI\': -45}'
            )

if __name__ == '__main__':
    unittest.main()