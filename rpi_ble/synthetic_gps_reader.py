import logging
import time
import math
from threading import Thread

from rpi_ble.event_defs import ExitApplicationEvent, GPSConnectedEvent
from rpi_ble.interfaces import GpsReceiver

logger = logging.getLogger(__name__)


class SyntheticGpsReader(Thread):
    """
    Synthetic GPS reader that generates realistic GPS data for testing.
    Simulates a vehicle moving in a circular pattern.
    """

    def __init__(self, receiver: GpsReceiver):
        Thread.__init__(self, daemon=True)
        self.receiver = receiver
        self.finished = False
        self.working = True

        # Starting position (San Francisco Bay Area as example)
        self.center_lat = 37.7749
        self.center_long = -122.4194

        # Movement parameters
        self.radius = 0.01  # ~1km radius in degrees
        self.angular_velocity = 0.1  # radians per second
        self.current_angle = 0.0

        ExitApplicationEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == ExitApplicationEvent:
            self.finished = True

    def run(self) -> None:
        logger.info("Starting synthetic GPS reader")

        # Emit connected event immediately
        GPSConnectedEvent.emit()

        while not self.finished:
            try:
                # Calculate current position in circular path
                self.current_angle += self.angular_velocity
                if self.current_angle > 2 * math.pi:
                    self.current_angle -= 2 * math.pi

                # Calculate lat/long offset
                lat = self.center_lat + self.radius * math.sin(self.current_angle)
                long = self.center_long + self.radius * math.cos(self.current_angle)

                # Calculate heading (direction of travel)
                heading = int((self.current_angle * 180 / math.pi + 90) % 360)

                # Simulate speed (20-40 mph)
                speed = int(30 + 10 * math.sin(self.current_angle * 0.5))

                # Current timestamp
                tstamp = time.time()

                # Simulate reasonable GPS accuracy values
                gdop = 1.5 + 0.5 * math.sin(self.current_angle * 2)
                pdop = 1.2 + 0.3 * math.sin(self.current_angle * 3)

                # Send data to receiver
                if self.receiver:
                    self.receiver.set_gps_position(
                        lat, long, heading, tstamp, speed, gdop, pdop
                    )

                logger.debug(f"Synthetic GPS: lat={lat:.6f}, long={long:.6f}, "
                           f"heading={heading}, speed={speed}mph")

                # Update once per second
                time.sleep(1.0)

            except Exception:
                logger.exception("Error in synthetic GPS reader")
                time.sleep(1.0)

        logger.info("Synthetic GPS reader stopped")

    def is_working(self) -> bool:
        return self.working
