import unittest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock all Linux-specific modules
sys.modules['gi.repository'] = Mock()
sys.modules['gi.repository.GLib'] = Mock()
sys.modules['dbus'] = Mock()
sys.modules['dbus.service'] = Mock()
sys.modules['dbus.mainloop.glib'] = Mock()
sys.modules['dbus.exceptions'] = Mock()
sys.modules['obd'] = Mock()
sys.modules['gps'] = Mock()

class TestMainIntegration(unittest.TestCase):

    @patch('rpi_ble.main.UsbDetector')
    @patch('rpi_ble.main.dbus.SystemBus')
    @patch('rpi_ble.main.dbus.mainloop.glib.DBusGMainLoop')
    @patch('rpi_ble.main.GattApplication')
    @patch('rpi_ble.main.LemonPiAdvertisement')
    def test_main_application_setup(self, mock_ad_class, mock_app_class, mock_loop, mock_bus_class, mock_usb):
        """Test that main() properly sets up advertising integration"""
        
        # Setup mocks
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        mock_app.get_mainloop.return_value = Mock()
        
        mock_advertisement = Mock()
        mock_ad_class.return_value = mock_advertisement
        
        # Mock USB detection
        mock_usb.detected.return_value = False
        
        from rpi_ble.main import main
        
        try:
            # This will run until we interrupt it
            with patch.object(mock_app.get_mainloop(), 'run', side_effect=KeyboardInterrupt):
                main()
        except SystemExit:
            pass  # Expected from the interrupt handling
        
        # Verify integration steps
        mock_app.set_advertisement.assert_called_once_with(mock_advertisement)
        mock_app.start_advertising.assert_called_once()
        
        # Verify advertisement was created correctly
        mock_ad_class.assert_called_once_with(mock_bus, 0)

    @patch('rpi_ble.main.UsbDetector')
    @patch('rpi_ble.main.dbus.SystemBus')
    @patch('rpi_ble.main.dbus.mainloop.glib.DBusGMainLoop')
    @patch('rpi_ble.main.GattApplication')
    @patch('rpi_ble.main.LemonPiAdvertisement')
    @patch('rpi_ble.main.ExitApplicationEvent')
    def test_main_shutdown_sequence(self, mock_exit_event, mock_ad_class, mock_app_class, mock_loop, mock_bus_class, mock_usb):
        """Test that shutdown properly sends exit events"""
        
        # Setup mocks
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        mock_mainloop = Mock()
        mock_app.get_mainloop.return_value = mock_mainloop
        
        mock_advertisement = Mock()
        mock_ad_class.return_value = mock_advertisement
        
        mock_usb.detected.return_value = False
        
        # Make mainloop.run() raise KeyboardInterrupt to simulate Ctrl+C
        mock_mainloop.run.side_effect = KeyboardInterrupt("Test interrupt")
        
        from rpi_ble.main import main
        
        main()
        
        # Verify exit event was emitted
        mock_exit_event.emit.assert_called_once()

if __name__ == '__main__':
    unittest.main()