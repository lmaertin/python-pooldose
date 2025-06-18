from typing import Any, Dict
from pooldose.request_handler import RequestHandler

class InstantValues:
    """
    Represents instant values from the Pooldose device, providing
    property-based access to all relevant sensor, binary sensor,
    switch, number, and select values.

    This class uses a mapping and a prefix to resolve the correct
    keys in the device data and provides type-safe accessors and
    setters (where applicable).

    Args:
        device_data (Dict[str, Any]): Raw data for the device.
        mapping (Dict[str, Any]): Mapping configuration for the model.
        prefix (str): Prefix for all keys in the device data.
        request_handler (RequestHandler): Handler for API requests.
    """

    def __init__(self, device_id : str, device_raw_data: Dict[str, Any], mapping: Dict[str, Any], prefix: str, request_handler: RequestHandler):
        self._device_id = device_id
        self._device_raw_data = device_raw_data
        self._mapping = mapping
        self._prefix = prefix
        self._request_handler = request_handler

    def _get_value(self, name: str) -> Any:
        """
        Internal helper to retrieve a value from the device data using the mapping.

        Args:
            name (str): Logical name of the value.

        Returns:
            Any: The value, or None if not found or type mismatch.
        """
        meta = self._mapping.get(name)
        if not meta:
            return None
        key = meta.get("key")
        if not key:
            key = name  # fallback if key is not set
        full_key = f"{self._prefix}{key}"
        entry = self._device_raw_data.get(full_key)
        if entry is None:
            return None
        type_ = meta.get("type")
        if not type_:
            return None
        # Sensor: return tuple (value, unit)
        if type_ == "sensor":
            value = entry.get("current") if isinstance(entry, dict) else entry
            unit = meta.get("unit", "")
            return (value, unit)
        # Binary sensor: return bool
        if type_ == "binary_sensor":
            if isinstance(entry, bool):
                return entry
            return None
        # Switch: return bool
        if type_ == "switch":
            if isinstance(entry, bool):
                return entry
            return None
        # Number: return float
        if type_ == "number":
            value = entry.get("current") if isinstance(entry, dict) else entry
            try:
                return float(value)
            except Exception:
                return None
        # Select: return str
        if type_ == "select":
            value = entry.get("current") if isinstance(entry, dict) else entry
            return str(value)
        return entry

    async def _set_value(self, name: str, value: Any) -> bool:
        """
        Internal helper to set a value on the device using the request handler.

        Args:
            name (str): Logical name of the value.
            value (Any): Value to set.

        Returns:
            bool: True if set was successful, False otherwise.
        """
        meta = self._mapping.get(name)
        if not meta:
            return False
        type_ = meta.get("type")
        key = meta.get("key")
        if not key:
            key = name
        full_key = f"{self._prefix}{key}"
        # Add further type checks as needed
        if type_ == "number":
            await self._request_handler.set_value(self._device_id, full_key, value, "number")
            return True
        if type_ == "switch":
            await self._request_handler.set_value(self._device_id, full_key, value, "switch")
            return True
        if type_ == "select":
            await self._request_handler.set_value(self._device_id, full_key, value, "select")
            return True
        return False

    ### Sensors ###
    @property
    def sensor_temperature(self) -> tuple[float, str]:
        """Current temperature value and unit."""
        return self._get_value("temp_actual")

    @property
    def sensor_ph(self) -> tuple[float, str]:
        """Current pH value and unit."""
        return self._get_value("ph_actual")

    @property
    def sensor_orp(self) -> tuple[float, str]:
        """Current ORP value and unit."""
        return self._get_value("orp_actual")

    @property
    def sensor_ph_type_dosing(self) -> str:
        """Returns the current pH dosing type as a string."""
        return self._get_value("ph_type_dosing")[0]

    @property
    def sensor_peristaltic_ph_dosing(self) -> str:
        """Returns the current peristaltic pH dosing mode as a string."""
        return self._get_value("peristaltic_ph_dosing")[0]

    @property
    def sensor_ofa_ph_value(self) -> tuple[float, str]:
        """Returns the current OFA pH value and its unit as a tuple."""
        return self._get_value("ofa_ph_value")

    @property
    def sensor_orp_type_dosing(self) -> str:
        """Returns the current ORP dosing type as a string."""
        return self._get_value("orp_type_dosing")[0]

    @property
    def sensor_peristaltic_orp_dosing(self) -> str:
        """Returns the current peristaltic ORP dosing mode as a string."""
        return self._get_value("peristaltic_orp_dosing")[0]

    @property
    def sensor_ofa_orp_value(self) -> tuple[float, str]:
        """Returns the current OFA ORP value and its unit as a tuple."""
        return self._get_value("ofa_orp_value")

    @property
    def sensor_ph_calibration_type(self) -> str:
        """Returns the current pH calibration type as a string."""
        return self._get_value("ph_calibration_type")[0]

    @property
    def sensor_ph_calibration_offset(self) -> tuple[float, str]:
        """Returns the current pH calibration offset and its unit as a tuple."""
        return self._get_value("ph_calibration_offset")

    @property
    def sensor_ph_calibration_slope(self) -> tuple[float, str]:
        """Returns the current pH calibration slope and its unit as a tuple."""
        return self._get_value("ph_calibration_slope")

    @property
    def sensor_orp_calibration_type(self) -> str:
        """Returns the current ORP calibration type as a string."""
        return self._get_value("orp_calibration_type")[0]

    @property
    def sensor_orp_calibration_offset(self) -> tuple[float, str]:
        """Returns the current ORP calibration offset and its unit as a tuple."""
        return self._get_value("orp_calibration_offset")

    @property
    def sensor_orp_calibration_slope(self) -> tuple[float, str]:
        """Returns the current ORP calibration slope and its unit as a tuple."""
        return self._get_value("orp_calibration_slope")

    ### Binary Sensors ###
    @property
    def binary_sensor_pump_running(self) -> bool:
        """Returns True if the pump is running, False otherwise."""
        return self._get_value("pump_running")

    @property
    def binary_sensor_ph_level_ok(self) -> bool:
        """Returns True if the pH level is OK, False otherwise."""
        return self._get_value("ph_level_ok")

    @property
    def binary_sensor_orp_level_ok(self) -> bool:
        """Returns True if the ORP level is OK, False otherwise."""
        return self._get_value("orp_level_ok")

    @property
    def binary_sensor_flow_rate_ok(self) -> bool:
        """Returns True if the flow rate is OK, False otherwise."""
        return self._get_value("flow_rate_ok")

    @property
    def binary_sensor_alarm_relay(self) -> bool:
        """Returns True if the alarm relay is active, False otherwise."""
        return self._get_value("alarm_relay")

    @property
    def binary_sensor_relay_aux1_ph(self) -> bool:
        """Returns True if the auxiliary relay 1 for pH is active, False otherwise."""
        return self._get_value("relay_aux1_ph")

    @property
    def binary_sensor_relay_aux2_orpcl(self) -> bool:
        """Returns True if the auxiliary relay 2 for ORP/CL is active, False otherwise."""
        return self._get_value("relay_aux2_orpcl")

    ### Numbers ###
    @property
    def number_orp_target(self) -> tuple[int, str, int, int, int]:
        """
        Returns a tuple with the ORP target value and its metadata.
        (Adapt the tuple structure to your mapping as needed.)
        """
        return self._get_value("orp_target")

    @property
    def number_ph_target(self) -> tuple[float, str, int, int, float]:
        """
        Returns a tuple with the pH target value and its metadata.
        (Adapt the tuple structure to your mapping as needed.)
        """
        return self._get_value("ph_target")

    ### Switches ###
    @property
    def switch_stop_pool_dosing(self) -> bool:
        """Returns True if pool dosing is stopped, False otherwise."""
        return self._get_value("stop_pool_dosing")

    @property
    def switch_pump_detection(self) -> bool:
        """Returns True if pump detection is active, False otherwise."""
        return self._get_value("pump_detection")

    @property
    def switch_frequency_input(self) -> bool:
        """Returns True if frequency input is active, False otherwise."""
        return self._get_value("frequency_input")

    ### Selects ###
    @property
    def select_water_meter_unit(self) -> str:
        """Returns the current water meter unit as a string."""
        return self._get_value("water_meter_unit")

    ### Setters for values ###
    ### Numbers ###
    async def number_orp_target_set(self, value: int) -> bool:
        """
        Set the ORP target value after validating range and step.

        Args:
            value (int): The value to set for ORP target.

        Raises:
            ValueError: If the value is out of range or does not match the allowed step.

        Returns:
            bool: True if the value was set successfully.
        """
        min, max, step = self.number_orp_target[2], self.number_orp_target[3], self.number_orp_target[4]
        if value in range(min, max, step):
            return await self._set_value("orp_target", value)
        else:
            raise ValueError(f"Value {value} is out of range for orp_target. Valid range: {min} - {max}, step: {step}")

    async def number_ph_target_set(self, value: float) -> bool:
        """
        Set the pH target value after validating range and step.

        Args:
            value (float): The value to set for pH target.

        Raises:
            ValueError: If the value is out of range or does not match the allowed step.

        Returns:
            bool: True if the value was set successfully.
        """
        min, max, step = self.number_ph_target[2], self.number_ph_target[3], self.number_ph_target[4]
        #python range does not work with floats, so we need to check manually
        epsilon = 1e-9 # using a very small epsilon to fix rounding issues with float precision
        if not (min <= value <= max):
            raise ValueError(f"Value {value} is out of range for ph_target. Valid range: {min} - {max}, step: {step}")
        n = (value - min) / step
        if abs(round(n) - n) > epsilon:
            raise ValueError(f"Value {value} is not a valid step for ph_target. Valid range: {min} - {max}, step: {step}")
        return await self._set_value("ph_target", value)
        
    ### Switches ###
    async def switch_stop_pool_dosing_set(self, value: bool) -> bool:
        """
        Set the stop pool dosing switch.

        Args:
            value (bool): The value to set.

        Returns:
            bool: True if the value was set successfully.
        """
        return await self._set_value("stop_pool_dosing", value)

    async def switch_pump_detection_set(self, value: bool) -> bool:
        """
        Set the pump detection switch.

        Args:
            value (bool): The value to set.

        Returns:
            bool: True if the value was set successfully.
        """
        return await self._set_value("pump_detection", value)

    async def switch_frequency_input_set(self, value: bool) -> bool:
        """
        Set the frequency input switch.

        Args:
            value (bool): The value to set.

        Returns:
            bool: True if the value was set successfully.
        """
        return await self._set_value("frequency_input", value)
    
    ### Selects ###
    async def select_water_meter_unit_set(self, value: int) -> bool:
        """
        Set the water meter unit select value.

        Args:
            value (int): The value to set.

        Returns:
            bool: True if the value was set successfully.
        """
        return await self._set_value("water_meter_unit", value)
