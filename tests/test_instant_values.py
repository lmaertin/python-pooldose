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

    def test_getitem_sensor_chlorine_unit(self, instant_values_fixture):
        """Test getting chlorine sensor values with ppm unit conversion."""
        value, unit = instant_values_fixture["chlorine"]
        assert value == 0.5
        assert unit == "ppm"

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

    def test_getitem_number_chlorine_unit(self, instant_values_fixture):
        """Test getting chlorine number values with ppm unit conversion."""
        value, unit, min_val, max_val, step = instant_values_fixture["chlorine_target"]
        assert value == 0.6
        assert unit == "ppm"
        assert min_val == 0.3
        assert max_val == 3.0
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
    async def test_set_threshold_accepts_full_absolute_range(self, instant_values_fixture, mock_request_handler):
        """Test threshold writes use both values without an artificial split."""
        # pylint: disable=protected-access
        instant_values_fixture._request_handler = mock_request_handler

        result = await instant_values_fixture.set_number("ofa_ph_lower", 7.5)

        assert result is True
        mock_request_handler.set_value.assert_awaited_once_with(
            "TEST123_DEVICE",
            "PDPR1H1HAW100_FW539187_w_ofa_ph",
            [7.5, 7.8],
            "NUMBER",
        )

    @pytest.mark.asyncio
    async def test_set_threshold_rejects_inverted_range(self, instant_values_fixture, mock_request_handler):
        """Test threshold writes reject minT values at or above maxT."""
        # pylint: disable=protected-access
        instant_values_fixture._request_handler = mock_request_handler

        result = await instant_values_fixture.set_number("ofa_ph_lower", 7.8)

        assert result is False
        mock_request_handler.set_value.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_threshold_clears_both_caches(self, instant_values_fixture, mock_request_handler):
        """Test a threshold write invalidates both paired cache entries."""
        # pylint: disable=protected-access
        instant_values_fixture._request_handler = mock_request_handler
        assert instant_values_fixture["ofa_ph_lower"] is not None
        assert instant_values_fixture["ofa_ph_upper"] is not None
        assert "ofa_ph_lower" in instant_values_fixture._cache
        assert "ofa_ph_upper" in instant_values_fixture._cache

        result = await instant_values_fixture.set_number("ofa_ph_lower", 7.0)

        assert result is True
        assert "ofa_ph_lower" not in instant_values_fixture._cache
        assert "ofa_ph_upper" not in instant_values_fixture._cache

    @pytest.mark.asyncio
    async def test_set_orp_lower_threshold_accepts_realistic_value(self, instant_values_fixture, mock_request_handler):
        """Test an ORP lower threshold above the old artificial limit is accepted."""
        # pylint: disable=protected-access
        instant_values_fixture._request_handler = mock_request_handler

        result = await instant_values_fixture.set_number("ofa_orp_lower", 650)

        assert result is True
        mock_request_handler.set_value.assert_awaited_once_with(
            "TEST123_DEVICE",
            "PDPR1H1HAW100_FW539187_w_ofa_orp",
            [650, 800],
            "NUMBER",
        )

    @pytest.mark.asyncio
    async def test_set_orp_lower_threshold_rejects_inverted_pair(self, instant_values_fixture, mock_request_handler):
        """Test an ORP lower threshold above maxT is rejected."""
        # pylint: disable=protected-access
        instant_values_fixture._request_handler = mock_request_handler

        result = await instant_values_fixture.set_number("ofa_orp_lower", 850)

        assert result is False
        mock_request_handler.set_value.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_orp_upper_threshold_rejects_inverted_pair(self, instant_values_fixture, mock_request_handler):
        """Test an ORP upper threshold below minT is rejected."""
        # pylint: disable=protected-access
        instant_values_fixture._request_handler = mock_request_handler

        result = await instant_values_fixture.set_number("ofa_orp_upper", 500)

        assert result is False
        mock_request_handler.set_value.assert_not_awaited()

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

    # --- minT/maxT number processing tests ---

    def test_number_min_t_field(self, instant_values_fixture):
        """Test that minT field exposes the device's absolute range."""
        result = instant_values_fixture["ofa_ph_lower"]
        value, _, min_val, max_val, step = result
        assert value == 6.5
        assert min_val == 0.0
        assert max_val == 14.0
        assert step == 0.1

    def test_number_max_t_field(self, instant_values_fixture):
        """Test that maxT field exposes the device's absolute range."""
        result = instant_values_fixture["ofa_ph_upper"]
        value, _, min_val, max_val, step = result
        assert value == 7.8
        assert min_val == 0.0
        assert max_val == 14.0
        assert step == 0.1

    def test_number_min_t_structured_dict(self, instant_values_fixture):
        """Test that minT/maxT numbers appear correctly in structured dict."""
        structured = instant_values_fixture.to_structured_dict()
        assert "ofa_ph_lower" in structured["number"]
        assert structured["number"]["ofa_ph_lower"]["value"] == 6.5
        assert structured["number"]["ofa_ph_lower"]["max"] == 14.0
        assert "ofa_ph_upper" in structured["number"]
        assert structured["number"]["ofa_ph_upper"]["value"] == 7.8
        assert structured["number"]["ofa_ph_upper"]["min"] == 0.0

    # --- _get_corresponding_value tests ---

    def test_get_corresponding_value_from_mapping(self, instant_values_fixture):
        """Test _get_corresponding_value finds the paired minT/maxT entry via mapping."""
        # pylint: disable=protected-access
        attrs = instant_values_fixture._mapping["ofa_ph_lower"]
        # ofa_ph_lower has field=minT, so corresponding should find ofa_ph_upper (maxT)
        result = instant_values_fixture._get_corresponding_value("ofa_ph_lower", "minT", attrs)
        assert result == 7.8  # maxT value from the device data

    def test_get_corresponding_value_reverse(self, instant_values_fixture):
        """Test _get_corresponding_value finds minT from maxT."""
        # pylint: disable=protected-access
        attrs = instant_values_fixture._mapping["ofa_ph_upper"]
        # ofa_ph_upper has field=maxT, so corresponding should find ofa_ph_lower (minT)
        result = instant_values_fixture._get_corresponding_value("ofa_ph_upper", "maxT", attrs)
        assert result == 6.5  # minT value from the device data

    def test_get_corresponding_value_fallback_raw(self, instant_values_fixture):
        """Test _get_corresponding_value falls back to raw device entry when no mapping pair exists."""
        # pylint: disable=protected-access
        # Remove the paired mapping entry to force fallback
        saved = instant_values_fixture._mapping.pop("ofa_ph_upper")
        attrs = instant_values_fixture._mapping["ofa_ph_lower"]
        result = instant_values_fixture._get_corresponding_value("ofa_ph_lower", "minT", attrs)
        # Fallback should find maxT directly in raw entry
        assert result == 7.8
        # Restore mapping
        instant_values_fixture._mapping["ofa_ph_upper"] = saved

    def test_get_corresponding_value_fallback_abs(self, instant_values_fixture):
        """Test _get_corresponding_value falls back to absMin/absMax when no field found."""
        # pylint: disable=protected-access
        # Remove paired mapping and remove the direct field from device data
        saved_mapping = instant_values_fixture._mapping.pop("ofa_ph_upper")
        raw_key = "PDPR1H1HAW100_FW539187_w_ofa_ph"
        saved_max_t = instant_values_fixture._device_data[raw_key].pop("maxT")
        attrs = instant_values_fixture._mapping["ofa_ph_lower"]
        result = instant_values_fixture._get_corresponding_value("ofa_ph_lower", "minT", attrs)
        # Should fall back to absMax
        assert result == 14.0
        # Restore
        instant_values_fixture._device_data[raw_key]["maxT"] = saved_max_t
        instant_values_fixture._mapping["ofa_ph_upper"] = saved_mapping

    def test_get_corresponding_value_no_data(self, instant_values_fixture):
        """Test _get_corresponding_value returns None when no data available."""
        # pylint: disable=protected-access
        result = instant_values_fixture._get_corresponding_value("nonexistent", "minT", {"key": "w_nonexistent"})
        assert result is None

    # --- binary_sensor with conversion tests ---

    def test_binary_sensor_with_conversion_false(self, instant_values_fixture):
        """Test binary sensor with conversion mapping returning False."""
        value = instant_values_fixture["binary_conv_sensor"]
        assert value is False

    def test_binary_sensor_with_conversion_in_structured(self, instant_values_fixture):
        """Test binary sensor with conversion appears in structured dict."""
        structured = instant_values_fixture.to_structured_dict()
        assert "binary_conv_sensor" in structured["binary_sensor"]
        assert structured["binary_sensor"]["binary_conv_sensor"]["value"] is False
