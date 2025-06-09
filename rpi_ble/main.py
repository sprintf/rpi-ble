
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import logging
import time

from rpi_ble.interfaces import ObdReceiver
from rpi_ble.event_defs import ExitApplicationEvent
from rpi_ble.obd_reader import ObdReader
from rpi_ble.gps_reader import GpsReader
from rpi_ble.usb_detector import UsbDetector, UsbDevice

from rpi_ble.gatt_application import GattApplication, LemonPiAdvertisement

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

mainloop = None

def main():

    logger.info("starting up")
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    logger.info("initializing application")
    app = GattApplication(bus)

    mainloop = app.get_mainloop()

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

    LemonPiAdvertisement(bus, 0).register(bus)

    logger.info('Press Ctrl+C to exit')
    try:
        mainloop.run()
    except KeyboardInterrupt:
        logger.info("Shutting down due to CTRL-C")

    # tell everything we're shutting down
    logger.info("sending shutdown notification")
    ExitApplicationEvent.emit()
    time.sleep(1)
    logger.info("Shutdown Complete. Good Bye!")

if __name__ == '__main__':
    main()