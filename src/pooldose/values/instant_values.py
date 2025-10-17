"""Instant values for Async API client for SEKO Pooldose."""

import logging
from typing import Any, Dict, Tuple, Union


# pylint: disable=line-too-long,too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-return-statements,too-many-branches,no-else-return,too-many-public-methods

_LOGGER = logging.getLogger(__name__)

class InstantValues:
    """Manage instant device values and provide typed setters.

    This class wraps raw device data and a mapping configuration to expose
    typed accessors (sensor, number, switch, select) and to send updates
    back to the device using a RequestHandler.
    """

    def __init__(
        self,
        device_data: Dict[str, Any],
        mapping: Dict[str, Any],
        prefix: str,
        device_id: str,
        request_handler: Any,
    ) -> None:
        """Initialize InstantValues.

        Args:
            device_data: Raw device data from API.
            mapping: Mapping configuration.
            prefix: Key prefix for device data lookup.
            device_id: Device ID.
            request_handler: API request handler (or mock shim).
        """
        self._device_data = device_data
        self._mapping = mapping
        self._prefix = prefix
        self._device_id = device_id
        self._request_handler: Any = request_handler
        self._cache: Dict[str, Any] = {}

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like read access to instant values."""
        if key in self._cache:
            return self._cache[key]
        value = self._get_value(key)
        if value is not None:
            self._cache[key] = value
        return value

    async def __setitem__(self, key: str, value: Any) -> None:
        """
        Disallow direct setting via __setitem__ to enforce type-specific methods.
        Use set_number, set_switch, or set_select instead.
        """
        raise NotImplementedError("Use set_number, set_switch, or set_select for setting values.")

    def __contains__(self, key: str) -> bool:
        """Allow 'in' checks for available instant values."""
        return key in self._mapping and self._find_device_entry(key) is not None

    def get(self, key: str, default=None):
        """Get value with default fallback."""
        try:
            value = self[key]
            return value if value is not None else default
        except KeyError:
            return default

    def to_structured_dict(self) -> Dict[str, Any]:
        """
        Convert instant values to structured dictionary format with types as top-level keys.

        Returns:
            Dict[str, Any]: Structured data with format:
                    "temperature": {"value": 25.5, "unit": "°C"},
                    "ph": {"value": 7.2, "unit": None}
                },
                "number": {
                    "target_ph": {"value": 7.0, "unit": None, "min": 6.0, "max": 8.0, "step": 0.1}
                },
                "switch": {
                    "stop_dosing": {"value": False}
                },
                "binary_sensor": {
                    "alarm_ph": {"value": False}
                },
                "select": {
                    "water_meter_unit": {"value": "L/h"}
                }
            }
        """
        structured_data: Dict[str, Dict[str, Any]] = {}

        # Process each mapping entry
        for mapping_key, mapping_entry in self._mapping.items():
            entry_type = mapping_entry.get("type")
            if not entry_type:
                continue

            # Skip if no data available for this key
            raw_entry = self._find_device_entry(mapping_key)
            if raw_entry is None:
                continue

            # Initialize type section if needed
            if entry_type not in structured_data:
                structured_data[entry_type] = {}

            # Get the processed value using existing logic
            try:
                value_data = self._get_value(mapping_key)
                if value_data is None:
                    continue

                # Structure the data based on type
                if entry_type == "sensor":
                    if isinstance(value_data, tuple) and len(value_data) >= 2:
                        structured_data[entry_type][mapping_key] = {
                            "value": value_data[0],
                            "unit": value_data[1]
                        }

                elif entry_type in ("binary_sensor", "switch"):
                    structured_data[entry_type][mapping_key] = {
                        "value": value_data
                    }

                elif entry_type == "number":
                    if isinstance(value_data, tuple) and len(value_data) >= 5:
                        structured_data[entry_type][mapping_key] = {
                            "value": value_data[0],
                            "unit": value_data[1],
                            "min": value_data[2],
                            "max": value_data[3],
                            "step": value_data[4]
                        }

                elif entry_type == "select":
                    structured_data[entry_type][mapping_key] = {
                        "value": value_data
                    }

            except (KeyError, TypeError, AttributeError) as err:
                _LOGGER.warning("Error processing %s for structured data: %s", mapping_key, err)
                continue

        return structured_data

    def _find_device_entry(self, name: str) -> Union[Dict[str, Any], None]:
        """
        Find the raw device entry for a given mapped name.

        Args:
            name (str): The mapped name (e.g., "temperature", "ph")

        Returns:
            Union[Dict[str, Any], None]: The raw device entry or None if not found
        """
        attributes = self._mapping.get(name)
        if not attributes:
            return None

        # Get raw device key
        device_key = attributes.get("key", name)
        full_device_key = f"{self._prefix}{device_key}"

        # Get the raw device entry
        return self._device_data.get(full_device_key)

    def _get_value(self, name: str) -> Any:
        """
        Internal helper to retrieve a value from the raw device data.
        Returns None and logs a warning on error.
        """
        try:
            # Get mapping attributes
            attributes = self._mapping.get(name)
            if not attributes:
                _LOGGER.warning("Key '%s' not found in mapping", name)
                return None

            # Get raw device entry
            raw_entry = self._find_device_entry(name)
            if raw_entry is None:
                _LOGGER.debug("No data found for key '%s'", name)
                return None

            # Get entry type
            entry_type = attributes.get("type")
            if not entry_type:
                _LOGGER.warning("No type found for key '%s'", name)
                return None

            # Process based on entry type
            if entry_type == "sensor":
                return self._process_sensor_value(raw_entry, attributes, name)
            elif entry_type == "binary_sensor":
                return self._process_binary_sensor_value(raw_entry, attributes, name)
            elif entry_type == "switch":
                return self._process_switch_value(raw_entry, name)
            elif entry_type == "number":
                return self._process_number_value(raw_entry, name)
            elif entry_type == "select":
                return self._process_select_value(raw_entry, attributes)
            else:
                _LOGGER.warning("Unknown type '%s' for key '%s'", entry_type, name)
                return None

        except (KeyError, TypeError, AttributeError) as err:
            _LOGGER.warning("Error getting value '%s': %s", name, err)
            return None

    def _process_sensor_value(self, raw_entry: Dict[str, Any], attributes: Dict[str, Any], name: str) -> Tuple[Any, Union[str, None]]:
        """Process sensor value and return (value, unit) tuple."""
        if not isinstance(raw_entry, dict):
            _LOGGER.warning("Invalid raw entry type for sensor '%s': expected dict, got %s", name, type(raw_entry))
            return (None, None)

        value = raw_entry.get("current")

        # Apply string-to-string conversion if specified
        if value is not None and "conversion" in attributes:
            conversion = attributes["conversion"]
            if isinstance(conversion, dict) and str(value) in conversion:
                value = conversion[str(value)]

        # Get unit
        units = raw_entry.get("magnitude", [""])
        unit = units[0] if units and units[0].lower() not in ("undefined", "ph") else None

        return (value, unit)

    def _process_binary_sensor_value(self, raw_entry: Dict[str, Any], attributes: Dict[str, Any], name: str) -> Union[bool, None]:
        """Process binary sensor value and return bool, with optional conversion mapping."""
        if not isinstance(raw_entry, dict):
            _LOGGER.warning("Invalid raw entry type for binary sensor '%s': expected dict, got %s", name, type(raw_entry))
            return None

        value = raw_entry.get("current")

        # Apply conversion mapping if defined in mapping
        if value is not None and "conversion" in attributes:
            conversion = attributes["conversion"]
            if isinstance(conversion, dict) and str(value) in conversion:
                value = conversion[str(value)]

        # Convert string values to boolean
        if isinstance(value, str):
            return value.upper() == "O"  # O = True, F = False

        return bool(value)

    def _process_switch_value(self, raw_entry: Dict[str, Any], name: str) -> Union[bool, None]:
        """Process switch value and return bool."""
        # Handle direct boolean values
        if isinstance(raw_entry, bool):
            return raw_entry

        if not isinstance(raw_entry, dict):
            _LOGGER.warning("Invalid raw entry type for switch '%s': expected dict or bool, got %s", name, type(raw_entry))
            return None

        value = raw_entry.get("current")
        if value is None:
            return None

        # Convert string values to boolean
        if isinstance(value, str):
            return value.upper() == "O"  # O = True, F = False

        return bool(value)

    def _process_number_value(self, raw_entry: Dict[str, Any], name: str) -> Tuple[Any, Union[str, None], Any, Any, Any]:
        """Process number value and return (value, unit, min, max, step) tuple.
        If the mapping for this number type contains an 'attribute', use that as the value key instead of 'current'.
        """
        if not isinstance(raw_entry, dict):
            _LOGGER.warning("Invalid raw entry type for number '%s': expected dict, got %s", name, type(raw_entry))
            return (None, None, None, None, None)
        # Check for special field in mapping
        attributes = self._mapping.get(name, {})
        value_key = attributes.get("field", "current")
        value = raw_entry.get(value_key)
        abs_min = raw_entry.get("absMin")
        abs_max = raw_entry.get("absMax")
        resolution = raw_entry.get("resolution")

        # Special handling for minT/maxT fields: split abs_min/abs_max range
        if value_key == "minT" and isinstance(abs_max, (int, float)):
            abs_max = abs_max / 2
        elif value_key == "maxT" and isinstance(abs_max, (int, float)) and isinstance(resolution, (int, float)):
            abs_min = abs_max / 2 + resolution

        # Get unit
        units = raw_entry.get("magnitude", [""])
        unit = units[0] if isinstance(units, (list, tuple)) and units and str(units[0]).lower() not in ("undefined", "ph") else None

        return (value, unit, abs_min, abs_max, resolution)

    def _process_select_value(self, raw_entry: Dict[str, Any], attributes: Dict[str, Any]) -> Any:
        """Process select value and return converted value."""
        if not isinstance(raw_entry, dict):
            return None

        value = raw_entry.get("current")
        options = attributes.get("options", {})

        # First, convert using options mapping (if available)
        if str(value) in options:
            value_text = options.get(str(value))

            # Then apply conversion mapping if available
            if "conversion" in attributes:
                conversion = attributes["conversion"]
                if isinstance(conversion, dict) and value_text in conversion:
                    return conversion[value_text]

            return value_text

        # If no options mapping, try direct conversion
        elif "conversion" in attributes:
            conversion = attributes["conversion"]
            if isinstance(conversion, dict) and str(value) in conversion:
                return conversion[str(value)]

        return value

    async def set_number(self, key: str, value: Any) -> bool:
        """Set number value with validation and device update."""
        if key not in self._mapping or self._mapping[key].get("type") != "number":
            _LOGGER.warning("Key '%s' is not a valid number", key)
            return False

        current_info = self[key]
        if current_info is None:
            _LOGGER.warning("Cannot get current info for number '%s'", key)
            return False

        try:
            _, _, min_val, max_val, step = current_info
            if min_val is not None and max_val is not None:
                if not min_val <= value <= max_val:
                    _LOGGER.warning("Value %s is out of range for %s. Valid range: %s - %s", value, key, min_val, max_val)
                    return False
            if isinstance(value, float) and step and min_val is not None:
                epsilon = 1e-9
                n = (value - min_val) / step
                if abs(round(n) - n) > epsilon:
                    _LOGGER.warning("Value %s is not a valid step for %s. Step: %s", value, key, step)
                    return False

            attributes = self._mapping.get(key, {})
            key_device = attributes.get("key", key)
            full_key = f"{self._prefix}{key_device}"
            field = attributes.get("field")
            if field in ("minT", "maxT"):
                # Safe call with Dict[str, Any] guaranteed
                corresponding = self._get_corresponding_value(key, field, attributes)
                min_val_set, max_val_set = (value, corresponding) if field == "minT" else (corresponding, value)
                if min_val_set is None or max_val_set is None:
                    _LOGGER.warning("Cannot set both minT and maxT: missing value for one corresponding field.")
                    return False
                result = await self._request_handler.set_value(self._device_id, full_key, [min_val_set, max_val_set], "NUMBER")
            else:
                if not isinstance(value, (int, float)):
                    _LOGGER.warning("Invalid type for number '%s': expected int/float, got %s", key, type(value))
                    return False
                result = await self._request_handler.set_value(self._device_id, full_key, value, "NUMBER")
            if result:
                self._cache.pop(key, None)
            return result
        except (TypeError, ValueError, IndexError, KeyError, AttributeError) as err:
            _LOGGER.warning("Error setting number '%s': %s", key, err)
            return False

    async def set_switch(self, key: str, value: bool) -> bool:
        """Set switch value with validation and device update."""
        if key not in self._mapping or self._mapping[key].get("type") != "switch":
            _LOGGER.warning("Key '%s' is not a valid switch", key)
            return False
        try:
            attributes = self._mapping.get(key, {})  # Use empty dict as default to avoid None
            key_device = attributes.get("key", key)
            full_key = f"{self._prefix}{key_device}"
            if not isinstance(value, bool):
                _LOGGER.warning("Invalid type for switch '%s': expected bool, got %s", key, type(value))
                return False
            value_str = "O" if value else "F"
            result = await self._request_handler.set_value(self._device_id, full_key, value_str, "STRING")
            if result:
                self._cache.pop(key, None)
            return result
        except (KeyError, TypeError, AttributeError, ValueError) as err:
            _LOGGER.warning("Error setting switch '%s': %s", key, err)
            return False

    async def set_select(self, key: str, value: Any) -> bool:
        """Set select value with validation and device update."""
        if key not in self._mapping or self._mapping[key].get("type") != "select":
            _LOGGER.warning("Key '%s' is not a valid select", key)
            return False
        try:
            mapping_entry = self._mapping[key]
            options = mapping_entry.get("options", {})
            conversion = mapping_entry.get("conversion", {})
            valid_values = [conversion[option_text] if option_text in conversion else option_text for _, option_text in options.items()]
            if value not in valid_values:
                _LOGGER.warning("Value '%s' is not a valid option for %s. Valid options: %s", value, key, valid_values)
                return False
            key_device = mapping_entry.get("key", key)
            full_key = f"{self._prefix}{key_device}"
            device_value = value
            if "conversion" in mapping_entry and "options" in mapping_entry:
                for option_key, option_text in options.items():
                    if option_text in conversion and conversion[option_text] == value:
                        device_value = int(option_key)
                        break
                else:
                    for option_key, option_text in options.items():
                        if option_text == value:
                            device_value = int(option_key)
                            break
                    else:
                        _LOGGER.warning("Value '%s' not found in options for '%s'", value, key)
                        return False
            result = await self._request_handler.set_value(self._device_id, full_key, device_value, "NUMBER")
            if result:
                self._cache.pop(key, None)
            return result
        except (KeyError, TypeError, AttributeError, ValueError) as err:
            _LOGGER.warning("Error setting select '%s': %s", key, err)
            return False

    def _get_corresponding_value(self, name: str, field: str, attributes: Dict[str, Any]) -> Any:
        """
        Returns the value of the corresponding field (minT/maxT) for the given mapping.
        """
        corresponding_field = "maxT" if field == "minT" else "minT"
        # Search for the mapping entry with the corresponding field
        for k, v in self._mapping.items():
            if v.get("type") == "number" and v.get("field") == corresponding_field and v.get("key") == attributes.get("key"):
                val = self[k]
                return val[0] if isinstance(val, tuple) else val
        # Fallback: get from raw device entry if not found in mapping
        raw_entry = self._find_device_entry(name)
        if raw_entry is None:
            return None

        if corresponding_field in raw_entry:
            return raw_entry[corresponding_field]
        # Final fallback: use absMin for minT, absMax for maxT
        if corresponding_field == "minT":
            return raw_entry.get("absMin")
        elif corresponding_field == "maxT":
            return raw_entry.get("absMax")
        return None
