"""Static Values for Async API client for SEKO Pooldose."""

import logging
from typing import Any, Dict, Optional

_LOGGER = logging.getLogger(__name__)

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
        """
        Initialize StaticValues.

        Args:
            device_info (Dict[str, Any]): The dictionary containing static device information.
        """
        self._device_info = device_info

    @property
    def sensor_name(self) -> Optional[str]:
        """The device name, or None on error."""
        try:
            return self._device_info.get("NAME")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'NAME': %s", err)
            return None

    @property
    def sensor_serial_number(self) -> Optional[str]:
        """The device serial number, or None on error."""
        try:
            return self._device_info.get("SERIAL_NUMBER")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'SERIAL_NUMBER': %s", err)
            return None

    @property
    def sensor_device_id(self) -> Optional[str]:
        """The device ID, or None on error."""
        try:
            return self._device_info.get("DEVICE_ID")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'DEVICE_ID': %s", err)
            return None

    @property
    def sensor_model(self) -> Optional[str]:
        """The device model, or None on error."""
        try:
            return self._device_info.get("MODEL")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'MODEL': %s", err)
            return None

    @property
    def sensor_model_id(self) -> Optional[str]:
        """The device model ID, or None on error."""
        try:
            return self._device_info.get("MODEL_ID")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'MODEL_ID': %s", err)
            return None

    @property
    def sensor_ownerid(self) -> Optional[str]:
        """The device owner ID, or None on error."""
        try:
            return self._device_info.get("OWNERID")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'OWNERID': %s", err)
            return None

    @property
    def sensor_groupname(self) -> Optional[str]:
        """The device group name, or None on error."""
        try:
            return self._device_info.get("GROUPNAME")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'GROUPNAME': %s", err)
            return None

    @property
    def sensor_fw_version(self) -> Optional[str]:
        """The device firmware version, or None on error."""
        try:
            return self._device_info.get("FW_VERSION")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'FW_VERSION': %s", err)
            return None

    @property
    def sensor_sw_version(self) -> Optional[str]:
        """The device software version, or None on error."""
        try:
            return self._device_info.get("SW_VERSION")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'SW_VERSION': %s", err)
            return None

    @property
    def sensor_api_version(self) -> Optional[str]:
        """The device API version, or None on error."""
        try:
            return self._device_info.get("API_VERSION")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'API_VERSION': %s", err)
            return None

    @property
    def sensor_fw_code(self) -> Optional[str]:
        """The device firmware code, or None on error."""
        try:
            return self._device_info.get("FW_CODE")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'FW_CODE': %s", err)
            return None

    @property
    def sensor_mac(self) -> Optional[str]:
        """The device MAC address, or None on error."""
        try:
            return self._device_info.get("MAC")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'MAC': %s", err)
            return None

    @property
    def sensor_ip(self) -> Optional[str]:
        """The device IP address, or None on error."""
        try:
            return self._device_info.get("IP")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'IP': %s", err)
            return None

    @property
    def sensor_wifi_ssid(self) -> Optional[str]:
        """The device WiFi SSID, or None on error."""
        try:
            return self._device_info.get("WIFI_SSID")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'WIFI_SSID': %s", err)
            return None

    @property
    def sensor_wifi_key(self) -> Optional[str]:
        """The device WiFi key, or None on error."""
        try:
            return self._device_info.get("WIFI_KEY")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'WIFI_KEY': %s", err)
            return None

    @property
    def sensor_ap_ssid(self) -> Optional[str]:
        """The device access point SSID, or None on error."""
        try:
            return self._device_info.get("AP_SSID")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'AP_SSID': %s", err)
            return None

    @property
    def sensor_ap_key(self) -> Optional[str]:
        """The device access point key, or None on error."""
        try:
            return self._device_info.get("AP_KEY")
        except KeyError as err:
            _LOGGER.warning("Error getting static value 'AP_KEY': %s", err)
            return None
