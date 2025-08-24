"""Common test fixtures and mocks for the pooldose test suite."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pooldose.request_status import RequestStatus
from pooldose.values.instant_values import InstantValues


@pytest.fixture
def mock_request_handler():
    """Create a mock request handler."""
    handler = AsyncMock()
    handler.api_version = "v1/"
    handler.connect.return_value = RequestStatus.SUCCESS
    handler.set_value.return_value = True
    return handler


@pytest.fixture
def mock_device_info():
    """Create mock device information with all fields."""
    return {
        "NAME": "Test Device",
        "SERIAL_NUMBER": "TEST123",
        "DEVICE_ID": "TEST123_DEVICE",
        "MODEL": "PDPR1H1HAW100",
        "MODEL_ID": "PDPR1H1HAW100",
        "OWNERID": "Owner1",
        "GROUPNAME": "GroupA",
        "FW_VERSION": "1.0.0",
        "SW_VERSION": "SW1.0",
        "API_VERSION": "v1/",
        "FW_CODE": "FW539187",
        "MAC": "00:11:22:33:44:55",
        "IP": "192.168.1.100",
        "WIFI_SSID": "TestSSID",
        "WIFI_KEY": "TestWifiKey",
        "AP_SSID": "TestAPSSID",
        "AP_KEY": "TestAPKey"
    }


@pytest.fixture
def mock_device_data():
    """Create mock device data for InstantValues."""
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
def mock_raw_data():
    """Create mock raw device data for client tests."""
    return {
        "devicedata": {
            "TEST123_DEVICE": {
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
                }
            }
        }
    }


@pytest.fixture
def mock_debug_config():
    """Create mock debug config response."""
    return {
        "GATEWAY": {
            "DID": "TEST123",
            "NAME": "Test Device",
            "FW_REL": "1.0.0"
        },
        "DEVICES": [{
            "DID": "TEST123_DEVICE",
            "NAME": "PDPR1H1HAW100",
            "PRODUCT_CODE": "PDPR1H1HAW100",
            "FW_REL": "1.0.0",
            "FW_CODE": "FW539187"
        }]
    }


@pytest.fixture
def mock_mapping_info(mock_mapping):  # pylint: disable=redefined-outer-name
    """Create mock mapping info object."""
    mapping_info = MagicMock()
    mapping_info.mapping = mock_mapping
    return mapping_info


@pytest.fixture
def instant_values_fixture(  # pylint: disable=redefined-outer-name
    mock_device_data, mock_mapping, mock_request_handler
):
    """Create InstantValues instance for testing."""
    return InstantValues(
        device_data=mock_device_data,
        mapping=mock_mapping,
        prefix="PDPR1H1HAW100_FW539187_",
        device_id="TEST123_DEVICE",
        request_handler=mock_request_handler
    )


@pytest.fixture
def mock_structured_data():
    """Create mock structured data for testing."""
    return {
        "sensor": {
            "temperature": {"value": 25.5, "unit": "°C"},
            "ph": {"value": 7.2, "unit": None}
        },
        "number": {
            "target_ph": {"value": 7.0, "unit": None, "min": 6.0, "max": 8.0, "step": 0.1}
        },
        "switch": {
            "pump_switch": {"value": True}
        },
        "binary_sensor": {
            "alarm_ph": {"value": False}
        },
        "select": {
            "water_unit": {"value": "m³"}
        }
    }


@pytest.fixture
def complete_client_setup(  # pylint: disable=redefined-outer-name
    mock_request_handler, mock_device_info, mock_mapping_info,
    mock_raw_data, mock_structured_data
):
    """Create a complete setup for client testing with all dependencies."""
    return {
        "request_handler": mock_request_handler,
        "device_info": mock_device_info,
        "mapping_info": mock_mapping_info,
        "raw_data": mock_raw_data,
        "structured_data": mock_structured_data
    }
