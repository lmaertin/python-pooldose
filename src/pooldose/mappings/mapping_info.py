"""Mapping Parser for async API client for SEKO Pooldose."""

import functools
import importlib.resources
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiofiles

from pooldose.request_handler import RequestStatus
from pooldose.type_definitions import (
    VALUE_TYPE_SENSOR,
    VALUE_TYPE_BINARY_SENSOR,
    VALUE_TYPE_NUMBER,
    VALUE_TYPE_SWITCH,
    VALUE_TYPE_SELECT,
)

# pylint: disable=line-too-long

_LOGGER = logging.getLogger(__name__)


@functools.cache
def _has_dedicated_mapping_file(model_id: str, fw_code: str) -> bool:
    """
    Check whether a dedicated mapping file exists for this model/firmware.

    Cached per (model_id, fw_code) pair, so this only hits the filesystem
    once for each combination actually queried (in practice at most the
    number of entries in MODEL_ALIASES, since this is only called for
    aliased models - see MappingInfo.load).
    """
    filename = f"model_{model_id}_FW{fw_code}.json"
    return importlib.resources.files("pooldose.mappings").joinpath(filename).is_file()


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
    async def load(
        cls,
        model_id: str,
        fw_code: str,
        fallback_model_id: Optional[str] = None,
    ) -> "MappingInfo":
        """
        Asynchronously load the model-specific mapping configuration from a JSON file.

        Uses ``model_id`` if a dedicated mapping file exists for it. Otherwise,
        if ``fallback_model_id`` (e.g. from MODEL_ALIASES) is given, uses that
        model's mapping file instead. Which model has its own dedicated file is
        determined by checking for the file's actual existence in the mappings
        package (see ``_has_dedicated_mapping_file``), not from a hand-maintained
        list, and is cached per (model_id, fw_code) pair so repeated calls for
        the same model don't repeatedly hit the filesystem.

        Args:
            model_id (str): The model ID as reported by the device.
            fw_code (str): The firmware code.
            fallback_model_id (Optional[str]): Alias model ID to use if no
                dedicated mapping file exists for ``model_id``.

        Returns:
            MappingInfo: The loaded mapping info object.
        """
        if not model_id or not fw_code:
            _LOGGER.error("MODEL_ID or FW_CODE not set!")
            return cls(mapping=None, status=RequestStatus.NO_DATA)

        resolved_model_id = model_id
        if fallback_model_id and not _has_dedicated_mapping_file(model_id, fw_code):
            resolved_model_id = fallback_model_id

        filename = f"model_{resolved_model_id}_FW{fw_code}.json"
        path = importlib.resources.files("pooldose.mappings").joinpath(filename)
        try:
            async with aiofiles.open(str(path), "r", encoding="utf-8") as f:
                content = await f.read()
                mapping = json.loads(content)
                return cls(mapping=mapping, status=RequestStatus.SUCCESS)
        except FileNotFoundError:
            _LOGGER.warning(
                "No mapping data was found for model %s (firmware %s). "
                "Please check the supported devices documentation or request a mapping for your device.",
                model_id,
                fw_code,
            )
            return cls(mapping=None, status=RequestStatus.MAPPING_NOT_FOUND)
        except (OSError, json.JSONDecodeError, ModuleNotFoundError) as err:
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
        result: Dict[str, List[str]] = {}
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
            if entry.get("type") == VALUE_TYPE_SENSOR:
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
            if entry.get("type") == VALUE_TYPE_BINARY_SENSOR:
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
            if entry.get("type") == VALUE_TYPE_NUMBER:
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
            if entry.get("type") == VALUE_TYPE_SWITCH:
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
            if entry.get("type") == VALUE_TYPE_SELECT:
                result[name] = SelectMapping(
                    key=entry["key"],
                    type=entry["type"],
                    conversion=entry["conversion"],
                    options=entry["options"],
                )
        return result
