"""Client for async API client for SEKO Pooldose."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional
from pooldose.values.instant_values import InstantValues
from pooldose.request_handler import RequestHandler
from pooldose.request_status import RequestStatus
from pooldose.values.static_values import StaticValues
from pooldose.mappings.mapping_info import (
    MappingInfo,
    SensorMapping,
    BinarySensorMapping,
    NumberMapping,
    SwitchMapping,
    SelectMapping,
)

# pylint: disable=line-too-long,too-many-instance-attributes

_LOGGER = logging.getLogger(__name__)

API_VERSION_SUPPORTED = "v1/"

class PooldoseClient:
    """
    Async client for SEKO Pooldose API.
    All getter methods return (status, data) and log errors.
    """

    def __init__(self, host: str, timeout: int = 30, *, include_sensitive_data: bool = False, use_ssl: bool = False, port: Optional[int] = None, ssl_verify: bool = True) -> None:  # pylint: disable=too-many-arguments
        """
        Initialize the Pooldose client.

        Args:
            host (str): The host address of the Pooldose device.
            timeout (int): Timeout for API requests in seconds.
            include_sensitive_data (bool): If True, fetch WiFi and AP keys.
            use_ssl (bool): If True, use HTTPS instead of HTTP.
            port (Optional[int]): Custom port for connections. Defaults to 80 for HTTP, 443 for HTTPS.
            ssl_verify (bool): If True, verify SSL certificates. Only used when use_ssl=True.
        """
        self._host = host
        self._timeout = timeout
        self._include_sensitive_data = include_sensitive_data
        self._use_ssl = use_ssl
        self._port = port
        self._ssl_verify = ssl_verify
        self._last_data = None
        self._request_handler = None

        # Initialize device info with default or placeholder values
        self.device_info = {
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

        # Mapping-Status und Mapping-Cache
        self._mapping_status = None
        self._mapping_info: Optional[MappingInfo] = None
        self._connected = False

    async def connect(self) -> RequestStatus:
        """
        Asynchronously connect to the device and initialize all components.
        
        Returns:
            RequestStatus: SUCCESS if connected successfully, otherwise appropriate error status.
        """
        # Create and connect request handler
        self._request_handler = RequestHandler(
            self._host,
            self._timeout,
            use_ssl=self._use_ssl,
            port=self._port,
            ssl_verify=self._ssl_verify
        )
        status = await self._request_handler.connect()
        if status != RequestStatus.SUCCESS:
            _LOGGER.error("Failed to create RequestHandler: %s", status)
            return status

        # Load device information
        status = await self._load_device_info()
        if status != RequestStatus.SUCCESS:
            _LOGGER.error("Failed to load device info: %s", status)
            return status

        self._connected = True
        _LOGGER.debug("Initialized Pooldose client with device info: %s", self.device_info)
        return RequestStatus.SUCCESS

    def check_apiversion_supported(self) -> tuple[RequestStatus, dict]:
        """
        Check if the loaded API version matches the supported version.

        Returns:
            tuple: (RequestStatus, dict)
                - dict contains:
                    "api_version_is": the current API version (or None if not set)
                    "api_version_should": the supported API version
                - RequestStatus.SUCCESS if supported,
                - RequestStatus.API_VERSION_UNSUPPORTED if not supported,
                - RequestStatus.NO_DATA if not set.
        """
        result = {
            "api_version_is": self._request_handler.api_version,
            "api_version_should": API_VERSION_SUPPORTED,
        }
        if not self._request_handler.api_version:
            _LOGGER.warning("API version not set, cannot check support")
            return RequestStatus.NO_DATA, result
        if self._request_handler.api_version != API_VERSION_SUPPORTED:
            _LOGGER.warning("Unsupported API version: %s, expected %s", self._request_handler.api_version, API_VERSION_SUPPORTED)
            return RequestStatus.API_VERSION_UNSUPPORTED, result

        return RequestStatus.SUCCESS, result

    async def _load_device_info(self) -> RequestStatus:
        """
        Load device information from the request handler.
        This method should be called after a successful connection.
        """
        if not self._request_handler:
            raise RuntimeError("RequestHandler is not initialized. Call async_connect first.")

        # Fetch core parameters and device info
        self.device_info["API_VERSION"] = self._request_handler.api_version

        # Load device information
        status, debug_config = await self._request_handler.get_debug_config()
        if status != RequestStatus.SUCCESS or not debug_config:
            _LOGGER.error("Failed to fetch debug config: %s", status)
            return status, None
        if (gateway := debug_config.get("GATEWAY")) is not None:
            self.device_info["SERIAL_NUMBER"] = gateway.get("DID")
            self.device_info["NAME"] = gateway.get("NAME")
            self.device_info["SW_VERSION"] = gateway.get("FW_REL")
        if (device := debug_config.get("DEVICES")[0]) is not None:
            self.device_info["DEVICE_ID"] = device.get("DID")
            self.device_info["MODEL"] = device.get("NAME")
            self.device_info["MODEL_ID"] = device.get("PRODUCT_CODE")
            self.device_info["FW_VERSION"] = device.get("FW_REL")
            self.device_info["FW_CODE"] = device.get("FW_CODE")
        await asyncio.sleep(0.5)

        # Load mapping information
        self._mapping_info = await MappingInfo.load(
            self.device_info.get("MODEL_ID"),
            self.device_info.get("FW_CODE")
        )

        # WiFi station info
        status, wifi_station = await self._request_handler.get_wifi_station()
        if status != RequestStatus.SUCCESS or not wifi_station:
            _LOGGER.warning("Failed to fetch WiFi station info: %s", status)
        else:
            self.device_info["WIFI_SSID"] = wifi_station.get("SSID")
            self.device_info["MAC"] = wifi_station.get("MAC")
            self.device_info["IP"] = wifi_station.get("IP")
            # Only include WiFi key if explicitly requested
            if self._include_sensitive_data:
                self.device_info["WIFI_KEY"] = wifi_station.get("KEY")
        await asyncio.sleep(0.5)

        # Access point info
        status, access_point = await self._request_handler.get_access_point()
        if status != RequestStatus.SUCCESS or not access_point:
            _LOGGER.warning("Failed to fetch access point info: %s", status)
        else:
            self.device_info["AP_SSID"] = access_point.get("SSID")
            # Only include AP key if explicitly requested
            if self._include_sensitive_data:
                self.device_info["AP_KEY"] = access_point.get("KEY")
        await asyncio.sleep(0.5)

        # Network info
        status, network_info = await self._request_handler.get_network_info()
        if status != RequestStatus.SUCCESS or not network_info:
            _LOGGER.error("Failed to fetch network info: %s", status)
            return status, None
        self.device_info["OWNERID"] = network_info.get("OWNERID")
        self.device_info["GROUPNAME"] = network_info.get("GROUPNAME")

        if self._include_sensitive_data:
            _LOGGER.info("Included WiFi and AP keys (use include_sensitive_data=False to exclude)")

        return RequestStatus.SUCCESS

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected to the device."""
        return self._connected

    def static_values(self) -> tuple[RequestStatus, StaticValues | None]:
        """
        Get the static device values as a StaticValues object.

        Returns:
            tuple: (RequestStatus, StaticValues|None) - Status and static values object.
        """
        try:
            return RequestStatus.SUCCESS, StaticValues(self.device_info)
        except (ValueError, TypeError, KeyError) as err:
            _LOGGER.warning("Error creating StaticValues: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    def available_types(self) -> dict[str, list[str]]:
        """
        Returns a dictionary mapping type categories to lists of available type names.

        Returns:
            dict[str, list[str]]: A dictionary where each key is a type category (as a string),
            and each value is a list of available type names (as strings). If no mapping information
            is available, returns an empty dictionary.
        """
        return self._mapping_info.available_types() if self._mapping_info else {}

    def available_sensors(self) -> dict[str, SensorMapping]:
        """
        Returns all available sensors from the mapping as SensorMapping objects.
        """
        return self._mapping_info.available_sensors() if self._mapping_info else {}

    def available_binary_sensors(self) -> dict[str, BinarySensorMapping]:
        """
        Returns all available binary sensors from the mapping as BinarySensorMapping objects.
        """
        return self._mapping_info.available_binary_sensors() if self._mapping_info else {}

    def available_numbers(self) -> dict[str, NumberMapping]:
        """
        Returns all available numbers from the mapping as NumberMapping objects.
        """
        return self._mapping_info.available_numbers() if self._mapping_info else {}

    def available_switches(self) -> dict[str, SwitchMapping]:
        """
        Returns all available switches from the mapping as SwitchMapping objects.
        """
        return self._mapping_info.available_switches() if self._mapping_info else {}

    def available_selects(self) -> dict[str, SelectMapping]:
        """
        Returns all available selects from the mapping as SelectMapping objects.
        """
        return self._mapping_info.available_selects() if self._mapping_info else {}

    async def instant_values(self) -> tuple[RequestStatus, InstantValues | None]:
        """
        Fetch the current instant values from the Pooldose device.

        Returns:
            tuple: (RequestStatus, InstantValues|None) - Status and instant values object.
        """
        try:
            status, raw_data = await self._request_handler.get_values_raw()
            if status != RequestStatus.SUCCESS or raw_data is None:
                return status, None
            # Mapping aus Cache verwenden
            mapping = self._mapping_info.mapping if self._mapping_info else None
            if mapping is None:
                return RequestStatus.UNKNOWN_ERROR, None
            device_id = self.device_info["DEVICE_ID"]
            device_raw_data = raw_data.get("devicedata", {}).get(device_id, {})
            model_id = self.device_info["MODEL_ID"]
            fw_code = self.device_info["FW_CODE"]
            prefix = f"{model_id}_FW{fw_code}_"
            return RequestStatus.SUCCESS, InstantValues(device_raw_data, mapping, prefix, device_id, self._request_handler)
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Error creating InstantValues: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None
