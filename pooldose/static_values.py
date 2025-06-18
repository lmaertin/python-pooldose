from typing import Any, Dict, Optional

class StaticValues:
    """
    Provides property-based access to static PoolDose device information fields.

    This class wraps the device_info dictionary and exposes each static
    value (such as name, serial number, firmware version, etc.) as a
    property with a descriptive name. All properties are read-only.

    Args:
        device_info (Dict[str, Any]): The dictionary containing static device information.
    """

    def __init__(self, device_info: Dict[str, Any]):
        self._device_info = device_info

    @property
    def sensor_name(self) -> Optional[str]:
        """The device name."""
        return self._device_info.get("NAME")

    @property
    def sensor_serial_number(self) -> Optional[str]:
        """The device serial number."""
        return self._device_info.get("SERIAL_NUMBER")

    @property
    def sensor_device_id(self) -> Optional[str]:
        """The device ID."""
        return self._device_info.get("DEVICE_ID")

    @property
    def sensor_model(self) -> Optional[str]:
        """The device model."""
        return self._device_info.get("MODEL")

    @property
    def sensor_model_id(self) -> Optional[str]:
        """The device model ID."""
        return self._device_info.get("MODEL_ID")

    @property
    def sensor_ownerid(self) -> Optional[str]:
        """The device owner ID."""
        return self._device_info.get("OWNERID")

    @property
    def sensor_groupname(self) -> Optional[str]:
        """The device group name."""
        return self._device_info.get("GROUPNAME")

    @property
    def sensor_fw_version(self) -> Optional[str]:
        """The device firmware version."""
        return self._device_info.get("FW_VERSION")

    @property
    def sensor_sw_version(self) -> Optional[str]:
        """The device software version."""
        return self._device_info.get("SW_VERSION")

    @property
    def sensor_api_version(self) -> Optional[str]:
        """The device API version."""
        return self._device_info.get("API_VERSION")

    @property
    def sensor_fw_code(self) -> Optional[str]:
        """The device firmware code."""
        return self._device_info.get("FW_CODE")

    @property
    def sensor_mac(self) -> Optional[str]:
        """The device MAC address."""
        return self._device_info.get("MAC")

    @property
    def sensor_ip(self) -> Optional[str]:
        """The device IP address."""
        return self._device_info.get("IP")

    @property
    def sensor_wifi_ssid(self) -> Optional[str]:
        """The device WiFi SSID."""
        return self._device_info.get("WIFI_SSID")

    @property
    def sensor_wifi_key(self) -> Optional[str]:
        """The device WiFi key."""
        return self._device_info.get("WIFI_KEY")

    @property
    def sensor_ap_ssid(self) -> Optional[str]:
        """The device access point SSID."""
        return self._device_info.get("AP_SSID")

    @property
    def sensor_ap_key(self) -> Optional[str]:
        """The device access point key."""
        return self._device_info.get("AP_KEY")