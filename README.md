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
2. Browse to the IP address or hostname (default port: 80 for HTTP, 443 for HTTPS).
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

### SSL/HTTPS Configuration Example

```python
import asyncio
from pooldose.client import PooldoseClient
from pooldose.request_status import RequestStatus

async def ssl_example() -> None:
    """Demonstrate SSL/HTTPS configuration options."""
    
    # HTTPS with SSL verification (recommended for production)
    client = PooldoseClient(
        host="pooldose.example.com",
        port=443,
        use_ssl=True,
        verify_ssl=True,  # Verify SSL certificates (default)
        timeout=30
    )
    
    # HTTPS with SSL verification disabled (for self-signed certificates)
    client_no_verify = PooldoseClient(
        host="192.168.1.100",
        port=8443,  # Custom HTTPS port
        use_ssl=True,
        verify_ssl=False,  # Disable SSL certificate verification
        timeout=30
    )
    
    # Standard HTTP (default)
    client_http = PooldoseClient(
        host="192.168.1.100",
        port=80,  # Default HTTP port
        use_ssl=False,  # HTTP instead of HTTPS
        timeout=30
    )
    
    # Connect and use the client
    status = await client.connect()
    if status == RequestStatus.SUCCESS:
        print(f"Connected via {'HTTPS' if client.use_ssl else 'HTTP'} on port {client.port}")
        print(f"SSL verification: {'enabled' if client.verify_ssl else 'disabled'}")
    else:
        print(f"Connection failed: {status}")

if __name__ == "__main__":
    asyncio.run(ssl_example())
```

### Advanced Usage

#### Connection Management
```python
from pooldose.client import PooldoseClient
from pooldose.request_status import RequestStatus

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
PooldoseClient(host, timeout=30, include_sensitive_data=False, port=80, use_ssl=False, verify_ssl=True)
```

**Parameters:**
- `host` (str): The hostname or IP address of the device
- `timeout` (int): Request timeout in seconds (default: 30)
- `include_sensitive_data` (bool): Whether to include sensitive data like WiFi passwords (default: False)
- `port` (int): Port number for API connections (default: 80 for HTTP, 443 typically for HTTPS)
- `use_ssl` (bool): Whether to use HTTPS instead of HTTP (default: False)
- `verify_ssl` (bool): Whether to verify SSL certificates when using HTTPS (default: True)

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
- `port` - Port number for API connections
- `use_ssl` - Whether SSL/HTTPS is enabled
- `verify_ssl` - Whether SSL certificate verification is enabled

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

## SSL/HTTPS Configuration

The python-pooldose client supports both HTTP and HTTPS connections with flexible SSL configuration options.

### SSL Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_ssl` | bool | `False` | Enable HTTPS instead of HTTP |
| `port` | int | `80` | Port number for connections |
| `verify_ssl` | bool | `True` | Verify SSL certificates |

### Configuration Examples

#### Standard HTTP (Default)
```python
client = PooldoseClient("192.168.1.100")
# Uses HTTP on port 80
```

#### HTTPS with SSL Verification
```python
client = PooldoseClient(
    host="pooldose.example.com",
    port=443,
    use_ssl=True,
    verify_ssl=True  # Verify SSL certificates (recommended)
)
```

#### HTTPS without SSL Verification (Self-signed certificates)
```python
client = PooldoseClient(
    host="192.168.1.100",
    port=8443,
    use_ssl=True,
    verify_ssl=False  # Disable SSL verification for self-signed certs
)
```

#### Custom Port Configuration
```python
# Custom HTTP port
client = PooldoseClient("192.168.1.100", port=8080, use_ssl=False)

# Custom HTTPS port
client = PooldoseClient("192.168.1.100", port=8443, use_ssl=True)
```

### SSL Security Considerations

- **Production environments**: Always use `verify_ssl=True` with properly signed certificates
- **Development/Testing**: Use `verify_ssl=False` only for self-signed certificates in trusted environments
- **Default behavior**: SSL verification is enabled by default for security
- **Port selection**: Use standard ports (80 for HTTP, 443 for HTTPS) unless your device is configured differently

### SSL Error Handling

```python
import asyncio
import ssl
from pooldose.client import PooldoseClient
from pooldose.request_status import RequestStatus

async def ssl_error_handling():
    client = PooldoseClient(
        host="192.168.1.100",
        port=443,
        use_ssl=True,
        verify_ssl=True
    )
    
    try:
        status = await client.connect()
        if status == RequestStatus.HOST_UNREACHABLE:
            print("Host not reachable - check IP and port")
        elif status == RequestStatus.CONNECTION_ERROR:
            print("Connection error - possibly SSL certificate issues")
        elif status == RequestStatus.SUCCESS:
            print("Connected successfully")
    except ssl.SSLError as e:
        print(f"SSL Error: {e}")
        print("Try setting verify_ssl=False for self-signed certificates")
```

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

### SSL Security Model
```
SSL Configuration:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Production      │    │ Development     │    │ Local Testing   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ use_ssl=True    │    │ use_ssl=True    │    │ use_ssl=False   │
│ verify_ssl=True │    │ verify_ssl=False│    │ port=80         │
│ port=443        │    │ port=8443       │    │                 │
│ Valid SSL cert  │    │ Self-signed     │    │ HTTP only       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  Maximum Security     Balanced Security       No Encryption
```

## Changelog

### [0.5.0] - 2024-07-25
- **NEW**: Added SSL/HTTPS support with configurable verification
- **NEW**: Added custom port configuration support  
- **NEW**: Added `use_ssl` parameter for HTTPS connections
- **NEW**: Added `verify_ssl` parameter for SSL certificate verification control
- **NEW**: Added `port` parameter for custom port configuration
- **NEW**: Extended PooldoseClient with SSL configuration properties
- **IMPROVED**: Enhanced URL construction to support both HTTP and HTTPS
- **IMPROVED**: Updated all API endpoints to use configurable SSL settings
- **FIXED**: Fixed bug in `_load_device_info` method returning incorrect tuple format
- **DOCS**: Comprehensive SSL configuration documentation and examples

### [0.4.2] - 2025-07-19
- Corrected imports of RequestStatus class
- Fixing broken release 0.4.1

### [0.4.1] - 2025-07-17
- **BREAKING**: Moved all RequestStatus into client module - import from `pooldose.client` instead of `pooldose.request_handler`
- Moved all connect checks into client (incl. API Version check) to avoid public access to requesthandler
- Clean up code and improved encapsulation

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