# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

This is a Raspberry Pi BLE (Bluetooth Low Energy) project that creates a GATT server to advertise GPS and OBD-II data over Bluetooth.

### Environment Setup
```bash
python -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
```

### Running the Application
```bash
python rpi_ble/main.py
```

### Running Tests
```bash
python -m unittest discover rpi_ble/test
```

## Architecture

The application creates a BLE GATT server that advertises as "Lemon-Pi Device" and exposes three main services:

1. **GPS Service** (`GpsGattService`) - Exposes GPS coordinates, speed, heading from USB GPS device
2. **OBD Service** (`ObdGattService`) - Exposes vehicle data (temperature, fuel level) from OBD-II adapter  
3. **Device Status Service** (`DeviceStatusGattService`) - Reports connection status of USB devices

### Key Components

- `GattApplication` - Main GATT server application managing all services
- `ObdReader` / `GpsReader` - Background threads reading from USB devices
- `UsbDetector` - Detects connected GPS and OBD-II USB devices
- Event system using custom event definitions for component communication
- Interface-based design with receiver patterns for data flow

### USB Device Detection

The application automatically detects GPS and OBD-II USB devices on startup and enables corresponding services. Services track connection status and start/stop background reader threads as devices are connected/disconnected.

### Threading Model

- Main thread runs GLib mainloop for BLE/DBus operations
- Separate daemon threads for GPS and OBD-II data reading
- Event-driven communication between threads using custom event system

### Dependencies

- D-Bus and BlueZ for BLE GATT server functionality
- `obd` library for OBD-II communication
- `gps` library for GPS data parsing
- GLib/GObject for main event loop