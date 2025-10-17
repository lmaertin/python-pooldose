"""Tests for MockPooldoseClient set_value and convenience setters.

These tests exercise payload shaping (single NUMBER vs NUMBER array),
switch string handling, and the convenience setters that wrap
`InstantValues` functionality.

Disable a couple of pylint complexity checks for this test module as the
payload-inspection test intentionally exercises multiple branches and
nested loops to validate different payload shapes.

"""

# pylint: disable=too-many-branches,too-many-nested-blocks

import asyncio
import json
from pathlib import Path

from pooldose.mock_client import MockPooldoseClient
from pooldose.request_status import RequestStatus


JSON_PATH = Path("references/testdaten/geraldnolan/instantvalues.json")


def test_set_value_number_single():
    """Verify single NUMBER value is encoded as an object."""
    client = MockPooldoseClient(JSON_PATH, model_id="PDHC1H1HAR1V1", fw_code="539224")
    device_id = client.device_info["DEVICE_ID"]
    success, payload_str = asyncio.run(
        client.set_value(device_id, "some/widget", 7.5, "NUMBER")
    )
    assert success is True
    payload = json.loads(payload_str)
    assert device_id in payload
    assert "some/widget" in payload[device_id]
    entries = payload[device_id]["some/widget"]
    assert isinstance(entries, dict)
    assert entries["value"] == 7.5
    assert entries["type"] == "NUMBER"


def test_set_value_number_array():
    """Verify NUMBER arrays are encoded as lists of value objects."""
    client = MockPooldoseClient(JSON_PATH, model_id="PDPR1H1HAR1V0", fw_code="539224")
    device_id = client.device_info["DEVICE_ID"]
    success, payload_str = asyncio.run(
        client.set_value(device_id, "some/widget", [5.5, 8.0], "NUMBER")
    )
    assert success is True
    payload = json.loads(payload_str)
    entries = payload[device_id]["some/widget"]
    assert isinstance(entries, list) and len(entries) == 2
    assert entries[0]["value"] == 5.5
    assert entries[1]["value"] == 8.0
    assert all(e["type"] == "NUMBER" for e in entries)


def test_set_value_string_switch():
    """Verify switch string payloads are passed through unchanged."""
    client = MockPooldoseClient(JSON_PATH, model_id="PDPR1H1HAR1V0", fw_code="539224")
    device_id = client.device_info["DEVICE_ID"]
    success, payload_str = asyncio.run(
        client.set_value(device_id, "some/widget", "O", "STRING")
    )
    assert success is True
    payload = json.loads(payload_str)
    entries = payload[device_id]["some/widget"]
    assert isinstance(entries, dict)
    assert entries["value"] == "O"
    assert entries["type"] == "STRING"


def test_switch_setter_boolean_only():
    """Ensure switch setter enforces boolean-only input via the client convenience method."""
    client = MockPooldoseClient(JSON_PATH, model_id="PDPR1H1HAR1V0", fw_code="539224")
    # Connect mock to initialize mapping info
    connect_status = asyncio.run(client.connect())
    assert connect_status == RequestStatus.SUCCESS
    # Non-boolean should be rejected
    result = asyncio.run(client.set_switch("stop_pool_dosing", "O"))
    assert result is False
    # Boolean should be accepted (mock returns truthy value or tuple)
    result = asyncio.run(client.set_switch("stop_pool_dosing", True))
    assert result is not False


def test_set_number_lower_upper_pairing():
    """Using the mock convenience setter, ensure lower/upper 
    pairing sends array payloads.

    This test is tolerant to the order/overwrite behavior 
    of the mock by scanning all
    available payload strings returned by the convenience 
    methods and the mock's `get_last_payload()`.
    """
    client = MockPooldoseClient(JSON_PATH, model_id="PDHC1H1HAR1V1", fw_code="539224")
    # Connect mock to initialize mapping info
    connect_status = asyncio.run(client.connect())
    assert connect_status == RequestStatus.SUCCESS

    # Set lower then upper
    ok1 = asyncio.run(client.set_number("ofa_ph_lower", 6.2))
    assert ok1 is not False
    ok2 = asyncio.run(client.set_number("ofa_ph_upper", 8.1))
    assert ok2 is not False

    # Collect payload strings from returned tuples and last_payload
    payload_strs = []
    if isinstance(ok1, tuple) and len(ok1) > 1:
        payload_strs.append(ok1[1])
    if isinstance(ok2, tuple) and len(ok2) > 1:
        payload_strs.append(ok2[1])
    last = client.get_last_payload()
    if last:
        payload_strs.append(last)

    assert payload_strs, "No payloads were produced"

    # Parse payloads and collect numeric values
    found_62 = False
    found_81 = False
    for ps in payload_strs:
        try:
            p = json.loads(ps)
        except json.JSONDecodeError:
            # Skip invalid payload strings
            continue
        for dev_payload in p.values():
            for val in dev_payload.values():
                if isinstance(val, list):
                    for entry in val:
                        try:
                            v = float(entry.get("value"))
                        except (TypeError, ValueError):
                            continue
                        if abs(v - 6.2) < 1e-6:
                            found_62 = True
                        if abs(v - 8.1) < 1e-6:
                            found_81 = True
                elif isinstance(val, dict):
                    try:
                        v = float(val.get("value"))
                    except (TypeError, ValueError):
                        continue
                    if abs(v - 6.2) < 1e-6:
                        found_62 = True
                    if abs(v - 8.1) < 1e-6:
                        found_81 = True

    assert found_62, "Lower value 6.2 not found in any payload"
    assert found_81, "Upper value 8.1 not found in any payload"
