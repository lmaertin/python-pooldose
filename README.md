# python-pooldose
Unofficial async Python client for [SEKO](https://www.seko.com/) Pooldosing systems. SEKO is a manufacturer of various monitoring and control devices for Pools and Spas.
This client uses an undocumented local HTTP API. It provides live readings for pool sensors such as temperature, pH, ORP/Redox, as well as status information and control over the dosing logic.

## Features
- **Async/await support** for non-blocking operations
- **Dynamic sensor discovery** based on device model and firmware
- **Dictionary-style access** to instant values
- **Type-specific getters** for sensors, switches, numbers, selects
- **Secure by default** - WiFi passwords excluded unless explicitly requested
- **Comprehensive error handling** with detailed logging

## API Overview

### Program Flow

```
1. Create PooldoseClient
   ├── Fetch Device Info
   │   ├── Debug Config
   │   ├── WiFi Station Info (optional)
   │   ├── Access Point Info (optional)
   │   └── Network Info
   ├── Load Mapping JSON (based on MODEL_ID + FW_CODE)
   └── Query Available Types
       ├── Sensors
       ├── Binary Sensors
       ├── Numbers
       ├── Switches
       └── Selects

2. Get Instant Values
   └── Access Values via Dictionary Interface
       ├── instant_values['temperature']
       ├── instant_values.get('ph', default)
       └── 'sensor_name' in instant_values

3. Set Values via Type Methods
   ├── set_number()
   ├── set_switch()
   └── set_select()
```

### API Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PooldoseClient │────│ RequestHandler  │────│   HTTP Device   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │ API Endpoints   │
         │              │ • get_debug     │
         │              │ • get_wifi      │
         │              │ • get_values    │
         │              │ • set_value     │
         │              └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│   MappingInfo   │────│  JSON Files     │
└─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Type Discovery  │
│ • Sensors       │
│ • Switches      │
│ • Numbers       │
│ • Selects       │
└─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│  InstantValues  │────│ Dictionary API  │
└─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Type Methods    │
│ • set_number()  │
│ • set_switch()  │
│ • set_select()  │
└─────────────────┘
```

## Prerequisites
1. Install and set-up the PoolDose devices according to the user manual.
   1. In particular, connect the device to your WiFi network.
   2. Identify the IP address or hostname of the device.
2. Browse to the IP address or hostname (default port: 80).
   1. Try to log in to the web interface with the default password (0000).
   2. Check availability of data in the web interface.
3. Optionally: Block the device from internet access to ensure cloudless-only operation.

## Installation

```bash
pip install python-pooldose
```

## Example Usage

### Basic Example
```python
import asyncio
import json
from pooldose.client import PooldoseClient
from pooldose.request_handler import RequestStatus

HOST = "192.168.1.100"  # Change this to your device's host or IP address
TIMEOUT = 30

async def main() -> None:
    """Demonstrate PooldoseClient usage with new dictionary-based API."""
    
    # Create client instance (excludes WiFi passwords by default)
    client = PooldoseClient(host=HOST, timeout=TIMEOUT)
    
    # Optional: Include sensitive data like WiFi passwords
    # client = PooldoseClient(host=HOST, timeout=TIMEOUT, include_sensitive_data=True)
    
    # Connect to device
    status = await client.connect()
    if status != RequestStatus.SUCCESS:
        print(f"Error connecting to device: {status}")
        return
    
    print(f"Connected to {HOST}")
    print("Device Info:", json.dumps(client.device_info, indent=2))

    # --- Query available types dynamically ---
    print("\nAvailable types:")
    for typ, keys in client.available_types().items():
        print(f"  {typ}: {keys}")

    # --- Query available sensors ---
    print("\nAvailable sensors:")
    for name, sensor in client.available_sensors().items():
        print(f"  {name}: key={sensor.key}, type={sensor.type}")
        if sensor.conversion is not None:
            print(f"    conversion: {sensor.conversion}")

    # --- Get static values ---
    status, static_values = client.static_values()
    if status == RequestStatus.SUCCESS:
        print(f"Device Name: {static_values.sensor_name}")
        print(f"Serial Number: {static_values.sensor_serial_number}")
        print(f"Firmware Version: {static_values.sensor_fw_version}")

    # --- Get instant values ---
    status, instant_values = await client.instant_values()
    if status != RequestStatus.SUCCESS:
        print(f"Error getting instant values: {status}")
        return

    # --- Dictionary-style access ---
    
    # Get all sensors at once
    print("\nAll sensor values:")
    sensors = instant_values.get_sensors()
    for key, value in sensors.items():
        if isinstance(value, tuple) and len(value) >= 2:
            print(f"  {key}: {value[0]} {value[1]}")

    # Dictionary-style individual access
    if "temperature" in instant_values:
        temp = instant_values["temperature"]
        print(f"Temperature: {temp[0]} {temp[1]}")

    # Get with default
    ph_value = instant_values.get("ph", "Not available")
    print(f"pH: {ph_value}")

    # --- Setting values ---
    
    # Set number values
    if "ph_target" in instant_values.get_numbers():
        result = await instant_values.set_number("ph_target", 7.2)
        print(f"Set pH target to 7.2: {result}")

    # Set switch values
    if "stop_pool_dosing" in instant_values.get_switches():
        result = await instant_values.set_switch("stop_pool_dosing", True)
        print(f"Set stop pool dosing: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Usage

#### Connection Management
```python
# Recommended: Separate initialization and connection
client = PooldoseClient("192.168.1.100", timeout=30)
status = await client.connect()

# Check connection status
if client.is_connected:
    print("Client is connected")
else:
    print("Client is not connected")
```

#### Error Handling
```python
from pooldose.request_handler import RequestStatus

client = PooldoseClient("192.168.1.100")
status = await client.connect()

if status == RequestStatus.SUCCESS:
    print("Connected successfully")
elif status == RequestStatus.HOST_UNREACHABLE:
    print("Could not reach device")
elif status == RequestStatus.PARAMS_FETCH_FAILED:
    print("Failed to fetch device parameters")
elif status == RequestStatus.API_VERSION_UNSUPPORTED:
    print("Unsupported API version")
else:
    print(f"Other error: {status}")
```

## API Reference

### PooldoseClient

#### Constructor
```python
PooldoseClient(host, timeout=10, include_sensitive_data=False)
```

**Parameters:**
- `host` (str): The hostname or IP address of the device
- `timeout` (int): Request timeout in seconds (default: 10)
- `include_sensitive_data` (bool): Whether to include sensitive data like WiFi passwords (default: False)

#### Methods
- `connect()` - Connect to device and initialize all components
- `static_values()` - Get static device information
- `instant_values()` - Get current sensor readings and device state
- `available_types()` - Get all available entity types
- `available_sensors()` - Get available sensor configurations
- `available_binary_sensors()` - Get available binary sensor configurations
- `available_numbers()` - Get available number configurations
- `available_switches()` - Get available switch configurations  
- `available_selects()` - Get available select configurations

#### Properties
- `is_connected` - Check if client is connected to device
- `device_info` - Dictionary containing device information
- `host` - Device hostname or IP address
- `timeout` - Request timeout in seconds

### InstantValues

#### Dictionary Interface
```python
# Reading
value = instant_values["sensor_name"]
value = instant_values.get("sensor_name", default)
exists = "sensor_name" in instant_values

# Writing (async)
await instant_values.__setitem__("switch_name", True)
```

#### Type-specific Methods
```python
# Getters
sensors = instant_values.get_sensors()
binary_sensors = instant_values.get_binary_sensors()
numbers = instant_values.get_numbers()
switches = instant_values.get_switches()
selects = instant_values.get_selects()

# Setters (async, with validation)
await instant_values.set_number("ph_target", 7.2)
await instant_values.set_switch("stop_dosing", True)
await instant_values.set_select("water_meter_unit", 1)
```

## Supported Devices

This client has been tested with:
- **PoolDose Double/Dual WiFi** (Model: PDPR1H1HAW100, FW: 539187)

Other SEKO PoolDose models may work but are untested. The client uses JSON mapping files to adapt to different device models and firmware versions (see e.g. `src/pooldose/mappings/model_PDPR1H1HAW100_FW539187.json`).

> **Note:** The other JSON files in the `docs/` directory define the default English names for the data keys of the PoolDose devices. These mappings are used for display and documentation purposes.

## Security

By default, the client excludes sensitive information like WiFi passwords from device info. To include sensitive data:

```python
client = PooldoseClient(
    host="192.168.1.100", 
    include_sensitive_data=True
)
status = await client.connect()
```

## Changelog

### [0.4.0] - 2025-07-11
- **BREAKING**: Removed `create()` factory method
- **BREAKING**: Changed client initialization pattern to separate `__init__` and async `connect()` methods
- Added `is_connected` property to check connection status
- Improved flexibility for testing and connection management
- Simplified RequestHandler by removing factory method pattern
- Changed default timeout to 30s
- Improved unit handling (No Unit is 'None')

### [0.3.1] - 2025-07-04
- First official release, published on PyPi
- Install with ```pip install python-pooldose```

### [0.3.0] - 2025-07-02
- **BREAKING**: Changed from dataclass properties to dictionary-based access for instant values
- Added dynamic sensor discovery based on device mapping files
- Added type-specific getter methods (get_sensors, get_switches, etc.)
- Added type-specific setter methods with validation (set_number, set_switch, etc.)
- Added dictionary-style access (__getitem__, __setitem__, get, __contains__)
- Added configurable sensitive data handling (excludes WiFi passwords by default)
- Improved async file loading to prevent event loop blocking
- Enhanced error handling and logging
- Added comprehensive type annotations

### [0.2.0] - 2024-06-25
- Added query feature to list all available sensors and actuators

### [0.1.5] - 2024-06-24
- First working prototype for PoolDose Double/Dual WiFi supported
- All sensors and actuators for PoolDose Double/Dual WiFi supported