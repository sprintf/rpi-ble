#!/usr/bin/env python3
"""
Simple test script to verify synthetic readers work correctly.
This runs independently without requiring BLE or D-Bus.
"""

import logging
import time
from rpi_ble.synthetic_gps_reader import SyntheticGpsReader
from rpi_ble.synthetic_obd_reader import SyntheticObdReader
from rpi_ble.interfaces import GpsReceiver, ObdReceiver

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


class TestGpsReceiver(GpsReceiver):
    """Test GPS receiver that prints received data"""

    def __init__(self):
        self.data_count = 0

    def set_gps_position(self, lat: float, long: float, heading: float,
                        tstamp: float, speed: int, gdop: float, pdop: float) -> None:
        self.data_count += 1
        logger.info(f"GPS #{self.data_count}: lat={lat:.6f}, long={long:.6f}, "
                   f"heading={heading}°, speed={speed}mph, gdop={gdop:.2f}, pdop={pdop:.2f}")


class TestObdReceiver(ObdReceiver):
    """Test OBD receiver that prints received data"""

    def __init__(self):
        super().__init__(None)
        self.temp_count = 0
        self.fuel_count = 0

    def set_temp_f(self, temperature: int) -> None:
        self.temp_count += 1
        logger.info(f"OBD Temp #{self.temp_count}: {temperature}°F")

    def set_fuel_percent_remaining(self, percent: int) -> None:
        self.fuel_count += 1
        logger.info(f"OBD Fuel #{self.fuel_count}: {percent}%")


def main():
    logger.info("=" * 60)
    logger.info("Testing Synthetic GPS and OBD Readers")
    logger.info("=" * 60)

    # Create receivers
    gps_receiver = TestGpsReceiver()
    obd_receiver = TestObdReceiver()

    # Create and start synthetic readers
    logger.info("\nStarting synthetic readers...")
    gps_reader = SyntheticGpsReader(gps_receiver)
    obd_reader = SyntheticObdReader(obd_receiver)

    gps_reader.start()
    obd_reader.start()

    # Run for 15 seconds
    logger.info("\nRunning for 15 seconds...\n")
    time.sleep(15)

    # Verify data was received
    logger.info("\n" + "=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)
    logger.info(f"GPS data received: {gps_receiver.data_count} times")
    logger.info(f"OBD temp data received: {obd_receiver.temp_count} times")
    logger.info(f"OBD fuel data received: {obd_receiver.fuel_count} times")

    if gps_receiver.data_count > 0 and obd_receiver.temp_count > 0:
        logger.info("\n✓ SUCCESS: Synthetic readers are working!")
    else:
        logger.error("\n✗ FAILURE: No data received from readers")

    logger.info("\nStopping readers...")
    # The threads will clean up automatically when the script exits


if __name__ == '__main__':
    main()
