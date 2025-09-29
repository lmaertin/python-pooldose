"""Request Handler for async API client for SEKO Pooldose."""

import asyncio
import json
import logging
import re
import socket
import ssl
from typing import Any, Optional, Tuple, Union

import aiohttp

from pooldose.type_definitions import (
    AccessPointDict,
    DebugConfigDict,
    NetworkInfoDict,
    WiFiStationDict,
)

from pooldose.request_status import RequestStatus

# pylint: disable=line-too-long,no-else-return

_LOGGER = logging.getLogger(__name__)

# Language constant for device language API - always use English as it's guaranteed to exist
_DEVICE_LANGUAGE = "en"

class RequestHandler:  # pylint: disable=too-many-instance-attributes
    """
    Handles all HTTP requests to the Pooldose API.
    Only softwareVersion, and apiversion are loaded from params.js.
    """

    def __init__(self, host: str, timeout: int = 10, *, websession: Optional[aiohttp.ClientSession] = None, use_ssl: bool = False, port: Optional[int] = None, ssl_verify: bool = True):  # pylint: disable=too-many-arguments
        self.host = host
        self.timeout = timeout
        self.use_ssl = use_ssl
        self.port = port if port is not None else (443 if use_ssl else 80)
        self.ssl_verify = ssl_verify
        self.last_data = None
        self._headers = {"Content-Type": "application/json"}
        self.software_version = None
        self.api_version = None
        self._connected = False
        # External session from Home Assistant (or None)
        self._websession = websession
        # Configure SSL context
        self._ssl_context: Union[ssl.SSLContext, bool, None] = None
        if self.use_ssl:
            self._ssl_context = ssl.create_default_context() if self.ssl_verify else False

    def _get_ssl_connector(self) -> Optional[aiohttp.TCPConnector]:
        """Get SSL connector for aiohttp sessions."""
        if self.use_ssl:
            # Ensure we pass the correct type to TCPConnector
            ssl_context: Union[bool, ssl.SSLContext] = self._ssl_context if self._ssl_context is not None else False
            return aiohttp.TCPConnector(ssl=ssl_context)
        return None

    async def _get_session(self) -> Tuple[aiohttp.ClientSession, bool]:
        """
        Get a session for HTTP requests.

        Returns:
            Tuple of (session, close_when_done)
                - session: The aiohttp.ClientSession to use for requests
                - close_when_done: True if this is an internal session that should be closed when done
        """
        if self._websession:
            # Use external session
            return self._websession, False

        # Create a new session with SSL connector if needed
        connector = self._get_ssl_connector()
        session = aiohttp.ClientSession(connector=connector)
        return session, True

    async def connect(self) -> RequestStatus:
        """
        Asynchronously connect to the device and initialize connection parameters.

        Returns:
            RequestStatus: SUCCESS if connected successfully, otherwise appropriate error status.
        """
        if not self.check_host_reachable():
            return RequestStatus.HOST_UNREACHABLE

        params = await self._get_core_params()
        if not params:
            _LOGGER.error("Could not fetch core params")
            return RequestStatus.PARAMS_FETCH_FAILED

        self.software_version = params.get("softwareVersion")
        self.api_version = params.get("apiversion")
        self._connected = True

        return RequestStatus.SUCCESS

    @property
    def is_connected(self) -> bool:
        """Check if the handler is connected to the device."""
        return self._connected

    def check_host_reachable(self) -> bool:
        """
        Check if the host is reachable on the configured port.

        Returns:
            bool: True if reachable, False otherwise.
        """
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout):
                return True
        except (socket.error, socket.timeout) as err:
            _LOGGER.error("Host %s not reachable on port %d: %s", self.host, self.port, err)
            return False

    def _build_url(self, path: str) -> str:
        """
        Build the full URL for an API endpoint.

        Args:
            path (str): The API endpoint path (e.g., "/api/v1/debug/config")

        Returns:
            str: The complete URL
        """
        scheme = "https" if self.use_ssl else "http"
        if self.port != (443 if self.use_ssl else 80):
            return f"{scheme}://{self.host}:{self.port}{path}"
        else:
            return f"{scheme}://{self.host}{path}"

    async def _get_core_params(self) -> dict[str, Any] | None:
        """
        Fetch and extract softwareVersion and apiversion from params.js.

        Returns:
            dict: Dictionary with the selected parameters, or None on error.
        """
        url = self._build_url("/js_libs/params.js")
        keys = ["softwareVersion", "apiversion"]
        result = {}
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            connector = self._get_ssl_connector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    js_text = await resp.text()

            for key in keys:
                match = re.search(rf'{key}\s*:\s*["\']([^"\']+)["\']', js_text)
                if match:
                    result[key] = match.group(1)
                else:
                    result[key] = None

            if len(result) < len(keys):
                _LOGGER.error("Not all parameters found in params.js: %s", result)
                return None

            return result
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Error fetching core params: %s", err)
            return None

    async def get_debug_config(self) -> Tuple[RequestStatus, Optional[DebugConfigDict]]:
        """
        Asynchronously fetches the debug configuration from the server.

        Sends a GET request to the /api/v1/debug/config endpoint of the configured host.
        Handles HTTP errors and timeouts, and returns the request status along with the response data.

        Returns:
            Tuple[RequestStatus, Optional[dict]]:
                - RequestStatus.SUCCESS and the configuration data if the request is successful.
                - RequestStatus.NO_DATA and None if no data is found in the response.
                - RequestStatus.UNKNOWN_ERROR and None if an error occurs during the request.
        """
        url = self._build_url("/api/v1/debug/config")
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            session, close_session = await self._get_session()
            try:
                async with session.get(url, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for debug config")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
            finally:
                if close_session:
                    await session.close()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Error fetching debug config: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_info_release(self, sw_version: str):
        """
        Asynchronously fetches release information for a given software version from the API.

        Args:
            sw_version (str): The software version to query for release information.

        Returns:
            Tuple[RequestStatus, Optional[dict]]:
                - RequestStatus.SUCCESS and the response data if the request is successful.
                - RequestStatus.NO_DATA and None if no data is found in the response.
                - RequestStatus.UNKNOWN_ERROR and None if a request or timeout error occurs.

        Raises:
            None. All exceptions are handled internally and logged.
        """
        url = self._build_url("/api/v1/infoRelease")
        payload = {"SOFTWAREVERSION": sw_version}
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            session, close_session = await self._get_session()
            try:
                async with session.post(url, json=payload, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for infoRelease")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
            finally:
                if close_session:
                    await session.close()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to fetch infoRelease: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_wifi_station(self) -> Tuple[RequestStatus, Optional[WiFiStationDict]]:
        """
        Asynchronously retrieves WiFi station information from the device.

        Sends a POST request to the device's WiFi station API endpoint and returns the status and data.

        Returns:
            Tuple[RequestStatus, Optional[dict]]:
                - RequestStatus.SUCCESS and the response data if successful.
                - RequestStatus.NO_DATA and None if no data is found.
                - RequestStatus.UNKNOWN_ERROR and None if an error occurs.

        Raises:
            None: All exceptions are handled internally and logged.
        """
        url = self._build_url("/api/v1/network/wifi/getStation")
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            session, close_session = await self._get_session()
            try:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for WiFi station info")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
            finally:
                if close_session:
                    await session.close()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            text = str(err)
            text = text.replace("\\\\n", "").replace("\\\\t", "")
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                data = json.loads(text[json_start:json_end])
            else:
                _LOGGER.error("Failed to fetch WiFi station info: %s", err)
                return RequestStatus.UNKNOWN_ERROR, None
        if not data:
            _LOGGER.error("No data found for WiFi station info")
            return RequestStatus.NO_DATA, None
        return RequestStatus.SUCCESS, data

    async def get_access_point(self) -> Tuple[RequestStatus, Optional[AccessPointDict]]:
        """
        Asynchronously retrieves the WiFi access point information from the device.

        Sends a POST request to the device's `/api/v1/network/wifi/getAccessPoint` endpoint.
        Handles response parsing, error handling, and timeout management.

        Returns:
            tuple: A tuple containing a `RequestStatus` enum value and the response data (dict) if successful,
                   or `None` if no data is found or an error occurs.

        Raises:
            None: All exceptions are handled internally and logged.
        """
        url = self._build_url("/api/v1/network/wifi/getAccessPoint")
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            session, close_session = await self._get_session()
            try:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    text = await resp.text()
                    json_start = text.find("{")
                    json_end = text.rfind("}") + 1
                    data = None
                    if json_start != -1 and json_end != -1:
                        data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for access point info")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
            finally:
                if close_session:
                    await session.close()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to fetch access point info: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_network_info(self) -> Tuple[RequestStatus, Optional[NetworkInfoDict]]:
        """
        Asynchronously fetches network information from the specified host's API endpoint.

        Sends a POST request to the `/api/v1/network/info/getInfo` endpoint using the configured host and headers.
        Handles request timeouts and client errors gracefully.

        Returns:
            tuple: A tuple containing a `RequestStatus` enum value and the response data (dict) if successful,
                   or `None` if no data is found or an error occurs.

        Raises:
            None: All exceptions are handled internally and logged.
        """
        url = self._build_url("/api/v1/network/info/getInfo")
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            session, close_session = await self._get_session()
            try:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for network info")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
            finally:
                if close_session:
                    await session.close()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to fetch network info: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_values_raw(self) -> Tuple[RequestStatus, Optional[Any]]:
        """
        Fetch raw instant values from the device.
        Returns (RequestStatus, data).
        """
        url = self._build_url("/api/v1/DWI/getInstantValues")
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            session, close_session = await self._get_session()
            try:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    self.last_data = data
                    if not data:
                        _LOGGER.error("No data found for instant values")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
            finally:
                if close_session:
                    await session.close()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Error fetching instant values: %s", err)
            if self.last_data is not None:
                return RequestStatus.LAST_DATA, self.last_data
            return RequestStatus.UNKNOWN_ERROR, None

    async def set_value(self, device_id: str, path: str, value: Any, value_type: str) -> bool:
        """
        Asynchronously sets a value for a specific device and path using the API.

        Args:
            device_id (str): The identifier of the device to set the value for.
            path (str): The path within the device to set the value.
            value (Any): The value to set.
            value_type (str): The type of the value (e.g., "int", "float", "str").

        Returns:
            bool: True if the value was set successfully, False otherwise.

        Raises:
            aiohttp.ClientError: If there is a client error during the request.
            asyncio.TimeoutError: If the request times out.

        Logs:
            Warnings for client errors and errors for timeout issues.
        """
        url = self._build_url("/api/v1/DWI/setInstantValues")
        payload = {
            device_id: {
                path: [
                    {
                        "value": value,
                        "type": value_type.upper()
                    }
                ]
            }
        }
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            connector = self._get_ssl_connector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, json=payload, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
        except aiohttp.ClientError as e:
            _LOGGER.warning("Client error setting value: %s", e)
            return False
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout error setting value: %s", err)
            return False

        return True

    def _extract_device_id(self, instant_values_data: dict) -> str | None:
        """
        Extract the device ID from instant values data.

        Args:
            instant_values_data (dict): The raw data from get_values_raw()

        Returns:
            str | None: The device ID (e.g., "0123456789_DEVICE") or None if not found
        """
        try:
            device_data = instant_values_data.get("devicedata", {})
            # Get the first (and usually only) device ID key
            device_ids = list(device_data.keys())
            if device_ids:
                return device_ids[0]
            return None
        except (AttributeError, KeyError) as err:
            _LOGGER.error("Error extracting device ID: %s", err)
            return None

    async def get_device_language(self, device_id: str | None = None):
        """
        Asynchronously fetches device language/labels from the API.
        Always uses English language as it's guaranteed to be available.

        Args:
            device_id (str | None): The device ID. If None, will try to get it from last_data or fetch it.

        Returns:
            Tuple[RequestStatus, Optional[dict]]:
                - RequestStatus.SUCCESS and the language data if successful.
                - RequestStatus.NO_DATA and None if no data is found.
                - RequestStatus.UNKNOWN_ERROR and None if an error occurs.
        """
        # If no device_id provided, try to extract from last_data or fetch it
        if device_id is None:
            if self.last_data is not None:
                device_id = self._extract_device_id(self.last_data)
            else:
                # Try to fetch instant values to get device_id
                status, data = await self.get_values_raw()
                if status == RequestStatus.SUCCESS and data:
                    device_id = self._extract_device_id(data)

            if device_id is None:
                _LOGGER.error("Could not determine device ID")
                return RequestStatus.NO_DATA, None

        url = self._build_url("/api/v1/DWI/getDeviceLanguage")
        payload = {
            "DeviceId": device_id,
            "LANG": _DEVICE_LANGUAGE
        }

        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            connector = self._get_ssl_connector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, json=payload, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for device language")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to fetch device language: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def reboot_device(self):
        """
        Reboot the Pooldose device via the API.

        Returns:
            (RequestStatus, bool): Tuple of status and True if the reboot command was sent successfully, False otherwise.
        """
        url = self._build_url("/api/v1/system/reboot")
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            connector = self._get_ssl_connector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    return RequestStatus.SUCCESS, True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Error sending reboot command: %s", err)
            return RequestStatus.UNKNOWN_ERROR, False
