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
