# API Reference

## PooldoseClient Class

### Constructor

```python
PooldoseClient(host, timeout=30, *, websession=None, include_sensitive_data=False, include_mac_lookup=False, use_ssl=False, port=None, ssl_verify=True, debug_payload=False, retry_delay=0.1)
```

**Parameters:**

- `host` (str): The hostname or IP address of the device
- `timeout` (int): Request timeout in seconds (default: 30)
- `websession` (Optional[aiohttp.ClientSession]): Optional external ClientSession for HTTP requests. If provided, will be used for all API calls (mainly for Home Assistant integration) (default: None)
- `include_sensitive_data` (bool): Whether to include sensitive data like WiFi passwords (default: False)
- `include_mac_lookup` (bool): Whether to include MAC lookup via ARP (default: False)
- `use_ssl` (bool): Whether to use HTTPS instead of HTTP (default: False)
- `port` (Optional[int]): Custom port for connections. Defaults to 80 for HTTP, 443 for HTTPS (default: None)
- `ssl_verify` (bool): Whether to verify SSL certificates when using HTTPS (default: True)
- `debug_payload` (bool): If True, log and store payloads sent to device for debugging (default: False)
- `retry_delay` (float): Delay in seconds between consecutive API requests during connect. Prevents overwhelming the embedded device (default: 0.1)

### Methods

- `async connect()` → `RequestStatus` - Connect to device and initialize all components
- `async get_cloud_status()` → `Optional[bool]` — Retrieve the current cloud connection status
- `async get_wifi_rssi()` → `Optional[int]` — Retrieve the current WiFi RSSI (signal strength)
- `static_values()` → `tuple[RequestStatus, StaticValues | None]` - Get static device information
- `async instant_values()` → `tuple[RequestStatus, InstantValues | None]` - Get current sensor readings and device state
- `async instant_values_structured()` → `tuple[RequestStatus, dict[str, Any]]` - Get structured data organized by type
- `check_apiversion_supported()` → `tuple[RequestStatus, dict]` - Check API version compatibility
- `async set_switch(key, value)` → `bool` - Set a mapped switch value (convenience wrapper)
- `async set_number(key, value)` → `bool` - Set a mapped numeric value (convenience wrapper)
- `async set_select(key, value)` → `bool` - Set a mapped select option (convenience wrapper)

### Properties

- `is_connected: bool` - Check if client is connected to device
- `device_info: dict` - Dictionary containing device information

## RequestStatus

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

## InstantValues Interface

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

## Structured Data Format

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

### Data Types

- **sensor**: Read-only sensor values with optional units
- **number**: Configurable numeric values with min/max/step constraints
- **switch**: Boolean on/off controls  
- **binary_sensor**: Read-only boolean status indicators
- **select**: Configurable selection options
