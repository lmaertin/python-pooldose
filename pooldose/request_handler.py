import aiohttp
import logging
import json
import re
from typing import Any, Optional

_LOGGER = logging.getLogger(__name__)

API_VERSION_SUPPORTED = "v1/"

class RequestHandler:
    """
    Handles all HTTP get/post requests to the Pooldose API.
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
            RequestHandler: An initialized RequestHandler instance.
        """
        self = cls(host, timeout)
        params = await self._get_core_params()
        if params:
            self.softwareVersion = params.get("softwareVersion")
            self.apiversion = params.get("apiversion")
        else:
            _LOGGER.warning("Could not fetch core params from params.js")
            return None
        return self

    async def _get_core_params(self) -> dict | None:
        """
        Fetch and extract softwareVersion and apiversion from params.js file which needs no api call itself.

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
            _LOGGER.warning("Error fetching or parsing core params from params.js: %s", err)
            return None

    async def get_debug_config(self) -> dict | None:
        url = f"http://{self.host}/api/v1/debug/config"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    return await resp.json()
                _LOGGER.error("No data found for debug config: %s", err)
                return None
        except Exception as err:
            _LOGGER.error("Error fetching debug config: %s", err)
            return None

    async def get_wifi_station(self) -> Optional[dict]:
        url = f"http://{self.host}/api/v1/network/wifi/getStation"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
        except Exception as err:
            text = str(err)
            text = text.replace("\\\\n", "").replace("\\\\t", "")
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                data = json.loads(text[json_start:json_end])
            else:
                _LOGGER.error("Failed to fetch WiFi station info: %s", err)
                return None
        if not data:
            _LOGGER.error("No data found for WiFi station info: %s", err)
            return None
        return data

    async def get_access_point(self) -> Optional[dict]:
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
                        return await resp.json()
                    _LOGGER.error("No data found for access point info: %s", err)
                    return None
        except Exception as err:
            _LOGGER.error("Failed to fetch access point info: %s", err)
            return None

    async def get_network_info(self) -> Optional[dict]:
        url = f"http://{self.host}/api/v1/network/info/getInfo"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    return await resp.json()
                _LOGGER.error("No data found for network info: %s", err)
                return None
        except Exception as err:
            _LOGGER.error("Failed to fetch network info: %s", err)
            return None

    async def get_values_raw(self) -> Optional[dict]:
        """
        Fetch raw instant values from the device.
        Returns None and logs a warning on error.
        """
        url = f"http://{self.host}/api/v1/DWI/getInstantValues"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    self.last_data = data
                    return data
                _LOGGER.error("No data found for instant values: %s", err)
                return None
        except Exception as err:
            _LOGGER.warning("Error fetching instant values: %s", err)
            if self.last_data is not None:
                return self.last_data
            return None

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
        if payload is None:
            _LOGGER.warning("No payload created for set_value, path: %s, value: %s, type: %s", path, value, value_type)
            return False  
        
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
        except aiohttp.ClientError as e:
            _LOGGER.warning("Client error setting instant value: %s", e)
            return False
        except Exception as err:
            _LOGGER.error("Error setting instant value: %s", err)
            return False

        return True

    async def reboot_device(self) -> bool:
        """
        Reboot the Pooldose device via the API.

        Returns:
            bool: True if the reboot command was sent successfully, False otherwise.
        """
        url = f"http://{self.host}/api/v1/system/reboot"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    return True
        except Exception as err:
            _LOGGER.warning("Error sending reboot command: %s", err)
            return False

    def check_apiversion_supported(self) -> bool:
        """
        Check if the loaded API version matches the supported version.

        Returns:
            bool: True if supported, False otherwise.
        """
        if not self.apiversion:
            _LOGGER.warning("API version not set, cannot check support")
            return False
        if self.apiversion != API_VERSION_SUPPORTED:
            _LOGGER.warning("Unsupported API version: %s, expected to start with %s", self.apiversion, API_VERSION_SUPPORTED)
            return False
        else:
            return True

    @property
    def software_version(self) -> Optional[str]:
        """Return the software version loaded from params.js."""
        return self.softwareVersion

    @property
    def api_version(self) -> Optional[str]:
        """Return the API version loaded from params.js."""
        return self.apiversion