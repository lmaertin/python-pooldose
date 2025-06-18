import asyncio
import aiohttp
import logging
import json
from typing import Any
from pooldose.exceptions import (
    PooldoseFetchError,
    PooldoseTimeoutError,
    PooldoseCacheMissingError
)

_LOGGER = logging.getLogger(__name__)

class RequestHandler:
    def __init__(self, host: str, timeout: int = 10):
        self.host = host
        self.timeout = timeout
        self.last_data = None

    async def get_debug_config(self) -> dict[str, Any]:
        url = f"http://{self.host}/api/v1/debug/config"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as err:
            raise PooldoseFetchError("Failed to fetch debug config") from err

    async def get_info_release(self, sw_version: str) -> dict[str, Any]:
        url = f"http://{self.host}/api/v1/infoRelease"
        payload = {"SOFTWAREVERSION": sw_version}
        headers = {"Content-Type": "application/json"}
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as err:
            raise PooldoseFetchError("Failed to fetch infoRelease") from err

    async def get_wifi_station(self) -> dict[str, Any]:
        url = f"http://{self.host}/api/v1/network/wifi/getStation"
        headers = {"Content-Type": "application/json"}
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
        except Exception as err:
            text = str(err)
            text = text.replace("\\\\n", "").replace("\\\\t", "")
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                data = json.loads(text[json_start:json_end])
        if not data:
            raise PooldoseFetchError("Failed to fetch WiFi station info") from err
        return data

    async def get_access_point(self) -> dict[str, Any]:
        url = f"http://{self.host}/api/v1/network/wifi/getAccessPoint"
        headers = {"Content-Type": "application/json"}
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    text = await resp.text()
                    json_start = text.find("{")
                    json_end = text.rfind("}") + 1
                    if json_start != -1 and json_end != -1:
                        return await resp.json()
                    return {}
        except Exception as err:
            raise PooldoseFetchError("Failed to fetch access point info") from err

    async def get_network_info(self) -> dict[str, Any]:
        url = f"http://{self.host}/api/v1/network/info/getInfo"
        headers = {"Content-Type": "application/json"}
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as err:
            raise PooldoseFetchError("Failed to fetch network info") from err

    async def get_values_raw(self) -> dict:
        url = f"http://{self.host}/api/v1/DWI/getInstantValues"
        try:
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    self.last_data = data
                    return data
        except (asyncio.TimeoutError, aiohttp.ServerDisconnectedError, aiohttp.ClientError) as e:
            _LOGGER.warning(
                "Pooldose API request failed (%s), using last known good data", e
            )
            if self.last_data is not None:
                return self.last_data
            raise PooldoseCacheMissingError("No cached data available from Pooldose") from e
        except Exception as err:
            raise PooldoseFetchError("Failed to fetch instant values") from err

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
                async with session.post(url, json=payload, timeout=timeout_obj) as resp:
                    resp.raise_for_status()
        except aiohttp.ClientError as e:
            _LOGGER.warning("Client error setting pool value: %s", e)
            return False
        except PooldoseTimeoutError:
            _LOGGER.warning("Pooldose server timeout during set_value")
            return False

        return True