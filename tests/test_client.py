"""Tests for Client for Async API client for SEKO Pooldose."""

import pytest
from pooldose.client import PooldoseClient
from pooldose.request_handler import RequestStatus

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
    status, static = client.static_values()
    assert status == RequestStatus.SUCCESS
    assert static.sensor_name == "TestDevice"
    assert static.sensor_serial_number == "12345"
    assert static.sensor_device_id == "12345_DEVICE"
    assert static.sensor_model == "TestModel"
    assert static.sensor_model_id == "TESTMODELID"

def test_get_model_mapping_file_not_found():
    """Test _get_model_mapping returns UNKNOWN_ERROR if file not found."""
    client = PooldoseClient("localhost")
    client.device_info = {
        "MODEL_ID": "DOESNOTEXIST",
        "FW_CODE": "000000"
    }
    status, mapping = client.get_model_mapping()
    assert status != RequestStatus.SUCCESS
    assert mapping is None
