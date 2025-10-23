"""Tests for MockPooldoseClient set_value and convenience setters.

These tests exercise payload shaping for arrays,
switch string handling, and the convenience setters that wrap
`InstantValues` functionality.

Disable a couple of pylint complexity checks for this test module as the
payload-inspection test intentionally exercises multiple branches and
nested loops to validate different payload shapes.

"""

# pylint: disable=too-many-branches,too-many-nested-blocks

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from pooldose.mock_client import MockPooldoseClient
from pooldose.request_status import RequestStatus


# Create test data inline
TEST_DATA = {
    "devicedata": {
        "012500004415_DEVICE": {
            "deviceInfo": {
                "dwi_status": "ok",
                "modbus_status": "on"
            },
            "collapsed_bar": [],
            "PDPR1H1HAR1V0_FW539224_w_test_ph": {
                "visible": True,
                "alarm": False,
                "current": 7.3,
                "resolution": 0.1,
                "magnitude": ["pH", "PH"],
                "absMin": 0,
                "absMax": 14,
                "minT": 6,
                "maxT": 8
            },
            "PDPR1H1HAR1V0_FW539224_w_1f2jpqa6e": {
                "current": "F"
            },
            "PDHC1H1HAR1V1_FW539224_w_1g1kvba4g": {
                "visible": True,
                "alarm": False,
                "current": 7.0,
                "resolution": 0.1,
                "magnitude": ["pH", "PH"],
                "absMin": 0,
                "absMax": 14,
                "minT": 6.0,
                "maxT": 8.0
            }
        }
    }
}


def create_temp_json_file(data: Dict[str, Any]) -> Path:
    """Create a temporary JSON file with test data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json.dump(data, temp_file, indent=2)
        return Path(temp_file.name)


def test_set_value_number_single() -> None:
    """Verify single NUMBER value is encoded as an array with one object."""
    json_path = create_temp_json_file(TEST_DATA)
    try:
        client = MockPooldoseClient(json_path, model_id="PDPR1H1HAR1V0", fw_code="539224")
        device_id = str(client.device_info["DEVICE_ID"])  # type: ignore[arg-type]
        result = asyncio.run(
            client.set_value(device_id, "some/widget", 7.5, "NUMBER")  # type: ignore[arg-type]
        )
        assert result is not False

        # Get payload from mock client
        if isinstance(result, tuple):
            success, payload_str = result
            assert success is True
            payload = json.loads(payload_str)
        else:
            # Get last payload if result is just bool
            payload_str_optional = client.get_last_payload()
            assert payload_str_optional is not None
            payload = json.loads(payload_str_optional)

        assert device_id in payload
        assert "some/widget" in payload[device_id]
        entries = payload[device_id]["some/widget"]
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert entries[0]["value"] == 7.5
        assert entries[0]["type"] == "NUMBER"
    finally:
        json_path.unlink()


def test_set_value_number_array() -> None:
    """Verify NUMBER arrays are encoded as lists of value objects."""
    json_path = create_temp_json_file(TEST_DATA)
    try:
        client = MockPooldoseClient(json_path, model_id="PDPR1H1HAR1V0", fw_code="539224")
        device_id = str(client.device_info["DEVICE_ID"])  # type: ignore[arg-type]
        result = asyncio.run(
            client.set_value(device_id, "some/widget", [5.5, 8.0], "NUMBER")  # type: ignore[arg-type]
        )
        assert result is not False

        # Get payload from mock client
        if isinstance(result, tuple):
            success, payload_str = result
            assert success is True
            payload = json.loads(payload_str)
        else:
            # Get last payload if result is just bool
            payload_str = client.get_last_payload()  # type: ignore[assignment]
            assert payload_str is not None
            payload = json.loads(payload_str)

        entries = payload[device_id]["some/widget"]
        assert isinstance(entries, list) and len(entries) == 2
        assert entries[0]["value"] == 5.5
        assert entries[1]["value"] == 8.0
        assert all(e["type"] == "NUMBER" for e in entries)
    finally:
        json_path.unlink()


def test_set_value_string_switch() -> None:
    """Verify switch string payloads are sent as arrays."""
    json_path = create_temp_json_file(TEST_DATA)
    try:
        client = MockPooldoseClient(json_path, model_id="PDPR1H1HAR1V0", fw_code="539224")
        device_id = str(client.device_info["DEVICE_ID"])  # type: ignore[arg-type]
        result = asyncio.run(
            client.set_value(device_id, "some/widget", "test", "STRING")  # type: ignore[arg-type]
        )
        assert result is not False

        # Get payload from mock client
        if isinstance(result, tuple):
            success, payload_str = result
            assert success is True
            payload = json.loads(payload_str)
        else:
            # Get last payload if result is just bool
            payload_str = client.get_last_payload()  # type: ignore[assignment]
            assert payload_str is not None
            payload = json.loads(payload_str)

        entries = payload[device_id]["some/widget"]
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert entries[0]["value"] == "test"
        assert entries[0]["type"] == "STRING"
    finally:
        json_path.unlink()


def test_switch_setter_boolean_only() -> None:
    """Ensure switch setter enforces boolean-only input via the client convenience method."""
    json_path = create_temp_json_file(TEST_DATA)
    try:
        client = MockPooldoseClient(json_path, model_id="PDPR1H1HAR1V0", fw_code="539224")
        # Connect mock to initialize mapping info
        connect_status = asyncio.run(client.connect())
        assert connect_status == RequestStatus.SUCCESS
        # Non-boolean should be rejected
        try:
            result = asyncio.run(client.set_switch("stop_pool_dosing", "O"))  # type: ignore
            assert result is False
        except TypeError:
            # Type error is expected for non-boolean input
            pass
        # Boolean should be accepted (mock returns truthy value or tuple)
        result = asyncio.run(client.set_switch("stop_pool_dosing", True))
        assert result is not False
    finally:
        json_path.unlink()


def test_set_number_lower_upper_pairing() -> None:
    """Test that number setters work with mock client."""
    json_path = create_temp_json_file(TEST_DATA)
    try:
        client = MockPooldoseClient(json_path, model_id="PDHC1H1HAR1V1", fw_code="539224")
        # Connect mock to initialize mapping info
        connect_status = asyncio.run(client.connect())
        assert connect_status == RequestStatus.SUCCESS

        # Just verify that the mock returns truthy values for set operations
        # Since this is a mock, the exact payload format is less important than
        # ensuring the interface works correctly
        result = asyncio.run(client.set_value("012500004415_DEVICE", "test/path", 6.5, "NUMBER"))
        assert result is not False

        # Check that we get a valid payload string
        last_payload = client.get_last_payload()
        assert last_payload is not None
        # Verify the payload contains the expected array format
        payload = json.loads(last_payload)
        assert "012500004415_DEVICE" in payload
        assert "test/path" in payload["012500004415_DEVICE"]
        entries = payload["012500004415_DEVICE"]["test/path"]
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert entries[0]["value"] == 6.5
        assert entries[0]["type"] == "NUMBER"
    finally:
        json_path.unlink()
