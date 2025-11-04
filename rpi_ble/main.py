
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import logging
from logging.handlers import RotatingFileHandler
import time
import argparse
import os

from rpi_ble.event_defs import ExitApplicationEvent
from rpi_ble.usb_detector import UsbDetector, UsbDevice

from rpi_ble.gatt_application import GattApplication, LemonPiAdvertisement

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)


class FlushingRotatingFileHandler(RotatingFileHandler):
    """
    RotatingFileHandler that flushes after every log message.
    Critical for devices that may lose power suddenly (like car accessories).
    """
    def emit(self, record):
        super().emit(record)
        self.flush()


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Console handler - DEBUG level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s %(name)s %(message)s',
                                     datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(console_formatter)

# File handler - INFO level, 1MB max, 10 backup files
# Uses FlushingRotatingFileHandler to ensure logs are written immediately
# This is critical since the device may lose power suddenly
file_handler = FlushingRotatingFileHandler('logs/rpi-ble.log',
                                           maxBytes=1024*1024,  # 1MB
                                           backupCount=10)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

mainloop = None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Lemon-Pi BLE GATT Server')
    parser.add_argument('--test-mode', action='store_true',
                        help='Run with synthetic GPS and OBD data for testing')
    args = parser.parse_args()

    if args.test_mode:
        logger.info("*** RUNNING IN TEST MODE WITH SYNTHETIC DATA ***")
    else:
        logger.info("starting up")

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    logger.info("initializing application")
    app = GattApplication(bus, test_mode=args.test_mode)

    mainloop = app.get_mainloop()

    if args.test_mode:
        # In test mode, enable both services and start synthetic readers
        logger.info("Enabling synthetic GPS and OBD services")
        app.get_gps_service().set_gps_connected()
        app.get_obd_service().set_obd_connected()
    else:
        # read USB devices
        logger.info("checking USB devices")
        UsbDetector.init()

        # enable devices based on USB
        if UsbDetector.detected(UsbDevice.GPS):
            app.get_gps_service().set_gps_connected()
        if UsbDetector.detected(UsbDevice.OBD):
            app.get_obd_service().set_obd_connected()

    logger.info('Registering GATT application...')

    app.register_application(bus)

    logger.info('BLE service is now running ')

    advertisement = LemonPiAdvertisement(bus, 0)
    app.set_advertisement(advertisement)
    app.start_advertising()

    logger.info('Press Ctrl+C to exit')
    try:
        mainloop.run()
    except KeyboardInterrupt:
        logger.info("Shutting down due to CTRL-C")

    # Clean up BlueZ and D-Bus resources
    logger.info("Cleaning up BlueZ and D-Bus resources")
    app.cleanup()

    # tell everything we're shutting down
    logger.info("sending shutdown notification")
    ExitApplicationEvent.emit()
    time.sleep(1)
    logger.info("Shutdown Complete. Good Bye!")

if __name__ == '__main__':
    main()