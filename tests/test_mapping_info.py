"""Tests for MappingInfo for async API client for SEKO Pooldose."""

import pytest
from pooldose.mappings.mapping_info import MappingInfo, SensorMapping, SelectMapping
from pooldose.request_handler import RequestStatus

async def test_load_file_not_found():
    """Test MappingInfo.load returns UNKNOWN_ERROR if file not found."""
    mapping_info = await MappingInfo.load("DOESNOTEXIST", "000000")
    assert mapping_info.status != RequestStatus.SUCCESS
    assert mapping_info.mapping is None

def test_available_types_and_sensors():
    """Test available_types and available_sensors return correct structure."""
    # Prepare fake mapping
    fake_mapping = {
        "temp_actual": {"key": "k1", "type": "sensor"},
        "ph_actual": {"key": "k2", "type": "sensor", "conversion": {"a": "b"}},
        "sel1": {"key": "k3", "type": "select", "conversion": {"x": "y"}, "options": {"o": 1}},
    }
    mapping_info = MappingInfo(mapping=fake_mapping, status=RequestStatus.SUCCESS)

    types = mapping_info.available_types()
    assert "sensor" in types
    assert "select" in types
    assert "temp_actual" in types["sensor"]
    assert "ph_actual" in types["sensor"]
    assert "sel1" in types["select"]

    sensors = mapping_info.available_sensors()
    assert "temp_actual" in sensors
    assert isinstance(sensors["temp_actual"], SensorMapping)
    assert sensors["temp_actual"].key == "k1"
    assert sensors["temp_actual"].conversion is None

    assert "ph_actual" in sensors
    assert sensors["ph_actual"].conversion == {"a": "b"}

def test_available_selects():
    """Test available_selects returns correct SelectMapping objects."""
    fake_mapping = {
        "sel1": {"key": "k3", "type": "select", "conversion": {"x": "y"}, "options": {"o": 1}},
    }
    mapping_info = MappingInfo(mapping=fake_mapping, status=RequestStatus.SUCCESS)
    selects = mapping_info.available_selects()
    assert "sel1" in selects
    select = selects["sel1"]
    assert isinstance(select, SelectMapping)
    assert select.key == "k3"
    assert select.conversion == {"x": "y"}
    assert select.options == {"o": 1}

def test_available_selects_missing_fields():
    """Test available_selects raises KeyError if conversion/options missing."""
    fake_mapping = {
        "sel1": {"key": "k3", "type": "select", "conversion": {"x": "y"}},  # missing options
        "sel2": {"key": "k4", "type": "select", "options": {"o": 1}},       # missing conversion
    }
    mapping_info = MappingInfo(mapping=fake_mapping, status=RequestStatus.SUCCESS)
    with pytest.raises(KeyError):
        _ = mapping_info.available_selects()


class TestPDPR1H1HAW100FW539187Mapping:
    """Tests for the PDPR1H1HAW100 FW539187 mapping file."""

    MODEL_ID = "PDPR1H1HAW100"
    FW_CODE = "539187"

    @pytest.fixture
    async def mapping(self):
        """Load the mapping file."""
        info = await MappingInfo.load(self.MODEL_ID, self.FW_CODE)
        assert info.status == RequestStatus.SUCCESS
        assert info.mapping is not None
        return info

    async def test_load_success(self, mapping):
        """Test mapping file loads successfully."""
        assert mapping.status == RequestStatus.SUCCESS

    async def test_total_entity_count(self, mapping):
        """Test total number of mapped entities."""
        assert len(mapping.mapping) == 54

    async def test_entity_type_counts(self, mapping):
        """Test entity count per type."""
        types = mapping.available_types()
        assert len(types.get("sensor", [])) == 19
        assert len(types.get("binary_sensor", [])) == 23
        assert len(types.get("number", [])) == 8
        assert len(types.get("switch", [])) == 3
        assert len(types.get("select", [])) == 1

    async def test_new_alarm_binary_sensors(self, mapping):
        """Test new alarm binary sensors are present."""
        types = mapping.available_types()
        expected_alarms = [
            "alarm_ofa2_ph",
            "alarm_ofa2_orp",
            "alarm_ofa2_cl",
            "alarm_water_too_cold",
            "alarm_water_too_hot",
            "alarm_ph_too_low",
            "alarm_ph_too_high",
            "alarm_cl_too_low_orp",
            "alarm_cl_too_high_orp",
            "alarm_cl_too_high",
            "alarm_system_standby",
            "circulation_pump_status",
            "power_on_delay_status",
            "flow_delay_status",
        ]
        for alarm in expected_alarms:
            assert alarm in types["binary_sensor"], f"Missing binary_sensor: {alarm}"

    async def test_new_sensors_with_conversions(self, mapping):
        """Test new sensors with conversion dictionaries."""
        sensors = mapping.available_sensors()
        sensors_with_conversion = [
            "peristaltic_cl_dosing",
            "device_config",
            "temperature_unit",
        ]
        for name in sensors_with_conversion:
            assert name in sensors, f"Missing sensor: {name}"
            assert sensors[name].conversion is not None, f"Missing conversion for {name}"
            assert len(sensors[name].conversion) >= 2, f"Conversion too small for {name}"

    async def test_new_number_entities(self, mapping):
        """Test new number entities are present."""
        types = mapping.available_types()
        expected_numbers = [
            "time_off_ph_dosing",
            "time_off_orp_dosing",
            "time_off_cl_dosing",
            "power_on_delay_timer",
            "flow_delay_timer",
        ]
        for number in expected_numbers:
            assert number in types["number"], f"Missing number: {number}"

    async def test_select_entity(self, mapping):
        """Test select entity with options and conversion."""
        selects = mapping.available_selects()
        assert "water_meter_unit" in selects
        assert len(selects["water_meter_unit"].options) == 2
        assert len(selects["water_meter_unit"].conversion) == 2
