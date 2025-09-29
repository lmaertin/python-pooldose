# python-pooldose

Unofficial async Python client for [SEKO](https://www.seko.com/) Pooldosing systems. SEKO is a manufacturer of various monitoring and control devices for pools and spas.

This client uses an undocumented local HTTP API. It provides live readings for pool sensors such as temperature, pH, ORP/Redox, as well as status information and control over the dosing logic.

## Features

- **Async/await support** for non-blocking operations
- **Dynamic sensor discovery** based on device model and firmware
- **Dictionary-style access** to instant values
- **Structured data API** with type-based organization
- **Device analyzer** for discovering unsupported device capabilities
- **PEP-561 compliant** with full type hints for Home Assistant integrations
- **Command-line interface** for direct device interaction and testing
- **Secure by default** - WiFi passwords excluded unless explicitly requested
- **Comprehensive error handling** with detailed logging
- **SSL/HTTPS support** for secure communication

## API Overview

### Program Flow

```
1. Create PooldoseClient
   ├── Connect to Device
   │   ├── Fetch Device Info (Debug Config)
   │   ├── WiFi Station Info (optional)
   │   ├── Access Point Info (optional)
   │   └── Network Info
   └── Load Mapping JSON (based on MODEL_ID + FW_CODE)

2. Get Static Values
   └── Device information and configuration

3. Get Instant Values
   ├── Dictionary-style access: instant_values['temperature']
   ├── Get with default: instant_values.get('ph', default)
   ├── Check existence: 'sensor_name' in instant_values
   └── Structured access: instant_values_structured()

4. Set Values via Type Methods
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
┌─────────────────┐    ┌─────────────────┐
│  InstantValues  │────│ Dictionary API  │
└─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Structured API  │
│ • sensor{}      │
│ • number{}      │
│ • switch{}      │
│ • binary_sensor{}│
│ • select{}      │
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
    include_sensitive_data=False,
    include_mac_lookup=False
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

## Command Line Usage

After installation, you can use python-pooldose directly from the command line:

### Connect to Real Device

```bash
# Basic connection
pooldose --host 192.168.1.100

# With HTTPS
pooldose --host 192.168.1.100 --ssl

# Custom port
pooldose --host 192.168.1.100 --ssl --port 8443

# Analyze device capabilities (discover unsupported devices)
pooldose --host 192.168.1.100 --analyze

# Show all widgets including hidden ones
pooldose --host 192.168.1.100 --analyze-all
```

### Mock Mode with JSON Files

```bash
# Use JSON file for testing
pooldose --mock path/to/your/data.json
```

### Alternative Module Execution

You can also run it as a Python module:

```bash
# Real device
python -m pooldose --host 192.168.1.100

# Device analysis
python -m pooldose --host 192.168.1.100 --analyze

# Mock mode
python -m pooldose --mock data.json

# Show help
python -m pooldose --help
```

## Device Analysis for Unsupported Devices

The device analyzer is a powerful feature that helps discover and analyze PoolDose devices that are not yet officially supported. This is particularly useful for:

- **New Device Discovery**: Identifying capabilities of unknown device models
- **Device Support Development**: Gathering data needed to add support for new devices
- **Troubleshooting**: Understanding how your device exposes data and controls
- **Widget Exploration**: Discovering all available sensors, controls, and settings

### Basic Device Analysis

```bash
# Analyze a device to discover its capabilities
pooldose --host 192.168.1.100 --analyze

# Show all widgets including hidden ones
pooldose --host 192.168.1.100 --analyze-all

# Analyze with HTTPS
pooldose --host 192.168.1.100 --ssl --analyze
```

### Analysis Output

The analyzer provides comprehensive information about your device:

```
=== DEVICE ANALYSIS ===
Device: 01234567890A_DEVICE
Model: PDPR1H1HAW***  
Firmware: FW53****

=== WIDGETS (Visible UI Elements) ===

SENSORS (Read-only values)
temperature: 24.5°C
ph: 7.2
orp: 720 mV

SETPOINTS (Configurable values)  
target_ph: 7.0 (Range: 6.0-8.0, Step: 0.1)
target_orp: 700 mV (Range: 400-900, Step: 10)

SWITCHES (On/Off controls)
stop_dosing: OFF
pump_detection: ON

SELECTS (Configuration options)
water_meter_unit: L/h
  Options: [L/h, m³/h, gal/h]

ALARMS (Status indicators)
alarm_ph: OK
alarm_orp: OK
```

### Using Analysis for Device Support

When you encounter an unsupported device, the analyzer helps gather the necessary information:

1. **Run Analysis**: Use `--analyze` to discover all device capabilities
2. **Document Output**: Save the analysis output to understand device structure  
3. **Check Widget Types**: Note which sensors, controls, and settings are available
4. **Identify Patterns**: Look for device model and firmware information
5. **Report Findings**: Use the analysis data to request support for your device model

### Example: Discovering New Device

```bash
# Unknown device analysis
pooldose --host 192.168.1.100 --analyze

# Output shows:
# Device: 01987654321B_DEVICE  
# Model: PDPR2H2XYZ***        ← New model not yet supported
# Firmware: FW54****          ← New firmware version
# 
# Widgets discovered: 15 sensors, 8 controls, 12 settings
```

With this information, you can:
- Report the new model/firmware combination  
- Share the widget structure for mapping development
- Help expand device support for the community

The device analyzer makes python-pooldose extensible and helps build support for the growing ecosystem of SEKO PoolDose devices.

## Examples

The `examples/` directory contains demonstration scripts that show how to use the python-pooldose library:

### 1. Real Device Demo (`examples/demo.py`)

Demonstrates connecting to a real PoolDose device and accessing all types of data:

```bash
# Edit the HOST variable in the file first
python examples/demo.py
```

**Features:**

- Connects to actual hardware
- Shows device information and static values
- Displays all sensor readings, alarms, setpoints, and settings
- Demonstrates error handling

### Benefits of the Examples

- **Learning**: Step-by-step progression from simple to advanced usage
- **Development**: Mock client allows development without hardware
- **Testing**: JSON-based testing for CI/CD pipelines
- **Reference**: Real-world code patterns and best practices

## Mock Client System

The **MockPooldoseClient** system allows using JSON files instead of real Pooldose hardware for testing and development. This is particularly useful for:

- **Development without hardware**
- **Unit tests**
- **Data analysis with real device data**
- **CI/CD pipeline tests**

### Mock Client Quick Start

```python
import asyncio
from pathlib import Path
from pooldose.mock_client import MockPooldoseClient

async def simple_test():
    # Load data file
    json_file = Path("path/to/your/data.json")
    
    # Create mock client
    client = MockPooldoseClient(json_file_path=json_file)
    
    # Connect (loads mapping data)
    status = await client.connect()
    if status.name != "SUCCESS":
        print(f"Connection failed: {status}")
        return
    
    # Get sensor values
    status, instant_values = await client.instant_values()
    if status.name == "SUCCESS" and instant_values:
        print(f"Temperature: {instant_values['temperature']}")
        print(f"pH Value: {instant_values['ph']}")
        print(f"ORP: {instant_values['orp']}")
    
    # Get structured data
    status, data = await client.instant_values_structured()
    if status.name == "SUCCESS":
        sensors = data.get('sensor', {})
        for name, info in sensors.items():
            value = info.get('value', 'N/A')
            unit = info.get('unit', '')
            print(f"{name}: {value} {unit}")

# Run demo
asyncio.run(simple_test())
```

### Mock Client Command Line Usage

You can use the mock client with custom JSON files via the command line:

```bash
# Use mock client with JSON file
pooldose --mock path/to/your/data.json

# Or as Python module
python -m pooldose --mock path/to/your/data.json
```

### JSON Data Format

The JSON file must have the following structure:

```json
{
    "devicedata": {
        "SERIALNUMBER_DEVICE": {
            "MODEL_FW_w_key1": {
                "current": 25.5,
                "magnitude": ["°C"]
            },
            "MODEL_FW_w_key2": {
                "current": 7.2,
                "magnitude": ["pH"]
            }
        }
    }
}
```

### Mock Client API Methods

#### Initialization

```python
client = MockPooldoseClient(
    json_file_path="path/to/data.json",
    timeout=30,  # Ignored (compatibility)
    include_sensitive_data=True  # Include WiFi keys etc.
)
```

#### Connection

```python
status = await client.connect()  # Loads mapping configuration
is_connected = client.is_connected  # Check status
```

#### Data Retrieval

```python
# Static device information
status, static_values = client.static_values()

# Live sensor values
status, instant_values = await client.instant_values()

# Structured data (grouped by types)
status, structured_data = await client.instant_values_structured()
```

#### Utility Methods

```python
# Get raw data
raw_data = client.get_raw_data()
device_data = client.get_device_data()

# Reload JSON file
success = client.reload_data()
```

### Available Sample Files

The following sample JSON files are available in the repository:

- `references/testdaten/tscherno/instantvalues.json` - Sample device data for testing

### Mock Client Use Cases

#### Unit Tests

```python
def test_temperature_reading():
    client = MockPooldoseClient("sample_data.json")
    asyncio.run(client.connect())
    
    status, values = asyncio.run(client.instant_values())
    assert status.name == "SUCCESS"
    assert values['temperature'][0] == 23.0  # Expected value
```

#### Data Analysis

```python
# Analyze all sensor values
client = MockPooldoseClient("production_data.json")
await client.connect()

status, data = await client.instant_values_structured()
sensors = data.get('sensor', {})

for sensor_name, sensor_data in sensors.items():
    value = sensor_data.get('value')
    unit = sensor_data.get('unit', '')
    print(f"{sensor_name}: {value} {unit}")
```

#### Integration Tests

```python
async def test_full_integration():
    client = MockPooldoseClient("integration_sample_data.json")
    
    # Test connection
    assert await client.connect() == RequestStatus.SUCCESS
    
    # Test static values
    status, static = client.static_values()
    assert status == RequestStatus.SUCCESS
    assert static.sensor_name is not None
    
    # Test live values
    status, instant = await client.instant_values()
    assert status == RequestStatus.SUCCESS
    assert 'temperature' in instant
```

### Benefits of the Mock System

- **Fast**: No network latency
- **Reliable**: No hardware dependencies  
- **Flexible**: Different scenarios testable
- **Realistic**: Real device data structures
- **Compatible**: Same API as real client

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
    """Demonstrate PooldoseClient usage with dictionary-based API."""
    
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

    # --- Get static values ---
    status, static_values = client.static_values()
    if status == RequestStatus.SUCCESS:
        print(f"Device Name: {static_values.sensor_name}")
        print(f"Serial Number: {static_values.sensor_serial_number}")
        print(f"Firmware Version: {static_values.sensor_fw_version}")

    # --- Get instant values (dictionary-style) ---
    status, instant_values = await client.instant_values()
    if status != RequestStatus.SUCCESS:
        print(f"Error getting instant values: {status}")
        return

    # Dictionary-style individual access
    if "temperature" in instant_values:
        temp = instant_values["temperature"]
        print(f"Temperature: {temp[0]} {temp[1]}")

    # Get with default
    ph_value = instant_values.get("ph", "Not available")
    print(f"pH: {ph_value}")

    # --- Get structured instant values ---
    status, structured_data = await client.instant_values_structured()
    if status != RequestStatus.SUCCESS:
        print(f"Error getting structured values: {status}")
        return

    # Access sensors
    sensors = structured_data.get("sensor", {})
    print("\nSensor Values:")
    for key, sensor_data in sensors.items():
        value = sensor_data.get("value")
        unit = sensor_data.get("unit")
        if unit:
            print(f"  {key}: {value} {unit}")
        else:
            print(f"  {key}: {value}")

    # Access numbers (setpoints)
    numbers = structured_data.get("number", {})
    print("\nSetpoints:")
    for key, number_data in numbers.items():
        value = number_data.get("value")
        unit = number_data.get("unit")
        min_val = number_data.get("min")
        max_val = number_data.get("max")
        
        if unit:
            print(f"  {key}: {value} {unit} (Range: {min_val}-{max_val})")
        else:
            print(f"  {key}: {value} (Range: {min_val}-{max_val})")

    # Access switches
    switches = structured_data.get("switch", {})
    print("\nSwitches:")
    for key, switch_data in switches.items():
        value = switch_data.get("value")
        status_text = "ON" if value else "OFF"
        print(f"  {key}: {status_text}")

    # Access binary sensors (alarms/status)
    binary_sensors = structured_data.get("binary_sensor", {})
    print("\nAlarms & Status:")
    for key, sensor_data in binary_sensors.items():
        value = sensor_data.get("value")
        status_text = "ACTIVE" if value else "OK"
        print(f"  {key}: {status_text}")

    # Access selects (configuration options)
    selects = structured_data.get("select", {})
    print("\nSettings:")
    for key, select_data in selects.items():
        value = select_data.get("value")
        print(f"  {key}: {value}")

    # --- Setting values ---
    
    # Set number values (via InstantValues)
    result = await instant_values.set_number("target_ph", 7.2)
    print(f"Set pH target to 7.2: {result}")

    # Set switch values
    result = await instant_values.set_switch("stop_dosing", True)
    print(f"Set stop dosing: {result}")

    # Set select values
    result = await instant_values.set_select("water_meter_unit", "L/h")
    print(f"Set water meter unit: {result}")

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

#### Working with Structured Data

```python
# Get all data types at once
status, structured_data = await client.instant_values_structured()

if status == RequestStatus.SUCCESS:
    # Check what types are available
    available_types = list(structured_data.keys())
    print("Available types:", available_types)
    
    # Process each type
    for data_type, items in structured_data.items():
        print(f"\n{data_type.title()} ({len(items)} items):")
        for key, data in items.items():
            if data_type in ["sensor", "number"]:
                value = data.get("value")
                unit = data.get("unit")
                if unit:
                    print(f"  {key}: {value} {unit}")
                else:
                    print(f"  {key}: {value}")
            elif data_type in ["switch", "binary_sensor"]:
                value = data.get("value")
                print(f"  {key}: {'ON' if value else 'OFF'}")
            elif data_type == "select":
                value = data.get("value")
                print(f"  {key}: {value}")
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
│ Get MODEL_ID    │ ──────► PDPR1H1HAW***
│ Get FW_CODE     │ ──────► 53****
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Load JSON File  │ ──────► model_PDPR1H1HAW***_FW53****.json
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
│ │ Binary Sens │ │ ──────► alarm_ph, alarm_orp, ...
│ └─────────────┘ │
└─────────────────┘
```

## API Reference

### PooldoseClient Class

#### Constructor

```python
PooldoseClient(host, timeout=30, include_sensitive_data=False, include_mac_lookup=False, use_ssl=False, port=None, ssl_verify=True)
```

**Parameters:**

- `host` (str): The hostname or IP address of the device
- `timeout` (int): Request timeout in seconds (default: 30)
- `include_sensitive_data` (bool): Whether to include sensitive data like WiFi passwords (default: False)
- `include_mac_lookup` (bool): Whether to include MAC lookup via ARP (default: False)
- `use_ssl` (bool): Whether to use HTTPS instead of HTTP (default: False)
- `port` (Optional[int]): Custom port for connections. Defaults to 80 for HTTP, 443 for HTTPS (default: None)
- `ssl_verify` (bool): Whether to verify SSL certificates when using HTTPS (default: True)

#### Methods

- `async connect()` → `RequestStatus` - Connect to device and initialize all components
- `static_values()` → `tuple[RequestStatus, StaticValues | None]` - Get static device information
- `async instant_values()` → `tuple[RequestStatus, InstantValues | None]` - Get current sensor readings and device state
- `async instant_values_structured()` → `tuple[RequestStatus, dict[str, Any]]` - Get structured data organized by type
- `check_apiversion_supported()` → `tuple[RequestStatus, dict]` - Check API version compatibility

#### Properties

- `is_connected: bool` - Check if client is connected to device
- `device_info: dict` - Dictionary containing device information

### RequestStatus

All client methods return `RequestStatus` enum values:

```python
from pooldose.request_status import RequestStatus

RequestStatus.SUCCESS                    # Operation successful
RequestStatus.HOST_UNREACHABLE           # Device not reachable
RequestStatus.PARAMS_FETCH_FAILED        # Failed to fetch device parameters
RequestStatus.API_VERSION_UNSUPPORTED    # API version not supported
RequestStatus.NO_DATA                    # No data received
RequestStatus.LAST_DATA                  # Last valid data used
RequestStatus.CLIENT_ERROR_SET           # Error setting client value
RequestStatus.UNKNOWN_ERROR              # Other error occurred
```

### InstantValues Interface

The `InstantValues` class provides dictionary-style access to sensor data:

```python
# Dictionary Interface
value = instant_values["sensor_name"]                    # Direct access
value = instant_values.get("sensor_name", default)      # Get with default
exists = "sensor_name" in instant_values                 # Check existence

# Setting values (async, with validation)
await instant_values.set_number("ph_target", 7.2)       # Set number value
await instant_values.set_switch("stop_dosing", True)    # Set switch value
await instant_values.set_select("unit", "L/h")          # Set select value
```

### Structured Data Format

The `instant_values_structured()` method returns data organized by type:

```python
{
    "sensor": {
        "temperature": {"value": 25.5, "unit": "°C"},
        "ph": {"value": 7.2, "unit": None}
    },
    "number": {
        "target_ph": {"value": 7.0, "unit": None, "min": 6.0, "max": 8.0, "step": 0.1}
    },
    "switch": {
        "stop_dosing": {"value": False}
    },
    "binary_sensor": {
        "alarm_ph": {"value": False}
    },
    "select": {
        "water_meter_unit": {"value": "L/h"}
    }
}
```

#### Data Types

- **sensor**: Read-only sensor values with optional units
- **number**: Configurable numeric values with min/max/step constraints
- **switch**: Boolean on/off controls  
- **binary_sensor**: Read-only boolean status indicators
- **select**: Configurable selection options

## Supported Devices

This client has been tested with:

- **SEKO PoolDose Double/Dual WiFi** (Model: PDPR1H1HAW***, FW: 53****)
- **VA dos BASIC Chlor - pH/ORP Wi-Fi** (Model: PDPR1H1HAR***, FW: 53****)

Other SEKO PoolDose models may work but are untested. The client uses JSON mapping files to adapt to different device models and firmware versions (see e.g. `src/pooldose/mappings/model_PDPR1H1HAW***_FW53****.json`).

> **Note:** The JSON files in the mappings directory define the device-specific data keys and their human-readable names for different PoolDose models and firmware versions.

## Type Hints & Home Assistant Integration

This package is **PEP-561 compliant** and fully typed for use in Home Assistant integrations:

### Type Safety Features

**PEP-561 Compliance**: Package includes `py.typed` file marking it as fully typed  
**Comprehensive Type Annotations**: All public API methods have complete type hints  
**mypy Support**: Built-in mypy configuration for static type checking  
**Home Assistant Ready**: Compatible with Home Assistant's strict typing requirements  

### Type-Safe Usage

```python
from pooldose import PooldoseClient
from pooldose.request_status import RequestStatus

# Type checkers will infer all types automatically
client: PooldoseClient = PooldoseClient("192.168.1.100")
status: RequestStatus = await client.connect()

# Dictionary-style access with proper typing
status, instant_values = await client.instant_values()
if status == RequestStatus.SUCCESS and instant_values:
    temperature = instant_values["temperature"]  # Typed as tuple[float, str]
    ph_value = instant_values.get("ph", "N/A")  # Safe access with default

# Structured data with full type safety
status, structured_data = await client.instant_values_structured()
sensors = structured_data.get("sensor", {})  # Type: dict[str, dict[str, Any]]
```

### Integration Benefits

- **IDE Support**: Full autocomplete and type checking in VS Code, PyCharm, etc.
- **Runtime Safety**: Catch type errors before deployment
- **Documentation**: Self-documenting code through type annotations
- **Maintenance**: Easier refactoring with type-guided development

For Home Assistant integrations, add this package to your integration's dependencies and enjoy full type safety throughout your integration code.

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

```text
Data Classification:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Public Data   │    │ Sensitive Data  │    │  Never Exposed  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Device Name   │    │ • WiFi Password │    │ • Admin Creds   │
│ • Model ID      │    │ • AP Password   │    │ • Internal Keys │
│ • Serial Number │    │                 │    │                 │
│ • Sensor Values │    │                 │    │                 │
│ • IP Address    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  Always Included      include_sensitive_data=True    Never Included
```

## Changelog

For detailed release notes and version history, please see [CHANGELOG.md](CHANGELOG.md).

### Latest Release (0.7.0)

- **Connection Handling**: Improved session management for more reliable connections
- **RequestHandler**: Centralized session management with internal _get_session method
- **Performance**: Reduced connection overhead for multiple consecutive API calls
- **Error Handling**: Better cleanup of HTTP sessions in error cases
