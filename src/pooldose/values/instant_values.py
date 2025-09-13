"""Instant values for Async API client for SEKO Pooldose."""

import logging
from typing import Any, Dict, Tuple, Union

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
            device_data (Dict[str, Any]): Raw device data from API.
            mapping (Dict[str, Any]): Mapping configuration.
            prefix (str): Key prefix for device data lookup.
            device_id (str): Device ID.
            request_handler (RequestHandler): API request handler.
        """
        self._device_data = device_data  # Raw format: {"PDPR1H1HAW100_FW539187_w_1eommf39k": {...}, ...}
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
        if value is not None:
            self._cache[key] = value
        return value

    async def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-like async write access to instant values."""
        await self._set_value(key, value)

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
            {
                "sensor": {
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
        """Process number value and return (value, unit, min, max, step) tuple."""
        if not isinstance(raw_entry, dict):
            _LOGGER.warning("Invalid raw entry type for number '%s': expected dict, got %s", name, type(raw_entry))
            return (None, None, None, None, None)

        value = raw_entry.get("current")
        abs_min = raw_entry.get("absMin")
        abs_max = raw_entry.get("absMax")
        resolution = raw_entry.get("resolution")

        # Get unit
        units = raw_entry.get("magnitude", [""])
        unit = units[0] if units and units[0].lower() not in ("undefined", "ph") else None

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

            # Validate range (only if min/max are defined)
            if min_val is not None and max_val is not None:
                if not min_val <= value <= max_val:
                    _LOGGER.warning("Value %s is out of range for %s. Valid range: %s - %s", value, key, min_val, max_val)
                    return False

            # Validate step (for float values)
            if isinstance(value, float) and step and min_val is not None:
                epsilon = 1e-9
                n = (value - min_val) / step
                if abs(round(n) - n) > epsilon:
                    _LOGGER.warning("Value %s is not a valid step for %s. Step: %s", value, key, step)
                    return False

            success = await self._set_value(key, value)
            if success:
                # Clear cache to force refresh of value
                self._cache.pop(key, None)
            return success

        except (TypeError, ValueError, IndexError) as err:
            _LOGGER.warning("Error validating number '%s': %s", key, err)
            return False

    async def set_switch(self, key: str, value: bool) -> bool:
        """Set switch value."""
        if key not in self._mapping or self._mapping[key].get("type") != "switch":
            _LOGGER.warning("Key '%s' is not a valid switch", key)
            return False

        success = await self._set_value(key, value)
        if success:
            # Clear cache to force refresh of value
            self._cache.pop(key, None)
        return success

    async def set_select(self, key: str, value: Any) -> bool:
        """Set select value with validation."""
        if key not in self._mapping or self._mapping[key].get("type") != "select":
            _LOGGER.warning("Key '%s' is not a valid select", key)
            return False

        # Validate against available converted values (not raw options)
        mapping_entry = self._mapping[key]
        options = mapping_entry.get("options", {})
        conversion = mapping_entry.get("conversion", {})

        # Build list of valid display values
        valid_values = []
        for _, option_text in options.items():
            if option_text in conversion:
                valid_values.append(conversion[option_text])
            else:
                valid_values.append(option_text)

        if value not in valid_values:
            _LOGGER.warning("Value '%s' is not a valid option for %s. Valid options: %s", value, key, valid_values)
            return False

        success = await self._set_value(key, value)
        if success:
            # Clear cache to force refresh of value
            self._cache.pop(key, None)
        return success

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

            # Convert value back to device format if needed
            device_value = value

            # Handle different types
            if entry_type == "number":
                if not isinstance(device_value, (int, float)):
                    _LOGGER.warning("Invalid type for number '%s': expected int/float, got %s", name, type(device_value))
                    return False
                result = await self._request_handler.set_value(self._device_id, full_key, device_value, "NUMBER")

            elif entry_type == "switch":
                if not isinstance(value, bool):
                    _LOGGER.warning("Invalid type for switch '%s': expected bool, got %s", name, type(value))
                    return False
                value_str = "O" if value else "F"  # O = True, F = False
                result = await self._request_handler.set_value(self._device_id, full_key, value_str, "STRING")

            elif entry_type == "select":
                # For selects, we need to reverse the conversion process
                if "conversion" in attributes and "options" in attributes:
                    # Find the option key for the given display value
                    conversion = attributes["conversion"]
                    options = attributes["options"]

                    # Reverse lookup: display value -> option text -> option key
                    for option_key, option_text in options.items():
                        if option_text in conversion and conversion[option_text] == value:
                            device_value = int(option_key)
                            break
                    else:
                        # Direct lookup if no conversion chain
                        for option_key, option_text in options.items():
                            if option_text == value:
                                device_value = int(option_key)
                                break
                        else:
                            _LOGGER.warning("Value '%s' not found in options for '%s'", value, name)
                            return False

                result = await self._request_handler.set_value(self._device_id, full_key, device_value, "NUMBER")

            else:
                _LOGGER.warning("Unsupported type '%s' for setting value '%s'", entry_type, name)
                return False

            return result

        except (KeyError, TypeError, AttributeError, ValueError) as err:
            _LOGGER.warning("Error setting value '%s': %s", name, err)
            return False
