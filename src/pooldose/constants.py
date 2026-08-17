"""Constants for the Pooldose library."""

from pooldose.type_definitions import DeviceInfoDict

# Model alias mapping: PRODUCT_CODE reported by device → model ID used in the
# raw instant-value data keys (prefix "<model_id>_FW<fw_code>_...").
# Some devices report a different PRODUCT_CODE than the model ID actually used
# in their raw data keys. This alias is used to resolve that raw-key prefix.
#
# It is also used as a *fallback* when loading the mapping JSON file: the
# loader (MappingInfo.load) always tries the reported PRODUCT_CODE's own
# mapping file first, and only falls back to the aliased model's mapping file
# if no dedicated one exists. So adding a dedicated mapping file for a model
# listed here (e.g. model_<PRODUCT_CODE>_FW<fw_code>.json) is picked up
# automatically without needing to change this table.
MODEL_ALIASES: dict[str, str] = {
    "PDHC1H1HAR1V1": "PDPR1H1HAR1V0",
    "PDHC1H1HAR1V0": "PDPR1H1HAR1V0",
    "PDPR1H1HAW102": "PDPR1H1HAW100",
    "PDPR1H1HAW1B0_I": "PDPR1H1HAW1B0",
}

# Default device info structure
DEFAULT_DEVICE_INFO: DeviceInfoDict = {
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


def get_default_device_info() -> DeviceInfoDict:
    """Return a copy of the default device info structure."""
    return DEFAULT_DEVICE_INFO.copy()
