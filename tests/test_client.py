"""Tests for Client for Async API client for SEKO Pooldose."""

import pytest
from pooldose.client import PooldoseClient
from pooldose.request_handler import RequestStatus
from pooldose.mappings.mapping_info import MappingInfo

@pytest.mark.asyncio
async def test_static_values():
    """Test static_values returns correct status and object."""
    client = PooldoseClient("localhost")
    client.device_info = {
        "NAME": "TestDevice",
        "SERIAL_NUMBER": "12345",
        "DEVICE_ID": "12345_DEVICE",
        "MODEL": "TestModel",
        "MODEL_ID": "TESTMODELID",
        "FW_CODE": "000000",
    }
    # MappingInfo is not required for static_values
    status, static = client.static_values()
    assert status == RequestStatus.SUCCESS
    assert static.sensor_name == "TestDevice"
    assert static.sensor_serial_number == "12345"
    assert static.sensor_device_id == "12345_DEVICE"
    assert static.sensor_model == "TestModel"
    assert static.sensor_model_id == "TESTMODELID"

async def test_get_model_mapping_file_not_found():
    """Test get_model_mapping returns UNKNOWN_ERROR if file not found."""
    client = PooldoseClient("localhost")
    client.device_info = {
        "MODEL_ID": "DOESNOTEXIST",
        "FW_CODE": "000000"
    }
    # Use MappingInfo directly, as get_model_mapping is deprecated
    mapping_info = client._mapping_info = None  # Simulate not loaded
    # Simulate the MappingInfo.load call
    mapping_info = await MappingInfo.load("DOESNOTEXIST", "000000")
    assert mapping_info.status != RequestStatus.SUCCESS
    assert mapping_info.mapping is None
