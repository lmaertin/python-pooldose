"""Mock client for SEKO Pooldose that uses JSON files instead of real devices."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from pooldose.constants import get_default_device_info
from pooldose.mappings.mapping_info import MappingInfo
from pooldose.request_status import RequestStatus
from pooldose.values.instant_values import InstantValues
from pooldose.values.static_values import StaticValues

_LOGGER = logging.getLogger(__name__)

API_VERSION_SUPPORTED = "v1/"


class MockPooldoseClient:
    """
    Mock client for SEKO Pooldose API that uses JSON files as data source.
    Perfect for testing and development without real hardware.
    """

    def __init__(
        self,
        json_file_path: Union[str, Path],
        *,
        timeout: int = 30,
        include_sensitive_data: bool = False
    ) -> None:
        """
        Initialize the Mock Pooldose client.

        Args:
            json_file_path: Path to JSON file containing device data
            timeout: Timeout for operations (ignored in mock, for compatibility)
            include_sensitive_data: If True, include sensitive data in responses
        """
        self.json_file_path = Path(json_file_path)
        self._timeout = timeout
        self._include_sensitive_data = include_sensitive_data
        self._mock_data = None
        self._device_key = None
        self._mapping_info = None

        # Initialize device info with default values
        self.device_info = get_default_device_info()

        # Load data immediately
        self._load_json_data()

    def _load_json_data(self) -> None:
        """Load and parse the JSON data file."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                self._mock_data = json.load(file)

            # Extract device key and device info
            if self._mock_data and 'devicedata' in self._mock_data:
                device_keys = [k for k in self._mock_data['devicedata'].keys()
                              if k.endswith('_DEVICE')]
                if device_keys:
                    self._device_key = device_keys[0]
                    self._extract_device_info()
                else:
                    raise ValueError("No device key found in JSON data")
            else:
                raise ValueError("No 'devicedata' key found in JSON file")

        except FileNotFoundError:
            _LOGGER.error("JSON file not found: %s", self.json_file_path)
            raise
        except json.JSONDecodeError as e:
            _LOGGER.error("Invalid JSON in file %s: %s", self.json_file_path, e)
            raise
        except Exception as e:
            _LOGGER.error("Error loading JSON data: %s", e)
            raise

    def _extract_device_info(self) -> None:
        """Extract device information from the loaded data."""
        if not self._device_key:
            return

        # Extract serial number from device key (remove _DEVICE suffix)
        serial_number = self._device_key.replace('_DEVICE', '')

        # Try to determine model and firmware from data keys
        device_data = self._mock_data['devicedata'][self._device_key]
        model = None
        fw_code = None

        # Look for model/firmware pattern in keys
        for key in device_data.keys():
            if key.startswith('PDPR1H1'):
                parts = key.split('_')
                if len(parts) >= 3:
                    model = parts[0]
                    fw_code = parts[1]
                    break

        # Update device info
        self.device_info.update({
            "NAME": f"Mock {model or 'POOLDOSE'} Device",
            "SERIAL_NUMBER": serial_number,
            "DEVICE_ID": self._device_key,
            "MODEL": model or "MOCK_MODEL",
            "MODEL_ID": model or "MOCK_MODEL",
            "FW_CODE": (
                fw_code.replace('FW', '')
                if fw_code and fw_code.startswith('FW')
                else fw_code or "MOCK_FW"
            ),
            "API_VERSION": API_VERSION_SUPPORTED,
            "IP": "127.0.0.1",  # Mock IP
        })

        if self._include_sensitive_data:
            self.device_info.update({
                "WIFI_SSID": "MockWiFi",
                "WIFI_KEY": "mock_wifi_key",
                "AP_SSID": "MockAP",
                "AP_KEY": "mock_ap_key"
            })

    async def connect(self) -> RequestStatus:
        """
        Mock connection - always succeeds if data is loaded.

        Returns:
            RequestStatus: SUCCESS if mock data is available
        """
        if self._mock_data and self._device_key:
            # Load mapping info
            try:
                self._mapping_info = await MappingInfo.load(
                    self.device_info["MODEL_ID"],
                    self.device_info["FW_CODE"]
                )
                _LOGGER.info("Mock client connected successfully")
                return RequestStatus.SUCCESS
            except (ImportError, ValueError, FileNotFoundError) as e:
                _LOGGER.error("Failed to load mapping info: %s", e)
                return RequestStatus.PARAMS_FETCH_FAILED
        else:
            _LOGGER.error("Mock data not available")
            return RequestStatus.HOST_UNREACHABLE

    def static_values(self) -> Tuple[RequestStatus, Optional[StaticValues]]:
        """
        Get static device values from mock data.

        Returns:
            Tuple of (RequestStatus, StaticValues or None)
        """
        try:
            if not self._mock_data:
                return RequestStatus.UNKNOWN_ERROR, None

            static_values = StaticValues(self.device_info)
            return RequestStatus.SUCCESS, static_values

        except (ValueError, TypeError, KeyError) as e:
            _LOGGER.error("Error creating static values: %s", e)
            return RequestStatus.UNKNOWN_ERROR, None

    async def instant_values(self) -> Tuple[RequestStatus, Optional[InstantValues]]:
        """
        Get instant values from mock data.

        Returns:
            Tuple of (RequestStatus, InstantValues or None)
        """
        try:
            if not self._mock_data or not self._device_key or not self._mapping_info:
                return RequestStatus.UNKNOWN_ERROR, None

            device_data = self._mock_data['devicedata'][self._device_key]

            # Filter out non-sensor data
            filtered_data = {
                k: v for k, v in device_data.items()
                if k.startswith(self.device_info["MODEL_ID"]) and isinstance(v, dict)
            }

            instant_values = InstantValues(
                device_data=filtered_data,
                mapping=self._mapping_info.mapping,
                prefix=f"{self.device_info['MODEL_ID']}_FW{self.device_info['FW_CODE']}_",
                device_id=self._device_key,
                request_handler=None  # No real request handler in mock
            )

            return RequestStatus.SUCCESS, instant_values

        except (ValueError, TypeError, KeyError) as e:
            _LOGGER.error("Error creating instant values: %s", e)
            return RequestStatus.UNKNOWN_ERROR, None

    async def instant_values_structured(self) -> Tuple[RequestStatus, Dict[str, Any]]:
        """
        Get structured instant values from mock data.

        Returns:
            Tuple of (RequestStatus, structured data dict)
        """
        try:
            status, instant_values = await self.instant_values()
            if status != RequestStatus.SUCCESS or not instant_values:
                return status, {}

            structured_data = instant_values.to_structured_dict()
            return RequestStatus.SUCCESS, structured_data

        except (ValueError, TypeError, AttributeError) as e:
            _LOGGER.error("Error creating structured instant values: %s", e)
            return RequestStatus.UNKNOWN_ERROR, {}

    @property
    def is_connected(self) -> bool:
        """Check if mock client is 'connected' (has valid data)."""
        return self._mock_data is not None and self._device_key is not None

    def reload_data(self) -> bool:
        """
        Reload data from JSON file.

        Returns:
            bool: True if reload was successful
        """
        try:
            self._load_json_data()
            return True
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            _LOGGER.error("Failed to reload JSON data: %s", e)
            return False

    def get_raw_data(self) -> Optional[Dict[str, Any]]:
        """
        Get the raw loaded JSON data.

        Returns:
            The complete loaded JSON data or None
        """
        return self._mock_data

    def get_device_data(self) -> Optional[Dict[str, Any]]:
        """
        Get only the device-specific data.

        Returns:
            Device data dictionary or None
        """
        if self._mock_data and self._device_key:
            return self._mock_data['devicedata'][self._device_key]
        return None
