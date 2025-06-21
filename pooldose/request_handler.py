import aiohttp
import logging
import json
import re
import socket
from typing import Any, Optional
from enum import Enum

_LOGGER = logging.getLogger(__name__)

API_VERSION_SUPPORTED = "v1/"

class RequestStatus(Enum):
    SUCCESS = "success"
    HOST_UNREACHABLE = "host unreachable"
    PARAMS_FETCH_FAILED = "params fetch failed"
    API_VERSION_UNSUPPORTED = "api version unsupported"
    NO_DATA = "no data available"
    CLIENT_ERROR_SET = "client error in set value"
    UNKNOWN_ERROR = "unknown error"

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
        self.softwareVersion = None
        self.apiversion = None

    @classmethod
    async def create(cls, host: str, timeout: int = 10):
        """
        Asynchronous factory method to create and initialize the RequestHandler.

        Returns:
            (RequestStatus, RequestHandler|None): Tuple of status and handler instance.
        """
        self = cls(host, timeout)
        if not self.check_host_reachable():
            _LOGGER.error("Host %s is not reachable.", host)
            return RequestStatus.HOST_UNREACHABLE, None
        params = await self._get_core_params()
        if not params:
            _LOGGER.warning("Could not fetch core params")
            return RequestStatus.PARAMS_FETCH_FAILED, None
        self.softwareVersion = params.get("softwareVersion")
        self.apiversion = params.get("apiversion")
        return RequestStatus.SUCCESS, self

    def check_host_reachable(self) -> bool:
        """
        Check if the host is reachable on port 80 (HTTP).

        Returns:
            bool: True if reachable, False otherwise.
        """
        try:
            with socket.create_connection((self.host, 80), timeout=self.timeout):
                return True
        except Exception as err:
            _LOGGER.error("Host %s not reachable: %s", self.host, err)
            return False

    async def _get_core_params(self) -> dict | RequestStatus:
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

            return result
        except Exception as err:
            _LOGGER.warning("Error fetching or parsing core params: %s", err)
            return None

    def check_apiversion_supported(self) -> RequestStatus:
        """
        Check if the loaded API version matches the supported version.

        Returns:
            RequestStatus: SUCCESS if supported, API_VERSION_UNSUPPORTED otherwise.
        """
        if not self.apiversion:
            _LOGGER.warning("API version not set, cannot check support")
            return RequestStatus.NO_DATA
        if self.apiversion != API_VERSION_SUPPORTED:
            _LOGGER.warning("Unsupported API version: %s, expected %s", self.apiversion, API_VERSION_SUPPORTED)
            return RequestStatus.API_VERSION_UNSUPPORTED
        else:
            return RequestStatus.SUCCESS

    @property
    def software_version(self) -> Optional[str]:
        """Return the software version loaded from params.js."""
        return self.softwareVersion

    @property
    def api_version(self) -> Optional[str]:
        """Return the API version loaded from params.js."""
        return self.apiversion

    async def get_debug_config(self):
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
        except Exception as err:
            _LOGGER.error("Error fetching debug config: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_info_release(self, sw_version: str):
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
        except Exception as err:
            _LOGGER.error("Failed to fetch infoRelease: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_wifi_station(self):
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
        except Exception as err:
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
            _LOGGER.error("No data found for WiFi station info: %s", err)
            return RequestStatus.NO_DATA, None
        return RequestStatus.SUCCESS, data

    async def get_access_point(self):
        url = f"http://{self.host}/api/v1/network/wifi/getAccessPoint"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    text = await resp.text()
                    json_start = text.find("{")
                    json_end = text.rfind("}") + 1
                    if json_start != -1 and json_end != -1:
                        data = await resp.json()
                    if not data:
                        _LOGGER.error("No data found for access point info")
                        return RequestStatus.NO_DATA, None
                    return RequestStatus.SUCCESS, data
        except Exception as err:
            _LOGGER.error("Failed to fetch access point info: %s", err)
            return RequestStatus.UNKNOWN_ERROR, None

    async def get_network_info(self):
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
        except Exception as err:
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
        except Exception as err:
            _LOGGER.warning("Error fetching instant values: %s", err)
            if self.last_data is not None:
                return RequestStatus.SUCCESS, self.last_data
            return RequestStatus.UNKNOWN_ERROR, None

    async def set_value(self, device_id: dict, path: str, value: Any, value_type: str) -> bool:
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
        except Exception as err:
            _LOGGER.error("Error setting value: %s", err)
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
        except Exception as err:
            _LOGGER.warning("Error sending reboot command: %s", err)
            return RequestStatus.UNKNOWN_ERROR, False