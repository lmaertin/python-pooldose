"""Tests for InstantValues class."""

import pytest
from unittest.mock import AsyncMock
from pooldose.values.instant_values import InstantValues


@pytest.fixture
def mock_request_handler():
    """Create a mock request handler."""
    handler = AsyncMock()
    handler.set_value.return_value = True
    return handler


@pytest.fixture
def mock_device_data():
    """Create mock device data."""
    return {
        "PDPR1H1HAW100_FW539187_w_1eommf39k": {
            "current": 25.5,
            "magnitude": ["°C"]
        },
        "PDPR1H1HAW100_FW539187_w_1eomog123": {
            "current": 7.2,
            "magnitude": ["ph"]
        },
        "PDPR1H1HAW100_FW539187_w_1eomph456": {
            "current": 7.0,
            "magnitude": ["ph"],
            "absMin": 6.0,
            "absMax": 8.0,
            "resolution": 0.1
        },
        "PDPR1H1HAW100_FW539187_w_1switch123": {
            "current": "O"
        },
        "PDPR1H1HAW100_FW539187_w_1select456": {
            "current": "0"
        },
        "PDPR1H1HAW100_FW539187_w_1label789": {
            "current": "|PDPR1H1HAW100_FW539187_LABEL_w_1eklg44ro_ALCALYNE|",
            "magnitude": ["undefined"]
        }
    }


@pytest.fixture
def mock_mapping():
    """Create mock mapping configuration."""
    return {
        "temperature": {
            "type": "sensor",
            "key": "w_1eommf39k"
        },
        "ph": {
            "type": "sensor",
            "key": "w_1eomog123"
        },
        "target_ph": {
            "type": "number",
            "key": "w_1eomph456"
        },
        "pump_switch": {
            "type": "switch",
            "key": "w_1switch123"
        },
        "water_unit": {
            "type": "select",
            "key": "w_1select456",
            "options": {
                "0": "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_M_",
                "1": "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_LITER"
            },
            "conversion": {
                "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_M_": "m³",
                "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_LITER": "L"
            }
        },
        "ph_type_dosing": {
            "type": "sensor",
            "key": "w_1label789",
            "conversion": {
                "|PDPR1H1HAW100_FW539187_LABEL_w_1eklg44ro_ALCALYNE|": "alcalyne"
            }
        },
        "alarm_ph": {
            "type": "binary_sensor",
            "key": "w_1switch123"
        }
    }


@pytest.fixture
def instant_values(mock_device_data, mock_mapping, mock_request_handler):
    """Create InstantValues instance."""
    return InstantValues(
        device_data=mock_device_data,
        mapping=mock_mapping,
        prefix="PDPR1H1HAW100_FW539187_",
        device_id="TEST123_DEVICE",
        request_handler=mock_request_handler
    )


