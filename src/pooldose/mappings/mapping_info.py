"""Mapping Parser for async API client for SEKO Pooldose."""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import importlib.resources
import json
import logging
import aiofiles
from pooldose.request_handler import RequestStatus

# pylint: disable=line-too-long

_LOGGER = logging.getLogger(__name__)

@dataclass
class SensorMapping:
    """
    Represents a sensor mapping entry.
    Attributes:
        key (str): The key for the sensor.
        type (str): The type, always "sensor".
        conversion (Optional[dict]): Optional conversion mapping.
    """
    key: str
    type: str
    conversion: Optional[dict] = None

@dataclass
class BinarySensorMapping:
    """
    Represents a binary sensor mapping entry.
    Attributes:
        key (str): The key for the binary sensor.
        type (str): The type, always "binary_sensor".
    """
    key: str
    type: str

@dataclass
class NumberMapping:
    """
    Represents a number mapping entry.
    Attributes:
        key (str): The key for the number.
        type (str): The type, always "number".
    """
    key: str
    type: str

@dataclass
class SwitchMapping:
    """
    Represents a switch mapping entry.
    Attributes:
        key (str): The key for the switch.
        type (str): The type, always "switch".
    """
    key: str
    type: str

@dataclass
class SelectMapping:
    """
    Represents a select mapping entry.
    Attributes:
        key (str): The key for the select.
        type (str): The type, always "select".
        conversion (dict): Mandatory conversion mapping.
        options (dict): Mandatory options mapping.
    """
    key: str
    type: str
    conversion: dict
    options: dict

@dataclass
class MappingInfo:
    """
    Provides utilities to load and query mapping configurations for different models and firmware codes.

    Attributes:
        mapping (Optional[Dict[str, Any]]): The loaded mapping configuration, or None if not loaded.
        status (Optional[RequestStatus]): The status of the mapping load operation.
    """
    mapping: Optional[Dict[str, Any]] = None
    status: Optional[RequestStatus] = None

    @classmethod
    async def load(cls, model_id: str, fw_code: str) -> "MappingInfo":
        """
        Asynchronously load the model-specific mapping configuration from a JSON file.

        Args:
            model_id (str): The model ID.
            fw_code (str): The firmware code.

        Returns:
            MappingInfo: The loaded mapping info object.
        """
        try:
            if not model_id or not fw_code:
                _LOGGER.error("MODEL_ID or FW_CODE not set!")
                return cls(mapping=None, status=RequestStatus.NO_DATA)
            filename = f"model_{model_id}_FW{fw_code}.json"
            path = importlib.resources.files("pooldose.mappings").joinpath(filename)
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
                mapping = json.loads(content)
                return cls(mapping=mapping, status=RequestStatus.SUCCESS)
        except (OSError, json.JSONDecodeError, ModuleNotFoundError, FileNotFoundError) as err:
            _LOGGER.warning("Error loading model mapping: %s", err)
            return cls(mapping=None, status=RequestStatus.UNKNOWN_ERROR)

    def available_types(self) -> dict[str, list[str]]:
        """
        Returns all available types and their keys for the current model/firmware.

        Returns:
            dict[str, list[str]]: Mapping from type to list of keys.
        """
        if not self.mapping:
            return {}
        result = {}
        for key, entry in self.mapping.items():
            typ = entry.get("type", "unknown")
            result.setdefault(typ, []).append(key)
        return result

    def available_sensors(self) -> Dict[str, SensorMapping]:
        """
        Returns all available sensors from the mapping as SensorMapping objects.

        Returns:
            Dict[str, SensorMapping]: Mapping from name to SensorMapping.
        """
        if not self.mapping:
            return {}
        result = {}
        for name, entry in self.mapping.items():
            if entry.get("type") == "sensor":
                result[name] = SensorMapping(
                    key=entry["key"],
                    type=entry["type"],
                    conversion=entry.get("conversion"),
                )
        return result

    def available_binary_sensors(self) -> Dict[str, BinarySensorMapping]:
        """
        Returns all available binary sensors from the mapping as BinarySensorMapping objects.

        Returns:
            Dict[str, BinarySensorMapping]: Mapping from name to BinarySensorMapping.
        """
        if not self.mapping:
            return {}
        result = {}
        for name, entry in self.mapping.items():
            if entry.get("type") == "binary_sensor":
                result[name] = BinarySensorMapping(
                    key=entry["key"],
                    type=entry["type"],
                )
        return result

    def available_numbers(self) -> Dict[str, NumberMapping]:
        """
        Returns all available numbers from the mapping as NumberMapping objects.

        Returns:
            Dict[str, NumberMapping]: Mapping from name to NumberMapping.
        """
        if not self.mapping:
            return {}
        result = {}
        for name, entry in self.mapping.items():
            if entry.get("type") == "number":
                result[name] = NumberMapping(
                    key=entry["key"],
                    type=entry["type"],
                )
        return result

    def available_switches(self) -> Dict[str, SwitchMapping]:
        """
        Returns all available switches from the mapping as SwitchMapping objects.

        Returns:
            Dict[str, SwitchMapping]: Mapping from name to SwitchMapping.
        """
        if not self.mapping:
            return {}
        result = {}
        for name, entry in self.mapping.items():
            if entry.get("type") == "switch":
                result[name] = SwitchMapping(
                    key=entry["key"],
                    type=entry["type"],
                )
        return result

    def available_selects(self) -> Dict[str, SelectMapping]:
        """
        Returns all available selects from the mapping as SelectMapping objects.

        Returns:
            Dict[str, SelectMapping]: Mapping from name to SelectMapping.
        Raises:
            KeyError: If a select entry does not contain 'conversion' or 'options'.
        """
        if not self.mapping:
            return {}
        result = {}
        for name, entry in self.mapping.items():
            if entry.get("type") == "select":
                result[name] = SelectMapping(
                    key=entry["key"],
                    type=entry["type"],
                    conversion=entry["conversion"],
                    options=entry["options"],
                )
        return result
