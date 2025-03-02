
from constants import SERVICE_UUID, CHAR_UUID

import sys
import signal
from bluepy.btle import Peripheral, DefaultDelegate, ADDR_TYPE_RANDOM
from bluepy.btle import UUID, Service, Characteristic, Descriptor
import struct

FIXED_STRING = "123"


class MyPeripheral(Peripheral):
    def __init__(self):
        Peripheral.__init__(self)
        self.service = None
        self.characteristic = None


class MyDelegate(DefaultDelegate):
    def __init__(self, peripheral):
        DefaultDelegate.__init__(self)
        self.peripheral = peripheral

    def handleNotification(self, cHandle, data):
        print(f"Notification from handle {cHandle}: {data}")

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print(f"Discovered device {dev.addr}")
        elif isNewData:
            print(f"Received new data from {dev.addr}")

    def handleRead(self, cHandle):
        print(f"Read request for handle {cHandle}")
        # For our fixed string characteristic
        if self.peripheral.characteristic and cHandle == self.peripheral.characteristic.getHandle():
            print(f"Returning fixed string: {FIXED_STRING}")
            return FIXED_STRING.encode()
        return None


def register_service(peripheral):
    """Register our service with BlueZ"""
    try:
        # Add service
        peripheral.service = Service(UUID(SERVICE_UUID), True)

        # Add characteristic
        peripheral.characteristic = Characteristic(
            UUID(CHAR_UUID),
            Characteristic.PROP_READ,
            Characteristic.PERM_READ,
            FIXED_STRING.encode()
        )

        # Add the characteristic to the service
        peripheral.service.addCharacteristic(peripheral.characteristic)

        # Add the service to the peripheral
        peripheral.addService(peripheral.service)

        print(f"Service {SERVICE_UUID} registered")
        print(f"Characteristic {CHAR_UUID} added with value: {FIXED_STRING}")

    except Exception as e:
        print(f"Error registering service: {e}")
        peripheral.disconnect()
        sys.exit(1)


def signal_handler(sig, frame):
    """Handle keyboard interrupt"""
    print("Ctrl+C pressed. Shutting down...")
    if p:
        p.disconnect()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    p = MyPeripheral()
    delegate = MyDelegate(p)
    p.withDelegate(delegate)

    # Register our service and characteristic
    register_service(p)

    # Advertise our service
    # advertise_service()

    print("BLE service is now running. Press Ctrl+C to exit.")
    try:
        while True:
            if p.waitForNotifications(1.0):
                continue
            # Do any additional background processing here
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if p:
            p.disconnect()