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


class TestDoubleSpaMapping:
    """Tests for the POOLDOSE DOUBLE SPA mapping file (PDPR1H04AW100_FW539292)."""

    @pytest.mark.asyncio
    async def test_load_double_spa_mapping(self):
        """Test that the DOUBLE SPA mapping file loads successfully."""
        mapping_info = await MappingInfo.load("PDPR1H04AW100", "539292")
        assert mapping_info.status == RequestStatus.SUCCESS
        assert mapping_info.mapping is not None

    @pytest.mark.asyncio
    async def test_double_spa_sensors(self):
        """Test that expected sensors are present in the DOUBLE SPA mapping."""
        mapping_info = await MappingInfo.load("PDPR1H04AW100", "539292")
        sensors = mapping_info.available_sensors()

        # Core measurement sensors
        expected_sensors = [
            "temperature", "ph", "orp", "cl",
            "ph_type_dosing", "peristaltic_ph_dosing",
            "orp_type_dosing", "peristaltic_orp_dosing",
            "peristaltic_cl_dosing",
            "ph_calibration_type", "ph_calibration_offset", "ph_calibration_slope",
            "orp_calibration_type", "orp_calibration_offset", "orp_calibration_slope",
            "cl_calibration_type", "cl_calibration_offset", "cl_calibration_slope",
            "circulation_pump_status",
            "ofa_ph_time", "ofa_orp_time", "ofa_cl_time",
            "device_config", "temperature_unit",
            "power_on_delay_status", "flow_delay_status",
        ]
        for name in expected_sensors:
            assert name in sensors, f"Missing sensor: {name}"

    @pytest.mark.asyncio
    async def test_double_spa_sensor_conversions(self):
        """Test that sensors with conversions have the correct label prefix."""
        mapping_info = await MappingInfo.load("PDPR1H04AW100", "539292")
        sensors = mapping_info.available_sensors()

        # pH type dosing should have conversion with PDPR1H04AW100_FW539292 prefix
        ph_type = sensors["ph_type_dosing"]
        assert ph_type.conversion is not None
        assert "|PDPR1H04AW100_FW539292_LABEL_w_1eklg44ro_ACID|" in ph_type.conversion
        assert ph_type.conversion["|PDPR1H04AW100_FW539292_LABEL_w_1eklg44ro_ACID|"] == "acid"

        # Peristaltic CL dosing - unique to DOUBLE SPA
        cl_dosing = sensors["peristaltic_cl_dosing"]
        assert cl_dosing.conversion is not None
        assert len(cl_dosing.conversion) == 5  # off, proportional, on/off, timed, cycle

    @pytest.mark.asyncio
    async def test_double_spa_binary_sensors(self):
        """Test that expected binary sensors are present, including DOUBLE SPA extras."""
        mapping_info = await MappingInfo.load("PDPR1H04AW100", "539292")
        binary_sensors = mapping_info.available_binary_sensors()

        # Standard alarms (shared with PDPR1H1HAW100)
        standard_alarms = [
            "pump_alarm", "ph_level_alarm", "orp_level_alarm",
            "flow_rate_alarm", "relay_alarm", "relay_aux1", "relay_aux2",
            "alarm_ofa_ph", "alarm_ofa_orp",
        ]
        for name in standard_alarms:
            assert name in binary_sensors, f"Missing binary_sensor: {name}"

        # DOUBLE SPA-specific alarms
        double_spa_alarms = [
            "cl_level_alarm",
            "alarm_ofa2_ph", "alarm_ofa2_orp",
            "alarm_ofa_cl", "alarm_ofa2_cl",
            "alarm_water_too_cold", "alarm_water_too_hot",
            "alarm_ph_too_low", "alarm_ph_too_high",
            "alarm_cl_too_low_orp", "alarm_cl_too_high_orp",
            "alarm_cl_too_low", "alarm_cl_too_high",
            "alarm_system_standby",
            "circulation_pump_status",
            "power_on_delay_status",
            "flow_delay_status",
        ]
        for name in double_spa_alarms:
            assert name in binary_sensors, f"Missing DOUBLE SPA binary_sensor: {name}"

    @pytest.mark.asyncio
    async def test_double_spa_numbers(self):
        """Test that expected number entities are present."""
        mapping_info = await MappingInfo.load("PDPR1H04AW100", "539292")
        numbers = mapping_info.available_numbers()

        expected_numbers = [
            "ph_target", "orp_target", "cl_target",
            "time_on_ph_dosing", "time_off_ph_dosing",
            "time_on_orp_dosing", "time_off_orp_dosing",
            "time_on_cl_dosing", "time_off_cl_dosing",
            "power_on_delay_timer", "flow_delay_timer",
        ]
        for name in expected_numbers:
            assert name in numbers, f"Missing number: {name}"

    @pytest.mark.asyncio
    async def test_double_spa_switches(self):
        """Test that expected switch entities are present."""
        mapping_info = await MappingInfo.load("PDPR1H04AW100", "539292")
        switches = mapping_info.available_switches()

        expected_switches = ["pause_dosing", "pump_monitoring", "frequency_input"]
        for name in expected_switches:
            assert name in switches, f"Missing switch: {name}"

    @pytest.mark.asyncio
    async def test_double_spa_selects(self):
        """Test that select entities are present with correct options."""
        mapping_info = await MappingInfo.load("PDPR1H04AW100", "539292")
        selects = mapping_info.available_selects()

        assert "water_meter_unit" in selects
        wmu = selects["water_meter_unit"]
        assert wmu.key == "w_1eklinki6"
        assert "0" in wmu.options
        assert "1" in wmu.options
        assert "PDPR1H04AW100_FW539292_COMBO_w_1eklinki6_M_" in wmu.conversion
        assert wmu.conversion["PDPR1H04AW100_FW539292_COMBO_w_1eklinki6_M_"] == "m3"

    @pytest.mark.asyncio
    async def test_double_spa_entity_counts(self):
        """Test the total entity counts for the DOUBLE SPA mapping."""
        mapping_info = await MappingInfo.load("PDPR1H04AW100", "539292")
        types = mapping_info.available_types()

        assert len(types.get("sensor", [])) == 26
        assert len(types.get("binary_sensor", [])) == 23
        assert len(types.get("number", [])) == 11
        assert len(types.get("switch", [])) == 3
        assert len(types.get("select", [])) == 1
