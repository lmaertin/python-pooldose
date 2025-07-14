"""Instant values for Async API client for SEKO Pooldose."""

import logging
from typing import Any, Dict
from pooldose.request_handler import RequestHandler

# pylint: disable=line-too-long,too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-return-statements,too-many-branches,no-else-return,too-many-public-methods

_LOGGER = logging.getLogger(__name__)

class InstantValues:
    """
    Provides dict-like access to instant values from the Pooldose device.
    Values are dynamically loaded based on the mapping configuration.
    """

    def __init__(self, device_data: Dict[str, Any], mapping: Dict[str, Any], prefix: str, device_id: str, request_handler: RequestHandler):
        """
        Initialize InstantValues.

        Args:
            device_data (Dict[str, Any]): Raw device data.
            mapping (Dict[str, Any]): Mapping configuration.
            prefix (str): Key prefix.
            device_id (str): Device ID.
            request_handler (RequestHandler): API request handler.
        """
        self._device_data = device_data
        self._mapping = mapping
        self._prefix = prefix
        self._device_id = device_id
        self._request_handler = request_handler
        self._cache: Dict[str, Any] = {}

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like read access to instant values."""
        if key in self._cache:
            return self._cache[key]
        value = self._get_value(key)
        self._cache[key] = value
        return value

    async def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like async write access to instant values."""
        await self._set_value(key, value)

    def __contains__(self, key: str) -> bool:
        """Allow 'in' checks for available instant values."""
        return key in self._mapping

    def get(self, key: str, default=None):
        """Get value with default fallback."""
        try:
            return self[key]
        except KeyError:
            return default

    def available_types(self) -> Dict[str, list[str]]:
        """
        Get all available types and their keys.
        
        Returns:
            Dict[str, list[str]]: Mapping from type to list of available keys.
        """
        result = {}
        for key, entry in self._mapping.items():
            typ = entry.get("type", "unknown")
            result.setdefault(typ, []).append(key)
        return result

    def get_sensors(self) -> Dict[str, Any]:
        """Get all sensor values."""
        return {key: self[key] for key in self._mapping if self._mapping[key].get("type") == "sensor"}

    def get_binary_sensors(self) -> Dict[str, Any]:
        """Get all binary sensor values."""
        return {key: self[key] for key in self._mapping if self._mapping[key].get("type") == "binary_sensor"}

    def get_numbers(self) -> Dict[str, Any]:
        """Get all number values."""
        return {key: self[key] for key in self._mapping if self._mapping[key].get("type") == "number"}

    def get_switches(self) -> Dict[str, Any]:
        """Get all switch values."""
        return {key: self[key] for key in self._mapping if self._mapping[key].get("type") == "switch"}

    def get_selects(self) -> Dict[str, Any]:
        """Get all select values."""
        return {key: self[key] for key in self._mapping if self._mapping[key].get("type") == "select"}

    async def set_number(self, key: str, value: Any) -> bool:
        """Set number value with validation."""
        if key not in self._mapping or self._mapping[key].get("type") != "number":
            _LOGGER.warning("Key '%s' is not a valid number", key)
            return False

        # Get current number info for validation
        current_info = self[key]
        if current_info is None:
            _LOGGER.warning("Cannot get current info for number '%s'", key)
            return False

        try:
            _, _, min_val, max_val, step = current_info

            # Validate range
            if not min_val <= value <= max_val:
                _LOGGER.warning("Value %s is out of range for %s. Valid range: %s - %s", value, key, min_val, max_val)
                return False

            # Validate step (for float values)
            if isinstance(value, float) and step:
                epsilon = 1e-9
                n = (value - min_val) / step
                if abs(round(n) - n) > epsilon:
                    _LOGGER.warning("Value %s is not a valid step for %s. Step: %s", value, key, step)
                    return False

            return await self._set_value(key, value)
        except (TypeError, ValueError, IndexError) as err:
            _LOGGER.warning("Error validating number '%s': %s", key, err)
            return False

    async def set_switch(self, key: str, value: bool) -> bool:
        """Set switch value."""
        if key not in self._mapping or self._mapping[key].get("type") != "switch":
            _LOGGER.warning("Key '%s' is not a valid switch", key)
            return False
        return await self._set_value(key, value)

    async def set_select(self, key: str, value: Any) -> bool:
        """Set select value with validation."""
        if key not in self._mapping or self._mapping[key].get("type") != "select":
            _LOGGER.warning("Key '%s' is not a valid select", key)
            return False

        # Validate against available options
        mapping_entry = self._mapping[key]
        options = mapping_entry.get("options", {})
        if str(value) not in options:
            _LOGGER.warning("Value '%s' is not a valid option for %s. Valid options: %s", value, key, list(options.keys()))
            return False

        return await self._set_value(key, value)

    def _get_value(self, name: str) -> Any:
        """
        Internal helper to retrieve a value from the device data using the mapping.
        Returns None and logs a warning on error.
        """
        try:
            attributes = self._mapping.get(name)
            if not attributes:
                _LOGGER.warning("Key '%s' not found in mapping", name)
                return None

            key = attributes.get("key", name)
            full_key = f"{self._prefix}{key}"
            entry = self._device_data.get(full_key)
            if entry is None:
                _LOGGER.warning("No data found for key '%s'", full_key)
                return None

            entry_type = attributes.get("type")
            if not entry_type:
                _LOGGER.warning("No type found for key '%s'", name)
                return None

            # Sensor: return tuple (value, unit)
            if entry_type == "sensor":
                value = entry.get("current") if isinstance(entry, dict) else None
                if "conversion" in attributes:
                    conversion = attributes["conversion"]
                    if value in conversion:
                        value = conversion[value]
                units = entry.get("magnitude", [""])
                unit = units[0] if units[0] != "UNDEFINED" else None
                return (value, unit)

            # Binary sensor: return bool
            if entry_type == "binary_sensor":
                value = entry.get("current")
                if value is None:
                    return None
                return value == "F"  # F = True, O = False

            # Switch: return bool
            if entry_type == "switch":
                if isinstance(entry, bool):
                    return entry
                return None

            # Number: return tuple (value, unit, min, max, step)
            if entry_type == "number":
                value = entry.get("current") if isinstance(entry, dict) else None
                abs_min = entry.get("absMin")
                abs_max = entry.get("absMax")
                resolution = entry.get("resolution")
                units = entry.get("magnitude", [""])
                unit = units[0] if units[0] != "UNDEFINED" else None
                return (value, unit, abs_min, abs_max, resolution)

            # Select: return converted value or raw value
            if entry_type == "select":
                value = entry.get("current") if isinstance(entry, dict) else None
                options = attributes.get("options", {})

                if value in options:
                    value_text = options.get(value)
                    if "conversion" in attributes:
                        conversion = attributes["conversion"]
                        if value_text in conversion:
                            return conversion[value_text]
                    return value_text
                return value

            _LOGGER.warning("Unknown type '%s' for key '%s'", entry_type, name)
            return None

        except (KeyError, TypeError, AttributeError) as err:
            _LOGGER.warning("Error getting value '%s': %s", name, err)
            return None

    async def _set_value(self, name: str, value: Any) -> bool:
        """
        Internal helper to set a value on the device using the request handler.
        Returns False and logs a warning on error.
        """
        try:
            attributes = self._mapping.get(name)
            if not attributes:
                _LOGGER.warning("Key '%s' not found in mapping", name)
                return False

            entry_type = attributes.get("type")
            key = attributes.get("key", name)
            full_key = f"{self._prefix}{key}"

            # Handle different types
            if entry_type == "number":
                if not isinstance(value, (int, float)):
                    _LOGGER.warning("Invalid type for number '%s': expected int/float, got %s", name, type(value))
                    return False
                result = await self._request_handler.set_value(self._device_id, full_key, value, "NUMBER")

            elif entry_type == "switch":
                if not isinstance(value, bool):
                    _LOGGER.warning("Invalid type for switch '%s': expected bool, got %s", name, type(value))
                    return False
                value_str = "O" if value else "F"  # O = True, F = False
                result = await self._request_handler.set_value(self._device_id, full_key, value_str, "STRING")

            elif entry_type == "select":
                result = await self._request_handler.set_value(self._device_id, full_key, value, "NUMBER")

            else:
                _LOGGER.warning("Unsupported type '%s' for setting value '%s'", entry_type, name)
                return False

            if result:
                # Update cache on success
                self._cache[name] = value
                return True
            else:
                _LOGGER.warning("Failed to set value '%s'", name)
                return False

        except (KeyError, TypeError, AttributeError, ValueError) as err:
            _LOGGER.warning("Error setting value '%s': %s", name, err)
            return False
