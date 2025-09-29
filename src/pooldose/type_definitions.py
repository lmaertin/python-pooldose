"""Type definitions for the pooldose package."""

from typing import Any, Dict, Final, List, Literal, Optional, TypedDict

# Device information types
class DeviceInfoDict(TypedDict, total=False):
    """Type definition for device information dictionary."""
    API_VERSION: Optional[str]
    SERIAL_NUMBER: Optional[str]
    NAME: Optional[str]
    SW_VERSION: Optional[str]
    DEVICE_ID: Optional[str]
    MODEL: Optional[str]
    MODEL_ID: Optional[str]
    FW_VERSION: Optional[str]
    FW_CODE: Optional[str]
    WIFI_SSID: Optional[str]
    IP: Optional[str]
    WIFI_KEY: Optional[str]
    AP_SSID: Optional[str]
    AP_KEY: Optional[str]
    OWNERID: Optional[str]
    GROUPNAME: Optional[str]
    MAC: Optional[str]

# API response types
class APIVersionResponse(TypedDict):
    """Type definition for API version response."""
    api_version_is: Optional[str]
    api_version_should: str

# Mapping types
class MappingDict(TypedDict):
    """Type definition for mapping dictionary."""
    # Allow any keys in the mapping
    __extra__: Any

# Value types
class ValueDict(TypedDict, total=False):
    """Type definition for a value entry."""
    type: str
    value: Any
    unit: str
    raw_value: Any
    status: str
    timestamp: int

# Structured values by type
class StructuredValuesDict(TypedDict, total=False):
    """Type definition for structured values dictionary."""
    sensor: Dict[str, ValueDict]
    switch: Dict[str, ValueDict]
    number: Dict[str, ValueDict]
    binary_sensor: Dict[str, ValueDict]
    select: Dict[str, ValueDict]
# Debug config types
class DeviceDebugInfo(TypedDict, total=False):
    """Type definition for device debug information."""
    DID: str
    NAME: str
    PRODUCT_CODE: str
    FW_REL: str
    FW_CODE: str

class GatewayDebugInfo(TypedDict, total=False):
    """Type definition for gateway debug information."""
    DID: str
    NAME: str
    FW_REL: str

class DebugConfigDict(TypedDict, total=False):
    """Type definition for debug configuration dictionary."""
    GATEWAY: GatewayDebugInfo
    DEVICES: List[DeviceDebugInfo]

# WiFi related types
class WiFiStationDict(TypedDict, total=False):
    """Type definition for WiFi station information."""
    SSID: str
    IP: str
    KEY: Optional[str]

class AccessPointDict(TypedDict, total=False):
    """Type definition for access point information."""
    SSID: str
    KEY: Optional[str]

class NetworkInfoDict(TypedDict, total=False):
    """Type definition for network information."""
    OWNERID: str
    GROUPNAME: str

# Constants
SUPPORTED_VALUE_TYPES: Final = Literal["sensor", "switch", "number", "binary_sensor", "select"]
