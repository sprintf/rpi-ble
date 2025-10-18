
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import logging
import time
import argparse

from rpi_ble.event_defs import ExitApplicationEvent
from rpi_ble.obd_reader import ObdReader
from rpi_ble.gps_reader import GpsReader
from rpi_ble.synthetic_obd_reader import SyntheticObdReader
from rpi_ble.synthetic_gps_reader import SyntheticGpsReader
from rpi_ble.usb_detector import UsbDetector, UsbDevice

from rpi_ble.gatt_application import GattApplication, LemonPiAdvertisement

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

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