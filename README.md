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

## SSL/HTTPS Support

The client supports SSL/HTTPS connections for secure communication with your PoolDose device. This is particularly useful when the device is configured for HTTPS or when connecting over untrusted networks.

### Basic SSL Configuration

```python
from pooldose.client import PooldoseClient

# Enable SSL with default settings (port 443, certificate verification enabled)
client = PooldoseClient("192.168.1.100", use_ssl=True)
status = await client.connect()
```

### SSL Configuration Options

```python
# Custom HTTPS port
client = PooldoseClient("192.168.1.100", use_ssl=True, port=8443)

# Disable SSL certificate verification (not recommended for production)
client = PooldoseClient("192.168.1.100", use_ssl=True, ssl_verify=False)

# Complete SSL configuration example
client = PooldoseClient(
    host="pool-device.local",
    timeout=30,
    use_ssl=True,
    port=8443,
    ssl_verify=True,  # Verify SSL certificates
    include_sensitive_data=False
)
```

### SSL Security Considerations

- **Certificate Verification**: By default, SSL certificate verification is enabled (`ssl_verify=True`). This ensures secure connections but requires valid certificates.
- **Self-signed Certificates**: If your device uses self-signed certificates, set `ssl_verify=False`. Note that this reduces security.
- **Port Configuration**: Use the `port` parameter to specify custom HTTPS ports. Defaults to 443 for HTTPS and 80 for HTTP.
- **Connection Timeouts**: Consider increasing the `timeout` value for SSL connections as they may take longer to establish.

### Migration from HTTP to HTTPS

To migrate existing code from HTTP to HTTPS:

```python
# Before (HTTP)
client = PooldoseClient("192.168.1.100")

# After (HTTPS with SSL verification)
client = PooldoseClient("192.168.1.100", use_ssl=True)

# After (HTTPS with custom port and no verification)
client = PooldoseClient("192.168.1.100", use_ssl=True, port=8443, ssl_verify=False)
```

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
from pooldose.request_status import RequestStatus

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
from pooldose.client import PooldoseClient
from pooldose.request_status import RequestStatus

# HTTP connection (default)
client = PooldoseClient("192.168.1.100", timeout=30)
status = await client.connect()

# HTTPS connection with SSL verification
client = PooldoseClient("192.168.1.100", timeout=30, use_ssl=True)
status = await client.connect()

# HTTPS connection with custom port and disabled verification
client = PooldoseClient("192.168.1.100", use_ssl=True, port=8443, ssl_verify=False)
status = await client.connect()

# Check connection status
if client.is_connected:
    print("Client is connected")
else:
    print("Client is not connected")
```

#### Error Handling
```python
from pooldose.client import PooldoseClient

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

#### Type-specific Access
```python
# Get all values by type
sensors = instant_values.get_sensors()          # All sensor readings
binary_sensors = instant_values.get_binary_sensors()  # All boolean states
numbers = instant_values.get_numbers()          # All configurable numbers
switches = instant_values.get_switches()        # All switch states
selects = instant_values.get_selects()          # All select options

# Check available types dynamically
available_types = instant_values.available_types()
print("Available types:", list(available_types.keys()))
```

#### Working with Mappings
```
Mapping Discovery Process:
┌─────────────────┐
│ Device Connect  │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Get MODEL_ID    │ ──────► PDPR1H1HAW100
│ Get FW_CODE     │ ──────► 539187
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Load JSON File  │ ──────► model_PDPR1H1HAW100_FW539187.json
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Type Discovery  │
│ ┌─────────────┐ │
│ │ Sensors     │ │ ──────► temperature, ph, orp, ...
│ │ Switches    │ │ ──────► stop_dosing, pump_detection, ...
│ │ Numbers     │ │ ──────► ph_target, orp_target, ...
│ │ Selects     │ │ ──────► water_meter_unit, ...
│ └─────────────┘ │
└─────────────────┘
```

