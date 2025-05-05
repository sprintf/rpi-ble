from typing import Optional

from gps import *

from dateutil import parser
from threading import Thread

#todo : think about doing moving and not moving ... can save some battery on BLE maybe
import logging
import time
import os
import subprocess

from rpi_ble.event_defs import ExitApplicationEvent, GPSConnectedEvent, GPSDisconnectedEvent
from rpi_ble.interfaces import GpsReceiver
from rpi_ble.usb_detector import UsbDetector, UsbDevice

logger = logging.getLogger(__name__)


class GpsReader(Thread):

    def __init__(self, receiver: GpsReceiver, log_to_file=False):
        Thread.__init__(self, daemon=True)
        self.speed_mph = 999
        self.heading = 0
        self.working = False
        self.lat = 0.0
        self.long = 0.0
        self.log = log_to_file
        self.finished = False
        self.time_synced = False
        self.receiver = receiver
        ExitApplicationEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == ExitApplicationEvent:
            self.finished = True

    def run(self) -> None:
        while not self.finished:
            try:
                logger.info("connecting to GPS...")
                self.call_gpsctl()
                session = gps()
                self.init_gps_connection(session)

                while not self.finished:
                    try:
                        data = session.next()

                        if session.fix.time and str(session.fix.time) != "nan":
                            logger.debug("{} {} {} {} {} {}".
                                         format(session.fix.time,
                                                data['class'],
                                                session.fix.latitude,
                                                session.fix.longitude,
                                                session.gdop,
                                                session.pdop))
                            gps_datetime = parser.isoparse(session.fix.time).astimezone()
                            if gps_datetime.year < 2021:
                                logger.debug("time wonky, ignoring")
                                continue
                            gps_tstamp = gps_datetime.timestamp()
                            gps_tstamp2 = session.real_sec + session.real_nsec / 1.0e9
                            print(f"difference in time is {gps_tstamp} {gps_tstamp2} {abs(gps_tstamp - gps_tstamp2)} ")
                        else:
                            # we can't trust the onboard time anymore as we don't expect to have wifi
                            continue

                        if session.fix.status == STATUS_NO_FIX:
                            # losing a gps fix doesn't emit a GPSDisconnected event ..
                            # we can look into whether it should or not once we have empirical information
                            logger.warning("no fix...awaiting")
                            self.time_synced = False
                            # don't sleep as we want to quickly traverse these messages until we find one that is synced
                            # do need to test battery drain without this, but it should be fine.
                            # time.sleep(0.5)
                            continue

                        self.time_synced = True

                        if data['class'] == 'TPV':
                            # assuming its coming in m/s
                            if not math.isnan(session.fix.speed):
                                self.speed_mph = int(session.fix.speed * 2.237)
                                # if self.speed_mph < 3:
                                #     NotMovingEvent.emit(speed=self.speed_mph,
                                #                         lat_long=(session.fix.latitude, session.fix.longitude))
                                # else:
                                #     MovingEvent.emit(speed=self.speed_mph,
                                #                      lat_long=(session.fix.latitude, session.fix.longitude))
                            if not math.isnan(session.fix.track):
                                self.heading = int(session.fix.track)
                            if not math.isnan(session.fix.latitude):
                                self.lat = session.fix.latitude
                                self.long = session.fix.longitude
                                # generally we should try to move away from position listeners, and instead
                                # have them pull from this class when they need it
                                if self.receiver:
                                    start_time = time.time()
                                    try:
                                        self.receiver.set_gps_position(self.lat, self.long,
                                                                       self.heading, gps_tstamp,
                                                                       self.speed_mph,
                                                                       session.gdop, session.pdop)
                                    except Exception:
                                        logger.exception("issue with GPS listener.")
                                    finally:
                                        elapsed_ms = int(time.time() - start_time * 1000)
                                        if elapsed_ms > 50:
                                            logger.warning(f"position handling took {elapsed_ms} ms")
                                if not self.working:
                                    self.working = True
                                    GPSConnectedEvent.emit()
                    except KeyError:
                        # this happens when elevation is not included, we don't care
                        pass
            except Exception:
                logger.exception("issue with GPS, reconnecting.")
                self.working = False
                GPSDisconnectedEvent.emit()
                time.sleep(10)

    def is_working(self) -> bool:
        return self.working

    @staticmethod
    def init_gps_connection(session: gps):
        # read anything that's out there
        session.read()
        session.send('?DEVICES;')
        code = session.read()
        logger.debug(f"got code {code}")
        response = session.data
        logger.debug(f"got response {response}")
        devices = response['devices']
        if len(devices) == 0 or "'native': 1" in str(response):
            session.close()
            logger.warning(f"response = {response}")
            raise Exception("no gps device or it's in the wrong mode")
        session.send('?WATCH={"enable":true,"json":true}')

    def call_gpsctl(self):
        if True: # not settings.GPSCTL_ARGS:
            return
        # args = settings.GPSCTL_ARGS.split(" ")
        if UsbDetector.detected(UsbDevice.GPS):
            gps_device = UsbDetector.get(UsbDevice.GPS)
            logger.info(f"calling gpsctl with {['gpsctl', *args, gps_device]}")
            returncode = -1
            tries = 0
            while returncode != 0 and tries < 5:
                result = subprocess.run(["gpsctl", *args, gps_device],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.info(f"result of gpsctl = {result.returncode}")
                logger.info(result.stdout.decode("UTF-8").strip())
                logger.info(result.stderr.decode("UTF-8").strip())
                returncode = result.returncode
                tries += 1


if __name__ == "__main__":

    if "SETTINGS_MODULE" not in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_car"

    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)


    class FileLogger(GpsReceiver):

        def __init__(self):
            self.file = open("traces/trace-{}.csv".format(int(time.time())), mode="w")

        def set_gps_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int) -> None:
            diff = int((time.time() - tstamp) * 1000)
            print(f"diff between now and gps time = {diff}ms")
            #self.file.write("{},{},{},{},{}\n".format(tstamp, lat, long, heading, speed))
            #self.file.flush()


    UsbDetector.init()
    tracker = GpsReader(FileLogger())
    # tracker.call_gpsctl()
    tracker.run()
