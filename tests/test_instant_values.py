"""Tests for Instant Values for Async API client for SEKO Pooldose."""

from pooldose.values.instant_values import InstantValues

# pylint: disable=line-too-long

def test_instant_values_properties_and_methods():
    """Test InstantValues properties and basic method signatures."""
    # Beispielhafte Testdaten (minimal)
    device_raw_data = {
        "PDPR1H1HAW100_FW539187_w_1eommf39k": {
        "current": 27.5,
        "resolution": 0.1,
        "magnitude": [
          "°C",
          "CDEG"
        ],
        "absMin": 0,
        "absMax": 55,
        "minT": 10,
        "maxT": 38
      },
    }
    mapping = {
        "temperature": {"key": "w_1eommf39k", "type": "sensor"},
    }

    prefix = "PDPR1H1HAW100_FW539187_"
    instant = InstantValues(device_raw_data, mapping, prefix, "TESTDEVICE", None)

    assert [instant.get_sensors()["temperature"][0],instant.get_sensors()["temperature"][1]]  == [27.5, "°C"]

def test_instant_values_missing_keys():
    """Test InstantValues with missing keys in device_raw_data."""
    device_raw_data = {}
    mapping = {
        "temperature": {"key": "w_1eommf39k", "type": "sensor"},
    }
    prefix = ""
    device_id = "TESTDEVICE"
    request_handler = None

    instant = InstantValues(device_raw_data, mapping, prefix, device_id, request_handler)
    assert "w_1eommf39k" not in instant.get_sensors()

def test_instant_values_missing_mapping():
    """Test that InstantValues returns None when a mapping for a requested attribute is missing."""
    device_raw_data = {
        "sensor_temperature": [25.0, "°C"],
    }
    mapping = {
        "temperature": {"key": "sensor_temperature", "type": "sensor"},
    }
    prefix = ""
    device_id = "TESTDEVICE"
    request_handler = None

    instant = InstantValues(device_raw_data, mapping, prefix, device_id, request_handler)
    assert "ph" not in instant.get_sensors() # Kein Mapping für ph_actual vorhanden

def test_instant_values_with_suffix_mapping():
    """Test the InstantValues class for correct mapping of sensor values using suffix-based keys."""
    device_raw_data = {
        "PDPR1H1HAW100_FW539187_w_1eommf39k": {"current": 27.5},
        "PDPR1H1HAW100_FW539187_w_1ekeigkin": {"current": 7},
        "PDPR1H1HAW100_FW539187_w_1eklenb23": {"current": 597},
    }
    mapping = {
        "temperature": {"key": "w_1eommf39k", "type": "sensor"},
        "ph": {"key": "w_1ekeigkin", "type": "sensor"},
        "orp": {"key": "w_1eklenb23", "type": "sensor"},
    }
    prefix = "PDPR1H1HAW100_FW539187_"
    instant = InstantValues(device_raw_data, mapping, prefix, "TESTDEVICE", None)
    assert instant.get_sensors()["temperature"][0] == 27.5
    assert instant.get_sensors()["ph"][0] == 7
    assert instant.get_sensors()["orp"][0] == 597
