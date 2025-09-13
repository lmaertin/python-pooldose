"""Tests for InstantValues class."""

import pytest

# pylint: disable=line-too-long

class TestInstantValues:  # pylint: disable=too-many-public-methods
    """Test InstantValues functionality."""

    def test_init(self, instant_values_fixture):
        """Test InstantValues initialization."""
        # pylint: disable=protected-access
        assert instant_values_fixture._prefix == "PDPR1H1HAW100_FW539187_"
        assert instant_values_fixture._device_id == "TEST123_DEVICE"
        assert len(instant_values_fixture._cache) == 0

    def test_getitem_sensor(self, instant_values_fixture):
        """Test getting sensor values."""
        value, unit = instant_values_fixture["temperature"]
        assert value == 25.5
        assert unit == "°C"

    def test_getitem_sensor_with_conversion(self, instant_values_fixture):
        """Test getting sensor values with string conversion."""
        value, unit = instant_values_fixture["ph_type_dosing"]
        assert value == "alcalyne"
        assert unit is None

    def test_getitem_number(self, instant_values_fixture):
        """Test getting number values."""
        value, unit, min_val, max_val, step = instant_values_fixture["target_ph"]
        assert value == 7.0
        assert unit is None
        assert min_val == 6.0
        assert max_val == 8.0
        assert step == 0.1

    def test_getitem_switch(self, instant_values_fixture):
        """Test getting switch values."""
        value = instant_values_fixture["pump_switch"]
        assert value is True

    def test_getitem_binary_sensor(self, instant_values_fixture):
        """Test getting binary sensor values."""
        value = instant_values_fixture["alarm_ph"]
        assert value is True

    def test_getitem_select(self, instant_values_fixture):
        """Test getting select values with conversion."""
        value = instant_values_fixture["water_unit"]
        assert value == "m³"

    def test_getitem_cached(self, instant_values_fixture):
        """Test that values are cached."""
        # First access
        value1 = instant_values_fixture["temperature"]
        # Second access should use cache
        value2 = instant_values_fixture["temperature"]
        assert value1 == value2
        # pylint: disable=protected-access
        assert "temperature" in instant_values_fixture._cache

    def test_contains(self, instant_values_fixture):
        """Test 'in' operator."""
        assert "temperature" in instant_values_fixture
        assert "nonexistent" not in instant_values_fixture

    def test_get_with_default(self, instant_values_fixture):
        """Test get method with default value."""
        value = instant_values_fixture.get("temperature", "default")
        assert value is not None

        value = instant_values_fixture.get("nonexistent", "default")
        assert value == "default"

    def test_to_structured_dict(self, instant_values_fixture):
        """Test conversion to structured dictionary."""
        structured = instant_values_fixture.to_structured_dict()

        assert "sensor" in structured
        assert "number" in structured
        assert "switch" in structured
        assert "binary_sensor" in structured
        assert "select" in structured

        # Check sensor structure
        assert "temperature" in structured["sensor"]
        assert structured["sensor"]["temperature"]["value"] == 25.5
        assert structured["sensor"]["temperature"]["unit"] == "°C"

        # Check number structure
        assert "target_ph" in structured["number"]
        assert structured["number"]["target_ph"]["value"] == 7.0
        assert structured["number"]["target_ph"]["min"] == 6.0
        assert structured["number"]["target_ph"]["max"] == 8.0

    @pytest.mark.asyncio
    async def test_set_number_success(self, instant_values_fixture):
        """Test setting number value successfully."""
        result = await instant_values_fixture.set_number("target_ph", 7.2)
        assert result is True
        # Cache should be cleared
        # pylint: disable=protected-access
        assert "target_ph" not in instant_values_fixture._cache

    @pytest.mark.asyncio
    async def test_set_number_out_of_range(self, instant_values_fixture):
        """Test setting number value out of range."""
        result = await instant_values_fixture.set_number("target_ph", 9.0)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_number_invalid_key(self, instant_values_fixture):
        """Test setting number with invalid key."""
        result = await instant_values_fixture.set_number("nonexistent", 7.0)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_switch_success(self, instant_values_fixture):
        """Test setting switch value successfully."""
        result = await instant_values_fixture.set_switch("pump_switch", False)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_switch_invalid_key(self, instant_values_fixture):
        """Test setting switch with invalid key."""
        result = await instant_values_fixture.set_switch("nonexistent", True)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_select_success(self, instant_values_fixture):
        """Test setting select value successfully."""
        result = await instant_values_fixture.set_select("water_unit", "L")
        assert result is True

    @pytest.mark.asyncio
    async def test_set_select_invalid_value(self, instant_values_fixture):
        """Test setting select with invalid value."""
        result = await instant_values_fixture.set_select("water_unit", "invalid")
        assert result is False

    def test_find_device_entry(self, instant_values_fixture):
        """Test finding device entries."""
        # pylint: disable=protected-access
        entry = instant_values_fixture._find_device_entry("temperature")
        assert entry is not None
        assert entry["current"] == 25.5

        entry = instant_values_fixture._find_device_entry("nonexistent")
        assert entry is None

    def test_process_sensor_value_invalid_entry(self, instant_values_fixture):
        """Test processing sensor value with invalid entry."""
        # pylint: disable=protected-access
        value, unit = instant_values_fixture._process_sensor_value("invalid", {}, "test")
        assert value is None
        assert unit is None

    def test_process_binary_sensor_value_invalid_entry(self, instant_values_fixture):
        """Test processing binary sensor value with invalid entry."""
        # pylint: disable=protected-access
        value = instant_values_fixture._process_binary_sensor_value("invalid", {}, "test")
        assert value is None

    def test_process_switch_value_bool(self, instant_values_fixture):
        """Test processing switch value with direct boolean."""
        # pylint: disable=protected-access
        value = instant_values_fixture._process_switch_value(True, "test")
        assert value is True

    def test_process_number_value_invalid_entry(self, instant_values_fixture):
        """Test processing number value with invalid entry."""
        # pylint: disable=protected-access
        result = instant_values_fixture._process_number_value("invalid", "test")
        assert result == (None, None, None, None, None)

    @pytest.mark.asyncio
    async def test_set_value_request_handler_failure(self, instant_values_fixture):
        """Test setting value when request handler fails."""
        # pylint: disable=protected-access
        instant_values_fixture._request_handler.set_value.return_value = False

        result = await instant_values_fixture.set_number("target_ph", 7.2)
        assert result is False

    def test_get_value_missing_mapping(self, instant_values_fixture):
        """Test getting value with missing mapping."""
        # pylint: disable=protected-access
        value = instant_values_fixture._get_value("nonexistent")
        assert value is None

    def test_get_value_no_raw_data(self, instant_values_fixture):
        """Test getting value when no raw data exists."""
        # Add mapping for key that doesn't exist in device data
        # pylint: disable=protected-access
        instant_values_fixture._mapping["missing"] = {"type": "sensor", "key": "w_missing"}

        value = instant_values_fixture._get_value("missing")
        assert value is None

    def test_get_value_unknown_type(self, instant_values_fixture):
        """Test getting value with unknown type."""
        # pylint: disable=protected-access
        instant_values_fixture._mapping["unknown"] = {"type": "unknown", "key": "w_1eommf39k"}

        value = instant_values_fixture._get_value("unknown")
        assert value is None
