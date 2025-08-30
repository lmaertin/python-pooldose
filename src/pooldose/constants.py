"""Constants for the Pooldose library."""

from typing import Any, Dict, Optional

# Default device info structure
DEFAULT_DEVICE_INFO: Dict[str, Optional[Any]] = {
    "NAME": None,           # Device name
    "SERIAL_NUMBER": None,  # Serial number
    "DEVICE_ID": None,      # Device ID, i.e., SERIAL_NUMBER + "_DEVICE"
    "MODEL": None,          # Device model
    "MODEL_ID": None,       # Model ID
    "OWNERID": None,        # Owner ID
    "GROUPNAME": None,      # Group name
    "FW_VERSION": None,     # Firmware version
    "SW_VERSION": None,     # Software version
    "API_VERSION": None,    # API version
    "FW_CODE": None,        # Firmware code
    "MAC": None,            # MAC address
    "IP": None,             # IP address
    "WIFI_SSID": None,      # WiFi SSID
    "WIFI_KEY": None,       # WiFi key
    "AP_SSID": None,        # Access Point SSID
    "AP_KEY": None,         # Access Point key
}


def get_default_device_info() -> Dict[str, Optional[Any]]:
    """Return a copy of the default device info structure."""
    return DEFAULT_DEVICE_INFO.copy()
