"""Client for async API client for SEKO Pooldose."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Tuple

import aiohttp
from getmac import get_mac_address

from pooldose.type_definitions import (
    APIVersionResponse,
    DeviceInfoDict,
    StructuredValuesDict,
)

from pooldose.constants import get_default_device_info
from pooldose.mappings.mapping_info import MappingInfo
from pooldose.request_handler import RequestHandler
from pooldose.request_status import RequestStatus
from pooldose.values.instant_values import InstantValues
from pooldose.values.static_values import StaticValues

# pylint: disable=line-too-long,too-many-instance-attributes

_LOGGER = logging.getLogger(__name__)

API_VERSION_SUPPORTED = "v1/"

class PooldoseClient:
    """
    Async client for SEKO Pooldose API.
    All getter methods return (status, data) and log errors.
    """

    def __init__(self, host: str, timeout: int = 30, *, websession: Optional[aiohttp.ClientSession] = None, include_sensitive_data: bool = False, include_mac_lookup: bool = False, use_ssl: bool = False, port: Optional[int] = None, ssl_verify: bool = True) -> None:  # pylint: disable=too-many-arguments
        """
        Initialize the Pooldose client.

        Args:
            host (str): The host address of the Pooldose device.
            timeout (int): Timeout for API requests in seconds.
            websession (Optional[aiohttp.ClientSession]): Optional external ClientSession for HTTP requests.
                If provided, will be used for all API calls (mainly for Home Assistant integration).
            include_sensitive_data (bool): If True, fetch WiFi and AP keys.
            include_mac_lookup (bool): If True, try to determine device MAC address from IP using getmac library.
            use_ssl (bool): If True, use HTTPS instead of HTTP.
            port (Optional[int]): Custom port for connections. Defaults to 80 for HTTP, 443 for HTTPS.
            ssl_verify (bool): If True, verify SSL certificates. Only used when use_ssl=True.
        """
        self._host = host
        self._timeout = timeout
        self._include_sensitive_data = include_sensitive_data
        self._include_mac_lookup = include_mac_lookup
        self._use_ssl = use_ssl
        self._port = port
        self._ssl_verify = ssl_verify
        self._last_data = None
        self._websession = websession
        self._request_handler: RequestHandler | None = None

        # Initialize device info with default or placeholder values
        self.device_info: DeviceInfoDict = get_default_device_info()

        # Mapping-Status und Mapping-Cache
        self._mapping_status = None
        self._mapping_info: MappingInfo | None = None
        self._connected = False

    async def connect(self) -> RequestStatus:
        """Asynchronously connect to the device and initialize all components.

        Returns:
            RequestStatus: SUCCESS if connected successfully, otherwise appropriate error status.
        """
        # Create and connect request handler
        self._request_handler = RequestHandler(
            self._host,
            self._timeout,
            websession=self._websession if hasattr(self, '_websession') else None,
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

    @property
    def request_handler(self) -> RequestHandler:
        """Get the request handler, ensuring it's initialized."""
        if self._request_handler is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        return self._request_handler

    def check_apiversion_supported(self) -> Tuple[RequestStatus, APIVersionResponse]:
        """
        Check if the loaded API version matches the supported version.

        Returns:
            tuple: (RequestStatus, dict)
                - dict contains:
                    "api_version_is": the current API version (or None if not set)
                    "api_version_should": the expected API version
                - RequestStatus.NO_DATA if not set.
        """
        if self._request_handler is None:
            return RequestStatus.NO_DATA, {
                "api_version_is": None,
                "api_version_should": API_VERSION_SUPPORTED,
            }

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

    async def _load_device_info(self) -> RequestStatus:  # pylint: disable=too-many-branches, too-many-statements
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
            return status
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
        model_id = self.device_info.get("MODEL_ID")
        fw_code = self.device_info.get("FW_CODE")
        if model_id and fw_code:
            self._mapping_info = await MappingInfo.load(str(model_id), str(fw_code))
        else:
            _LOGGER.warning("Missing MODEL_ID or FW_CODE, cannot load mapping")
            self._mapping_info = MappingInfo(mapping=None, status=RequestStatus.NO_DATA)

        # WiFi station info
        status, wifi_station = await self._request_handler.get_wifi_station()
        if status != RequestStatus.SUCCESS or not wifi_station:
            _LOGGER.warning("Failed to fetch WiFi station info: %s", status)
        else:
            self.device_info["WIFI_SSID"] = wifi_station.get("SSID")
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
            return status
        self.device_info["OWNERID"] = network_info.get("OWNERID")
        self.device_info["GROUPNAME"] = network_info.get("GROUPNAME")

        if self._include_sensitive_data:
            _LOGGER.info("Included WiFi and AP keys (use include_sensitive_data=False to exclude)")

        # Optionally: MAC address via getmac library (using arp which may not work on all network topologies)
        if self._include_mac_lookup:
            if self.device_info["IP"]:
                self.device_info["MAC"] = get_mac_address(ip=self.device_info["IP"])
                if not self.device_info["MAC"]:
                    _LOGGER.warning("Failed to fetch MAC address via getmac library for IP: %s", self.device_info["IP"])
            else:
                _LOGGER.warning("IP address not set, cannot fetch MAC address via getmac library")
                self.device_info["MAC"] = None

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

    async def instant_values(self) -> tuple[RequestStatus, InstantValues | None]:
        """
        Fetch the current instant values from the Pooldose device.

        Returns:
            tuple: (RequestStatus, InstantValues|None) - Status and instant values object.
        """
        try:
            if self._request_handler is None:
                return RequestStatus.NO_DATA, None

            status, raw_data = await self._request_handler.get_values_raw()
            if status != RequestStatus.SUCCESS or raw_data is None:
                return status, None
            # Mapping aus Cache verwenden
            mapping = self._mapping_info.mapping if self._mapping_info else None
            if mapping is None:
                return RequestStatus.UNKNOWN_ERROR, None
            device_id = str(self.device_info.get("DEVICE_ID", ""))
            device_raw_data = raw_data.get("devicedata", {}).get(device_id, {})
            model_id = str(self.device_info.get("MODEL_ID", ""))
            fw_code = str(self.device_info.get("FW_CODE", ""))
            prefix = f"{model_id}_FW{fw_code}_"
            return RequestStatus.SUCCESS, InstantValues(device_raw_data, mapping, prefix, device_id, self._request_handler)
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Error creating InstantValues: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def instant_values_structured(self) -> Tuple[RequestStatus, StructuredValuesDict]:
        """
        Get instant values in structured JSON format with types as top-level keys.

        Returns:
            Tuple[RequestStatus, Dict[str, Any]]: Status and structured data dict.
        """
        # Get instant values object
        status, instant_values = await self.instant_values()
        if status != RequestStatus.SUCCESS or instant_values is None:
            return status, {}

        try:
            # Let InstantValues handle the structuring
            structured_data = instant_values.to_structured_dict()
            return RequestStatus.SUCCESS, structured_data

        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.error("Error creating structured instant values: %s", err)
            return RequestStatus.UNKNOWN_ERROR, {}
