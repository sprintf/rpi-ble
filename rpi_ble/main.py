
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import logging
import time


from interfaces import ObdReceiver
from event_defs import ExitApplicationEvent
from obd_reader import ObdReader
from gps_reader import GpsReader
from usb_detector import UsbDetector, UsbDevice
from service import *

logger = logging.getLogger(__name__)


def main():

    logger.info("starting up")
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    logger.info("initializing application")
    app = Application(bus)

    mainloop = app.get_mainloop()

    # read USB devices
    logger.info("checking USB devices")
    UsbDetector.init()

    # if there's a GPS device then fire up a thread to read it
    gps_thread = None
    if UsbDetector.detected(UsbDevice.GPS):
        gps_thread = GpsReader(app.get_gps_service())
        gps_thread.start()

    # if there's an OBD device then fire up a thread to read it
    obd_thread = None
    if UsbDetector.detected(UsbDevice.OBD):
        obd_thread = ObdReader(ObdReceiver(app.get_obd_servics()))
        obd_thread.start()

    logger.info('Registering GATT application...')

    app.register_application(bus)

    logger.info('BLE service is now running ')
    logger.info('Press Ctrl+C to exit')
    try:
        mainloop.run()
    except KeyboardInterrupt:
        logger.info("Shutting down due to CTRL-C")

    # tell everything we're shutting down
    logger.info("sending shurtown notification")
    ExitApplicationEvent.emit()
    time.sleep(1)
    logger.info("Shutdown Complete. Good Bye!")

if __name__ == '__main__':
    main()