```python
# Query what's available for your specific device
print("\nAvailable sensors:")
for name, sensor in client.available_sensors().items():
    print(f"  {name}: key={sensor.key}")
    if sensor.conversion:
        print(f"    conversion: {sensor.conversion}")

print("\nAvailable numbers (settable):")
for name, number in client.available_numbers().items():
    print(f"  {name}: key={number.key}")

print("\nAvailable switches:")
for name, switch in client.available_switches().items():
    print(f"  {name}: key={switch.key}")
```

## API Reference

### PooldoseClient Class Hierarchy
```
PooldoseClient
├── Device Info
│   ├── static_values() ──────► StaticValues
│   └── device_info{} ─────────► dict
├── Type Discovery
│   ├── available_types() ────► dict[str, list[str]]
│   ├── available_sensors() ──► dict[str, SensorMapping]
│   ├── available_numbers() ──► dict[str, NumberMapping]
│   ├── available_switches() ─► dict[str, SwitchMapping]
│   └── available_selects() ──► dict[str, SelectMapping]
└── Live Data
    └── instant_values() ─────► InstantValues
```

#### Constructor
```python
PooldoseClient(host, timeout=10, include_sensitive_data=False, use_ssl=False, port=None, ssl_verify=True)
```

**Parameters:**
- `host` (str): The hostname or IP address of the device
- `timeout` (int): Request timeout in seconds (default: 10)
- `include_sensitive_data` (bool): Whether to include sensitive data like WiFi passwords (default: False)
- `use_ssl` (bool): Whether to use HTTPS instead of HTTP (default: False)
- `port` (Optional[int]): Custom port for connections. Defaults to 80 for HTTP, 443 for HTTPS (default: None)
- `ssl_verify` (bool): Whether to verify SSL certificates when using HTTPS (default: True)

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

### RequestStatus

All client methods return `RequestStatus` enum values:

```python
from pooldose.request_status import RequestStatus

RequestStatus.SUCCESS                    # Operation successful
RequestStatus.CONNECTION_ERROR           # Network connection failed
RequestStatus.HOST_UNREACHABLE           # Device not reachable
RequestStatus.PARAMS_FETCH_FAILED        # Failed to fetch device parameters
RequestStatus.API_VERSION_UNSUPPORTED    # API version not supported
RequestStatus.NO_DATA                    # No data received
RequestStatus.UNKNOWN_ERROR              # Other error occurred
```

### InstantValues Interface
```
InstantValues
├── Dictionary Interface
│   ├── [key] ─────────────────► __getitem__
│   ├── get(key, default) ────► get method
│   ├── key in values ────────► __contains__
│   └── [key] = value ────────► __setitem__ (async)
├── Type Getters
│   ├── get_sensors() ────────► dict[str, tuple]
│   ├── get_binary_sensors() ─► dict[str, bool]
│   ├── get_numbers() ────────► dict[str, tuple]
│   ├── get_switches() ───────► dict[str, bool]
│   └── get_selects() ────────► dict[str, int]
└── Type Setters (async)
    ├── set_number(key, value) ──► bool
    ├── set_switch(key, value) ──► bool
    └── set_select(key, value) ──► bool
```

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

### Security Model
```
Data Classification:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Public Data   │    │ Sensitive Data  │    │  Never Exposed  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Device Name   │    │ • WiFi Password │    │ • Admin Creds   │
│ • Model ID      │    │ • AP Password   │    │ • Internal Keys │
│ • Serial Number │    │                 │    │                 │
│ • Sensor Values │    │                 │    │                 │
│ • IP Address    │    │                 │    │                 │
│ • MAC Address   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  Always Included      include_sensitive_data=True    Never Included
```

## Changelog

For detailed release notes and version history, please see [CHANGELOG.md](CHANGELOG.md).

### Latest Release (0.4.6)
- Device returns unit for pH values, which have physically no unit. Fixed by replacing such occurrences with None.