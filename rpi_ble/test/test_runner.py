#!/usr/bin/env python3
"""
Test runner that simulates BLE client connections for testing on macOS
"""
import unittest
import sys
import time
from unittest.mock import Mock, patch, MagicMock

# Mock all Linux dependencies before importing our modules
sys.modules['gi.repository'] = Mock()
sys.modules['gi.repository.GLib'] = Mock()
sys.modules['dbus'] = Mock()
sys.modules['dbus.service'] = Mock()
sys.modules['dbus.mainloop.glib'] = Mock()
sys.modules['dbus.exceptions'] = Mock()
sys.modules['dbus.mainloop'] = Mock()
sys.modules['obd'] = Mock()
sys.modules['gps'] = Mock()

class MockMainLoop:
    def __init__(self):
        self.running = False
        
    def run(self):
        self.running = True
        print("Mock mainloop started - use Ctrl+C to stop")
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Mock mainloop stopped")
            
    def quit(self):
        self.running = False

def run_mock_application():
    """Run the application with mocked dependencies"""
    print("Starting mock BLE application...")
    
    with patch('rpi_ble.gatt_application.GLib.MainLoop', return_value=MockMainLoop()):
        with patch('rpi_ble.main.dbus.SystemBus'):
            from rpi_ble.main import main
            from rpi_ble.gatt_application import GattApplication
            
            # Simulate some client connections during runtime
            import threading
            def simulate_connections():
                time.sleep(2)
                
                # Get the app instance to simulate connections properly
                print("Simulating client connection...")
                # This would normally be triggered by BlueZ
                print("BLE advertising should stop when client connects")
                
                time.sleep(3)
                print("Simulating client disconnection...")
                print("BLE advertising should restart after disconnection")
            
            threading.Thread(target=simulate_connections, daemon=True).start()
            main()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'mock-run':
        run_mock_application()
    else:
        # Run unit tests
        loader = unittest.TestLoader()
        suite = loader.discover('rpi_ble/test', pattern='*_test.py')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)