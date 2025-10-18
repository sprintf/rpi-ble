import logging
import time
import math
from threading import Thread

from rpi_ble.event_defs import ExitApplicationEvent, OBDConnectedEvent
from rpi_ble.interfaces import ObdReceiver

logger = logging.getLogger(__name__)


class SyntheticObdReader(Thread):
    """
    Synthetic OBD reader that generates realistic vehicle data for testing.
    Simulates engine temperature warming up and fuel consumption.
    """

    def __init__(self, receiver: ObdReceiver):
        Thread.__init__(self, daemon=True)
        self.receiver = receiver
        self.finished = False
        self.working = True

        # Initial values
        self.temp_f = 68  # Starting at ambient temperature
        self.fuel_level = 75  # Start at 75% fuel
        self.start_time = time.time()

        ExitApplicationEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == ExitApplicationEvent:
            self.finished = True

    def run(self) -> None:
        logger.info("Starting synthetic OBD reader")

        # Emit connected event immediately
        OBDConnectedEvent.emit()

        while not self.finished:
            try:
                elapsed = time.time() - self.start_time

                # Simulate engine warming up over ~10 minutes to operating temperature
                # Operating temp around 195-220°F, warm up follows logarithmic curve
                target_temp = 205
                warmup_rate = 0.01  # How quickly it warms up
                self.temp_f = int(68 + (target_temp - 68) * (1 - math.exp(-warmup_rate * elapsed)))

                # Add small oscillations to make it more realistic
                self.temp_f += int(5 * math.sin(elapsed * 0.1))

                # Keep temperature in reasonable range
                self.temp_f = max(68, min(220, self.temp_f))

                # Simulate fuel consumption (very slowly decrease)
                # Lose about 1% every 5 minutes
                fuel_consumed = elapsed / 300  # 300 seconds = 5 minutes per percent
                self.fuel_level = max(0, int(75 - fuel_consumed))

                # Send data to receiver
                if self.receiver:
                    self.receiver.set_temp_f(self.temp_f)
                    self.receiver.set_fuel_percent_remaining(self.fuel_level)

                logger.debug(f"Synthetic OBD: temp={self.temp_f}°F, fuel={self.fuel_level}%")

                # Update every 10 seconds (matching real OBD refresh rate)
                time.sleep(10.0)

            except Exception:
                logger.exception("Error in synthetic OBD reader")
                time.sleep(10.0)

        logger.info("Synthetic OBD reader stopped")

    def is_working(self) -> bool:
        return self.working
