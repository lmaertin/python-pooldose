# client.py
"""Async API client for SEKO Pooldose."""

from __future__ import annotations

import asyncio
from typing import Any, Optional
import json
import logging
from pathlib import Path
from pooldose.instant_values import InstantValues
from pooldose.request_handler import RequestHandler
from pooldose.static_values import StaticValues

_LOGGER = logging.getLogger(__name__)

class PooldoseClient:
    """
    Async client for SEKO Pooldose API.
    All getter methods return None on error and log a warning.
    """

    def __init__(self, host: str, timeout: int = 10) -> None:
        """
        Initialize the Pooldose client.

        Args:
            host (str): The host address of the Pooldose device.
            timeout (int): Timeout for API requests in seconds.
        """
        self._host = host
        self._timeout = timeout
        self._last_data = None
        self._request_handler = RequestHandler(host, timeout)

        # Initialize device info with default or placeholder values
        self.device_info = {
            "NAME": None,           # Device name
            "SERIAL_NUMBER": None,  # Serial number
            "DEVICE_ID": "01220000095B_DEVICE",      # Device ID, i.e., SERIAL_NUMBER + "_DEVICE"
            "MODEL": None,          # Device model
            "MODEL_ID": "PDPR1H1HAW100",       # Model ID
            "OWNERID": None,        # Owner ID
            "GROUPNAME": None,      # Group name
            "FW_VERSION": None,     # Firmware version
            "SW_VERSION": None,     # Software version
            "API_VERSION": None,    # API version
            "FW_CODE": "539187",        # Firmware code
            "MAC": None,            # MAC address
            "IP": None,             # IP address
            "WIFI_SSID": None,      # WiFi SSID
            "WIFI_KEY": None,       # WiFi key
            "AP_SSID": None,        # Access Point SSID
            "AP_KEY": None,         # Access Point key
        } 

    @classmethod
    async def create(cls, host: str, timeout: int = 10) -> "PooldoseClient":
        """
        Asynchronous factory method to initialize the Pooldose client.

        This method can be extended to fetch and populate device information
        from the Pooldose API during initialization.

        Args:
            host (str): The host address of the Pooldose device.
            timeout (int): Timeout for API requests in seconds.

        Returns:
            PooldoseClient: An initialized PooldoseClient instance, or None on error.
        """
        try:
            self = cls(host, timeout)

            self._request_handler = await RequestHandler.create(host, timeout)
            if not self._request_handler:
                _LOGGER.error("Failed to create RequestHandler")
                return None
            # Fetch core parameters and device info
            if self._request_handler.check_apiversion_supported():
                self.device_info["API_VERSION"] = self._request_handler.api_version
            if not self.device_info["API_VERSION"]:
                _LOGGER.error("Failed to fetch API version")
                return None
            
            debug_config = await self._request_handler.get_debug_config()
            if not debug_config:
                _LOGGER.error("Failed to fetch debug config")
                return None
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

            wifi_station = await self._request_handler.get_wifi_station()
            if not wifi_station:
                _LOGGER.error("Failed to fetch WiFi station info")
                return None
            self.device_info["WIFI_SSID"] = wifi_station.get("SSID")
            self.device_info["WIFI_KEY"] = wifi_station.get("KEY")
            self.device_info["MAC"] = wifi_station.get("MAC")
            self.device_info["IP"] = wifi_station.get("IP")
            await asyncio.sleep(0.5)

            access_point = await self._request_handler.get_access_point()
            if not access_point:
                _LOGGER.error("Failed to fetch access point info")
                return None
            self.device_info["AP_SSID"] = access_point.get("SSID")
            self.device_info["AP_KEY"] = access_point.get("KEY")
            await asyncio.sleep(0.5)

            network_info = await self._request_handler.get_network_info()
            if not network_info:
                _LOGGER.error("Failed to fetch network info")
                return None
            self.device_info["OWNERID"] = network_info.get("OWNERID")
            self.device_info["GROUPNAME"] = network_info.get("GROUPNAME")
            
            _LOGGER.debug("Initialized Pooldose client with device info: %s", self.device_info)
            return self
        except Exception as err:
            _LOGGER.warning("Error creating PooldoseClient: %s", err)
            return None
    
    def static_values(self) -> Optional[StaticValues]:
        """
        Get the static device values as a StaticValues object.
        Returns None and logs a warning on error.
        """
        try:
            return StaticValues(self.device_info)
        except Exception as err:
            _LOGGER.warning("Error creating StaticValues: %s", err)
            return None

    def _get_model_mapping(self) -> Optional[dict]:
        """
        Load the model-specific mapping configuration from a JSON file.
        Returns None and logs a warning on error.
        """
        try:
            model_id = self.device_info.get("MODEL_ID")
            fw_code = self.device_info.get("FW_CODE")
            if not model_id or not fw_code:
                _LOGGER.error("MODEL_ID or FW_CODE not set!")
                return None
            mapping_path = Path(__file__).parent / "mappings" / f"model_{model_id}_FW{fw_code}.json"
            with open(mapping_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            _LOGGER.warning("Error loading model mapping: %s", err)
            return None

    async def instant_values(self) -> Optional[InstantValues]:
        """
        Fetch the current instant values from the Pooldose device.
        Returns None and logs a warning on error.
        """
        try:
            raw_data = await self._request_handler.get_values_raw()
            if raw_data is None:
                return None
            mapping = self._get_model_mapping()
            if mapping is None:
                return None
            device_id = self.device_info["DEVICE_ID"]
            device_raw_data = raw_data.get("devicedata", {}).get(device_id, {})
            model_id = self.device_info["MODEL_ID"]
            fw_code = self.device_info["FW_CODE"]
            prefix = f"{model_id}_FW{fw_code}_"
            return InstantValues(device_raw_data, mapping, prefix, device_id, self._request_handler)
        except Exception as err:
            _LOGGER.warning("Error creating InstantValues: %s", err)
            return None

