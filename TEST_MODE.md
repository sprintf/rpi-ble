# Test Mode

## Overview

The application now supports a **test mode** that allows you to run the BLE GATT server with synthetic GPS and OBD-II data, eliminating the need for physical hardware (Raspberry Pi connected to a car and GPS device) during development and testing.

## Usage

### Running in Test Mode

To start the application in test mode, use the `--test-mode` flag:

```bash
python rpi_ble/main.py --test-mode
```

### Normal Mode (Default)

To run with real hardware (default behavior):

```bash
python rpi_ble/main.py
```

## What Test Mode Does

When test mode is enabled:

1. **No USB device detection** - The application doesn't check for connected GPS or OBD-II USB devices
2. **Synthetic GPS data** - Generates realistic GPS coordinates simulating a vehicle moving in a circular pattern
3. **Synthetic OBD data** - Generates realistic engine temperature and fuel level data

### Synthetic GPS Data

The synthetic GPS reader (`SyntheticGpsReader`) provides:

- **Location**: Circular path around San Francisco Bay Area (center: 37.7749°N, 122.4194°W)
- **Speed**: Varies between 20-40 mph
- **Heading**: Changes as the vehicle follows the circular path
- **Update rate**: Once per second
- **GPS accuracy** (GDOP/PDOP): Realistic varying values

### Synthetic OBD Data

The synthetic OBD reader (`SyntheticObdReader`) provides:

- **Engine temperature**:
  - Starts at ambient (68°F)
  - Warms up logarithmically to operating temperature (195-220°F)
  - Includes realistic oscillations
  - Updates every 10 seconds

- **Fuel level**:
  - Starts at 75%
  - Slowly decreases (~1% per 5 minutes)
  - Updates every 10 seconds

## Testing Without BLE

You can test the synthetic readers independently without requiring BLE or D-Bus:

```bash
python test_synthetic.py
```

This script runs the synthetic GPS and OBD readers for 15 seconds and verifies they generate data correctly.

## Implementation Details

### Files Added

- `rpi_ble/synthetic_gps_reader.py` - Synthetic GPS data generator
- `rpi_ble/synthetic_obd_reader.py` - Synthetic OBD-II data generator
- `test_synthetic.py` - Standalone test script

### Files Modified

- `rpi_ble/main.py` - Added `--test-mode` argument parsing and conditional logic
- `rpi_ble/gatt_application.py` - Added `test_mode` parameter to constructor
- `rpi_ble/gps_gatt_service.py` - Added `test_mode` support and synthetic reader integration
- `rpi_ble/obd_gatt_service.py` - Added `test_mode` support and synthetic reader integration

### Architecture

The synthetic readers follow the same interface as the real readers:

- Implement the same receiver interfaces (`GpsReceiver`, `ObdReceiver`)
- Run as background daemon threads
- Support graceful shutdown via `ExitApplicationEvent`
- Emit connection events (`GPSConnectedEvent`, `OBDConnectedEvent`)

## Benefits

1. **Easy development** - Test BLE functionality without physical hardware
2. **Predictable data** - Consistent, reproducible test scenarios
3. **No dependencies** - No need for car, GPS device, or Raspberry Pi during development
4. **Faster iteration** - Quick testing cycles without hardware setup

## Future Enhancements

Potential improvements to test mode:

- Command-line options to customize synthetic data (location, speed, temperature, etc.)
- Multiple predefined movement patterns (straight line, figure-8, etc.)
- Simulate error conditions (GPS loss, OBD disconnection)
- Configuration file for test scenarios
- Record and replay real data traces
