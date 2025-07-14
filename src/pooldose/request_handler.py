"""Request Handler for async API client for SEKO Pooldose."""

import logging
import json
import re
import socket
from typing import Any
from enum import Enum
import asyncio
import aiohttp

# pylint: disable=line-too-long,no-else-return

_LOGGER = logging.getLogger(__name__)

API_VERSION_SUPPORTED = "v1/"

class RequestStatus(Enum):
    """
    Enum for standardized return codes of API and client methods.

    Each status represents a specific result or error case:
    - SUCCESS: Operation was successful.
    - HOST_UNREACHABLE: The host could not be reached (e.g. network error).
    - PARAMS_FETCH_FAILED: params.js could not be fetched or parsed.
    - API_VERSION_UNSUPPORTED: The API version is not supported.
    - NO_DATA: No data was returned or found.
    - LAST_DATA: No new data was found, last valid data was returned.
    - CLIENT_ERROR_SET: Error while setting a value on the client/device.
    - UNKNOWN_ERROR: An unspecified or unexpected error occurred.
    """
    SUCCESS = "success"
    HOST_UNREACHABLE = "host_unreachable"
    PARAMS_FETCH_FAILED = "params_fetch_failed"
    API_VERSION_UNSUPPORTED = "api_version_unsupported"
    NO_DATA = "no_data"
    LAST_DATA = "last_data"
    CLIENT_ERROR_SET = "client_error_set"
    UNKNOWN_ERROR = "unknown_error"

class RequestHandler:
    """
    Handles all HTTP requests to the Pooldose API.
    Only softwareVersion, and apiversion are loaded from params.js.
    """

    def __init__(self, host: str, timeout: int = 10):
        self.host = host
        self.timeout = timeout
        self.last_data = None
        self._headers = {"Content-Type": "application/json"}
        self.software_version = None
        self.api_version = None
        self._connected = False

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
        Check if the host is reachable on port 80 (HTTP).

        Returns:
            bool: True if reachable, False otherwise.
        """
        try:
            with socket.create_connection((self.host, 80), timeout=self.timeout):
                return True
        except (socket.error, socket.timeout) as err:
            _LOGGER.error("Host %s not reachable: %s", self.host, err)
            return False

    async def _get_core_params(self) -> dict | None:
        """
        Fetch and extract softwareVersion and apiversion from params.js.

        Returns:
            dict: Dictionary with the selected parameters, or None on error.
        """
        url = f"http://{self.host}/js_libs/params.js"
        keys = ["softwareVersion", "apiversion"]
        result = {}
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
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
            "api_version_is": self.api_version,
            "api_version_should": API_VERSION_SUPPORTED,
        }
        if not self.api_version:
            _LOGGER.warning("API version not set, cannot check support")
            return RequestStatus.NO_DATA, result
        if self.api_version != API_VERSION_SUPPORTED:
            _LOGGER.warning("Unsupported API version: %s, expected %s", self.api_version, API_VERSION_SUPPORTED)
            return RequestStatus.API_VERSION_UNSUPPORTED, result
        else:
            return RequestStatus.SUCCESS, result

    async def get_debug_config(self):
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
        url = f"http://{self.host}/api/v1/debug/config"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for debug config")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
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
        url = f"http://{self.host}/api/v1/infoRelease"
        payload = {"SOFTWAREVERSION": sw_version}
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for infoRelease")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to fetch infoRelease: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_wifi_station(self):
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
        url = f"http://{self.host}/api/v1/network/wifi/getStation"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for WiFi station info")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
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

    async def get_access_point(self):
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
        url = f"http://{self.host}/api/v1/network/wifi/getAccessPoint"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
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
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to fetch access point info: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_network_info(self):
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
        url = f"http://{self.host}/api/v1/network/info/getInfo"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for network info")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to fetch network info: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_values_raw(self):
        """
        Fetch raw instant values from the device.
        Returns (RequestStatus, data).
        """
        url = f"http://{self.host}/api/v1/DWI/getInstantValues"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    self.last_data = data
                    if not data:
                        _LOGGER.error("No data found for instant values")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Error fetching instant values: %s", err)
            if self.last_data is not None:
                return RequestStatus.LAST_DATA, self.last_data
            return RequestStatus.UNKNOWN_ERROR, None

    async def set_value(self, device_id: dict, path: str, value: Any, value_type: str) -> bool:
        """
        Asynchronously sets a value for a specific device and path using the API.

        Args:
            device_id (dict): The identifier of the device to set the value for.
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
        url = f"http://{self.host}/api/v1/DWI/setInstantValues"
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
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
        except aiohttp.ClientError as e:
            _LOGGER.warning("Client error setting value: %s", e)
            return False
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout error setting value: %s", err)
            return False

        return True

    async def reboot_device(self):
        """
        Reboot the Pooldose device via the API.

        Returns:
            (RequestStatus, bool): Tuple of status and True if the reboot command was sent successfully, False otherwise.
        """
        url = f"http://{self.host}/api/v1/system/reboot"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    return RequestStatus.SUCCESS, True
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Error sending reboot command: %s", err)
            return RequestStatus.UNKNOWN_ERROR, False