class TestInstantValues:
    """Test InstantValues functionality."""

    def test_init(self, instant_values):
        """Test InstantValues initialization."""
        assert instant_values._prefix == "PDPR1H1HAW100_FW539187_"
        assert instant_values._device_id == "TEST123_DEVICE"
        assert len(instant_values._cache) == 0

    def test_getitem_sensor(self, instant_values):
        """Test getting sensor values."""
        value, unit = instant_values["temperature"]
        assert value == 25.5
        assert unit == "°C"

    def test_getitem_sensor_with_conversion(self, instant_values):
        """Test getting sensor values with string conversion."""
        value, unit = instant_values["ph_type_dosing"]
        assert value == "alcalyne"
        assert unit is None

    def test_getitem_number(self, instant_values):
        """Test getting number values."""
        value, unit, min_val, max_val, step = instant_values["target_ph"]
        assert value == 7.0
        assert unit is None
        assert min_val == 6.0
        assert max_val == 8.0
        assert step == 0.1

    def test_getitem_switch(self, instant_values):
        """Test getting switch values."""
        value = instant_values["pump_switch"]
        assert value is True

    def test_getitem_binary_sensor(self, instant_values):
        """Test getting binary sensor values."""
        value = instant_values["alarm_ph"]
        assert value is True

    def test_getitem_select(self, instant_values):
        """Test getting select values with conversion."""
        value = instant_values["water_unit"]
        assert value == "m³"

    def test_getitem_cached(self, instant_values):
        """Test that values are cached."""
        # First access
        value1 = instant_values["temperature"]
        # Second access should use cache
        value2 = instant_values["temperature"]
        assert value1 == value2
        assert "temperature" in instant_values._cache

    def test_contains(self, instant_values):
        """Test 'in' operator."""
        assert "temperature" in instant_values
        assert "nonexistent" not in instant_values

    def test_get_with_default(self, instant_values):
        """Test get method with default value."""
        value = instant_values.get("temperature", "default")
        assert value is not None
        
        value = instant_values.get("nonexistent", "default")
        assert value == "default"

    def test_to_structured_dict(self, instant_values):
        """Test conversion to structured dictionary."""
        structured = instant_values.to_structured_dict()
        
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
    async def test_set_number_success(self, instant_values):
        """Test setting number value successfully."""
        result = await instant_values.set_number("target_ph", 7.2)
        assert result is True
        # Cache should be cleared
        assert "target_ph" not in instant_values._cache

    @pytest.mark.asyncio
    async def test_set_number_out_of_range(self, instant_values):
        """Test setting number value out of range."""
        result = await instant_values.set_number("target_ph", 9.0)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_number_invalid_key(self, instant_values):
        """Test setting number with invalid key."""
        result = await instant_values.set_number("nonexistent", 7.0)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_switch_success(self, instant_values):
        """Test setting switch value successfully."""
        result = await instant_values.set_switch("pump_switch", False)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_switch_invalid_key(self, instant_values):
        """Test setting switch with invalid key."""
        result = await instant_values.set_switch("nonexistent", True)
        assert result is False

    @pytest.mark.asyncio
    async def test_set_select_success(self, instant_values):
        """Test setting select value successfully."""
        result = await instant_values.set_select("water_unit", "L")
        assert result is True

    @pytest.mark.asyncio
    async def test_set_select_invalid_value(self, instant_values):
        """Test setting select with invalid value."""
        result = await instant_values.set_select("water_unit", "invalid")
        assert result is False

    def test_find_device_entry(self, instant_values):
        """Test finding device entries."""
        entry = instant_values._find_device_entry("temperature")
        assert entry is not None
        assert entry["current"] == 25.5
        
        entry = instant_values._find_device_entry("nonexistent")
        assert entry is None

    def test_process_sensor_value_invalid_entry(self, instant_values):
        """Test processing sensor value with invalid entry."""
        value, unit = instant_values._process_sensor_value("invalid", {}, "test")
        assert value is None
        assert unit is None

    def test_process_binary_sensor_value_invalid_entry(self, instant_values):
        """Test processing binary sensor value with invalid entry."""
        value = instant_values._process_binary_sensor_value("invalid", "test")
        assert value is None

    def test_process_switch_value_bool(self, instant_values):
        """Test processing switch value with direct boolean."""
        value = instant_values._process_switch_value(True, "test")
        assert value is True

    def test_process_number_value_invalid_entry(self, instant_values):
        """Test processing number value with invalid entry."""
        result = instant_values._process_number_value("invalid", "test")
        assert result == (None, None, None, None, None)

    @pytest.mark.asyncio
    async def test_set_value_request_handler_failure(self, instant_values):
        """Test setting value when request handler fails."""
        instant_values._request_handler.set_value.return_value = False
        
        result = await instant_values.set_number("target_ph", 7.2)
        assert result is False

    def test_get_value_missing_mapping(self, instant_values):
        """Test getting value with missing mapping."""
        value = instant_values._get_value("nonexistent")
        assert value is None

    def test_get_value_no_raw_data(self, instant_values):
        """Test getting value when no raw data exists."""
        # Add mapping for key that doesn't exist in device data
        instant_values._mapping["missing"] = {"type": "sensor", "key": "w_missing"}
        
        value = instant_values._get_value("missing")
        assert value is None

    def test_get_value_unknown_type(self, instant_values):
        """Test getting value with unknown type."""
        instant_values._mapping["unknown"] = {"type": "unknown", "key": "w_1eommf39k"}
        
        value = instant_values._get_value("unknown")
        assert value is None
