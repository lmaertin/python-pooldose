"""Instant values for Async API client for SEKO Pooldose."""

import logging
from typing import Any, Dict, Optional
from pooldose.request_handler import RequestHandler
# pylint: disable=line-too-long,too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-return-statements,too-many-branches,no-else-return,too-many-public-methods

_LOGGER = logging.getLogger(__name__)

class InstantValues:
    """
    Provides property-based access to instant values from the Pooldose device.
    All getter methods return None on error and log a warning.
    All setter methods return False on error and log a warning.
    """

    def __init__(self, device_data: Dict[str, Any], mapping: Dict[str, Any], prefix: str, device_id : str, request_handler: RequestHandler):
        """
        Initialize InstantValues.

        Args:
            device_data (Dict[str, Any]): Raw device data.
            mapping (Dict[str, Any]): Mapping configuration.
            prefix (str): Key prefix.
            request_handler (RequestHandler): API request handler.
        """
        self._device_data = device_data
        self._mapping = mapping
        self._prefix = prefix
        self._device_id = device_id
        self._request_handler = request_handler

    def _get_value(self, name: str) -> Any:
        """
        Internal helper to retrieve a value from the device data using the mapping.
        Returns None and logs a warning on error.
        """
        try:
            attributes = self._mapping.get(name)
            if not attributes:
                return None
            key = attributes.get("key", name)
            full_key = f"{self._prefix}{key}"
            entry = self._device_data.get(full_key)
            if entry is None:
                return None
            entry_type = attributes.get("type")
            if not entry_type:
                return None
            # Sensor: return tuple (value, unit)
            if entry_type == "sensor":
                value = entry.get("current") if isinstance(entry, dict) else None
                if "conversion" in attributes:
                    conversion = attributes["conversion"]
                    if value in conversion:
                        value = conversion[value]
                units = entry.get("magnitude")
                if units:
                    unit = units[0]
                else:
                    unit = "" #no unit
                return (value, unit)

            # Binary sensor: return bool
            if entry_type == "binary_sensor":
                value = entry.get("current")
                if value is None:
                    return None
                return value=="F" # F = True, O = False
            # Switch: return bool
            if entry_type == "switch":
                if isinstance(entry, bool):
                    return entry
                return None
            # Number: return float or int
            if entry_type == "number":
                value = entry.get("current") if isinstance(entry, dict) else None
                abs_min = entry.get("absMin")
                abs_max = entry.get("absMax")
                resolution = entry.get("resolution")
                units = entry.get("magnitude")
                if units:
                    unit = units[0]
                else:
                    unit = "" #no unit
                return (value, unit, abs_min, abs_max, resolution)

            # Select: return str
            if entry_type == "select":
                value = entry.get("current") if isinstance(entry, dict) else None
                options = attributes.get("options")
                if not options:
                    return None
                value_text = None
                if value in options:
                    value_text = options.get(value)
                if "conversion" in attributes:
                    conversion = attributes["conversion"]
                    if value_text in conversion:
                        return conversion[value_text]
            return None #no valid type found
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
                return False
            entry_type = attributes.get("type")
            key = attributes.get("key", name)
            full_key = f"{self._prefix}{key}"
            # Add further type checks as needed
            if entry_type == "number":
                if not isinstance(value, (int, float)):
                    return False
                return await self._request_handler.set_value(self._device_id, full_key, value, "NUMBER")
            if entry_type == "switch":
                if not isinstance(value, bool):
                    return False
                value_str = "O" if value else "F"  # O = True, F = False
                return await self._request_handler.set_value(self._device_id, full_key, value_str, "STRING")
            if entry_type == "select":
                options = attributes.get("options")
                if options and str(value) not in options:
                    return False
                return await self._request_handler.set_value(self._device_id, full_key, value, "NUMBER")

            _LOGGER.warning("Unsupported type '%s' for setting value '%s'", entry_type, name)
            return False
        except (KeyError, TypeError, AttributeError, ValueError) as err:
            _LOGGER.warning("Error setting value '%s': %s", name, err)
            return False

    # Sensors
    @property
    def sensor_temperature(self) -> Optional[tuple[float, str]]:
        """Current temperature value and unit, or None on error."""
        return self._get_value("temp_actual")

    @property
    def sensor_ph(self) -> Optional[tuple[float, str]]:
        """Current pH value and unit, or None on error."""
        return self._get_value("ph_actual")

    @property
    def sensor_orp(self) -> Optional[tuple[float, str]]:
        """Current ORP value and unit, or None on error."""
        return self._get_value("orp_actual")

    @property
    def sensor_ph_type_dosing(self) -> Optional[str]:
        """Returns the current pH dosing type as a string, or None on error."""
        return self._get_value("ph_type_dosing")[0]

    @property
    def sensor_peristaltic_ph_dosing(self) -> Optional[str]:
        """Returns the current peristaltic pH dosing mode as a string, or None on error."""
        return self._get_value("peristaltic_ph_dosing")[0]

    @property
    def sensor_ofa_ph_value(self) -> Optional[tuple[float, str]]:
        """Returns the current OFA pH value and its unit as a tuple, or None on error."""
        return self._get_value("ofa_ph_value")

    @property
    def sensor_orp_type_dosing(self) -> Optional[str]:
        """Returns the current ORP dosing type as a string, or None on error."""
        return self._get_value("orp_type_dosing")[0]

    @property
    def sensor_peristaltic_orp_dosing(self) -> Optional[str]:
        """Returns the current peristaltic ORP dosing mode as a string, or None on error."""
        return self._get_value("peristaltic_orp_dosing")[0]

    @property
    def sensor_ofa_orp_value(self) -> Optional[tuple[float, str]]:
        """Returns the current OFA ORP value and its unit as a tuple, or None on error."""
        return self._get_value("ofa_orp_value")

    @property
    def sensor_ph_calibration_type(self) -> Optional[str]:
        """Returns the current pH calibration type as a string, or None on error."""
        return self._get_value("ph_calibration_type")[0]

    @property
    def sensor_ph_calibration_offset(self) -> Optional[tuple[float, str]]:
        """Returns the current pH calibration offset and its unit as a tuple, or None on error."""
        return self._get_value("ph_calibration_offset")

    @property
    def sensor_ph_calibration_slope(self) -> Optional[tuple[float, str]]:
        """Returns the current pH calibration slope and its unit as a tuple, or None on error."""
        return self._get_value("ph_calibration_slope")

    @property
    def sensor_orp_calibration_type(self) -> Optional[str]:
        """Returns the current ORP calibration type as a string, or None on error."""
        return self._get_value("orp_calibration_type")[0]

    @property
    def sensor_orp_calibration_offset(self) -> Optional[tuple[float, str]]:
        """Returns the current ORP calibration offset and its unit as a tuple, or None on error."""
        return self._get_value("orp_calibration_offset")

    @property
    def sensor_orp_calibration_slope(self) -> Optional[tuple[float, str]]:
        """Returns the current ORP calibration slope and its unit as a tuple, or None on error."""
        return self._get_value("orp_calibration_slope")

    # Binary Sensors
    @property
    def binary_sensor_pump_running(self) -> Optional[bool]:
        """Returns True if the pump is running, False otherwise, or None on error."""
        return self._get_value("pump_running")

    @property
    def binary_sensor_ph_level_ok(self) -> Optional[bool]:
        """Returns True if the pH level is OK, False otherwise, or None on error."""
        return self._get_value("ph_level_ok")

    @property
    def binary_sensor_orp_level_ok(self) -> Optional[bool]:
        """Returns True if the ORP level is OK, False otherwise, or None on error."""
        return self._get_value("orp_level_ok")

    @property
    def binary_sensor_flow_rate_ok(self) -> Optional[bool]:
        """Returns True if the flow rate is OK, False otherwise, or None on error."""
        return self._get_value("flow_rate_ok")

    @property
    def binary_sensor_alarm_relay(self) -> Optional[bool]:
        """Returns True if the alarm relay is active, False otherwise, or None on error."""
        return self._get_value("alarm_relay")

    @property
    def binary_sensor_relay_aux1_ph(self) -> Optional[bool]:
        """Returns True if the auxiliary relay 1 for pH is active, False otherwise, or None on error."""
        return self._get_value("relay_aux1_ph")

    @property
    def binary_sensor_relay_aux2_orpcl(self) -> Optional[bool]:
        """Returns True if the auxiliary relay 2 for ORP/CL is active, False otherwise, or None on error."""
        return self._get_value("relay_aux2_orpcl")

    # Numbers
    @property
    def number_orp_target(self) -> Optional[tuple[int, str, int, int, int]]:
        """
        Returns a tuple with the ORP target value and its metadata, or None on error.
        (Adapt the tuple structure to your mapping as needed.)
        """
        return self._get_value("orp_target")

    @property
    def number_ph_target(self) -> Optional[tuple[float, str, int, int, float]]:
        """
        Returns a tuple with the pH target value and its metadata, or None on error.
        (Adapt the tuple structure to your mapping as needed.)
        """
        return self._get_value("ph_target")

    # Switches
    @property
    def switch_stop_pool_dosing(self) -> Optional[bool]:
        """Returns True if pool dosing is stopped, False otherwise, or None on error."""
        return self._get_value("stop_pool_dosing")

    @property
    def switch_pump_detection(self) -> Optional[bool]:
        """Returns True if pump detection is active, False otherwise, or None on error."""
        return self._get_value("pump_detection")

    @property
    def switch_frequency_input(self) -> Optional[bool]:
        """Returns True if frequency input is active, False otherwise, or None on error."""
        return self._get_value("frequency_input")

    # Selects
    @property
    def select_water_meter_unit(self) -> Optional[str]:
        """Returns the current water meter unit as a string, or None on error."""
        return self._get_value("water_meter_unit")

    # Setters for values
    # Numbers
    async def number_orp_target_set(self, value: int) -> bool:
        """
        Set the ORP target value after validating range and step.
        Returns False and logs a warning on error.

        Args:
            value (int): The value to set for ORP target.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        try:
            result = self.number_orp_target
            if result is None:
                _LOGGER.warning("Cannot set ORP target: mapping or value missing.")
                return False
            min_val, max_val, step = result[2], result[3], result[4]
            if value in range(min_val, max_val, step):
                return await self._set_value("orp_target", value)
            else:
                _LOGGER.warning("Value %s is out of range for orp_target. Valid range: %s - %s, step: %s", value, min_val, max_val, step)
                return False
        except (TypeError, ValueError) as err:
            _LOGGER.warning("Error in number_orp_target_set: %s", err)
            return False

    async def number_ph_target_set(self, value: float) -> bool:
        """
        Set the pH target value after validating range and step.
        Returns False and logs a warning on error.

        Args:
            value (float): The value to set for pH target.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        try:
            result = self.number_ph_target
            if result is None:
                _LOGGER.warning("Cannot set pH target: mapping or value missing.")
                return False
            min_value, max_value, step = result[2], result[3], result[4]
            epsilon = 1e-9
            if not min_value <= value <= max_value:
                _LOGGER.warning("Value %s is out of range for ph_target. Valid range: %s - %s, step: %s", value, min_value, max_value, step)
                return False
            n = (value - min_value) / step
            if abs(round(n) - n) > epsilon:
                _LOGGER.warning("Value %s is not a valid step for ph_target. Valid range: %s - %s, step: %s", value, min_value, max_value, step)
                return False
            return await self._set_value("ph_target", value)
        except (TypeError, ValueError) as err:
            _LOGGER.warning("Error in number_ph_target_set: %s", err)
            return False

    # Switches
    async def switch_stop_pool_dosing_set(self, value: bool) -> bool:
        """
        Set the stop pool dosing switch.

        Args:
            value (bool): The value to set.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        return await self._set_value("stop_pool_dosing", value)

    async def switch_pump_detection_set(self, value: bool) -> bool:
        """
        Set the pump detection switch.

        Args:
            value (bool): The value to set.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        return await self._set_value("pump_detection", value)

    async def switch_frequency_input_set(self, value: bool) -> bool:
        """
        Set the frequency input switch.

        Args:
            value (bool): The value to set.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        return await self._set_value("frequency_input", value)
    
    # Selects
    async def select_water_meter_unit_set(self, value: int) -> bool:
        """
        Set the water meter unit select value.

        Args:
            value (int): The value to set.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        return await self._set_value("water_meter_unit", value)
