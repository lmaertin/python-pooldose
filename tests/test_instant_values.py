"""Tests for Instant Values for Async API client for SEKO Pooldose."""

from pooldose.instant_values import InstantValues

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
        "temp_actual": {"key": "w_1eommf39k", "type": "sensor"},
    }

    prefix = "PDPR1H1HAW100_FW539187_"
    instant = InstantValues(device_raw_data, mapping, prefix, "TESTDEVICE", None)

    assert [instant.sensor_temperature[0],instant.sensor_temperature[1]]  == [27.5, "°C"]

def test_instant_values_missing_keys():
    """Test InstantValues with missing keys in device_raw_data."""
    device_raw_data = {}
    mapping = {
        "sensor_temperature": "sensor_temperature",
        "sensor_ph": "sensor_ph",
    }
    prefix = ""
    device_id = "TESTDEVICE"
    request_handler = None

    instant = InstantValues(device_raw_data, mapping, prefix, device_id, request_handler)
    assert instant.sensor_temperature is None
    assert instant.sensor_ph is None

def test_instant_values_missing_mapping():
    """Test that InstantValues returns None when a mapping for a requested attribute is missing."""
    device_raw_data = {
        "sensor_temperature": [25.0, "°C"],
    }
    mapping = {
        "temp_actual": {"key": "sensor_temperature", "type": "sensor"},
    }
    prefix = ""
    device_id = "TESTDEVICE"
    request_handler = None

    instant = InstantValues(device_raw_data, mapping, prefix, device_id, request_handler)
    assert instant.sensor_ph is None  # Kein Mapping für ph_actual vorhanden

def test_instant_values_with_suffix_mapping():
    """Test the InstantValues class for correct mapping of sensor values using suffix-based keys."""
    device_raw_data = {
        "PDPR1H1HAW100_FW539187_w_1eommf39k": {"current": 27.5},
        "PDPR1H1HAW100_FW539187_w_1ekeigkin": {"current": 7},
        "PDPR1H1HAW100_FW539187_w_1eklenb23": {"current": 597},
    }
    mapping = {
        "temp_actual": {"key": "w_1eommf39k", "type": "sensor"},
        "ph_actual": {"key": "w_1ekeigkin", "type": "sensor"},
        "orp_actual": {"key": "w_1eklenb23", "type": "sensor"},
    }
    prefix = "PDPR1H1HAW100_FW539187_"
    instant = InstantValues(device_raw_data, mapping, prefix, "TESTDEVICE", None)
    assert instant.sensor_temperature[0] == 27.5
    assert instant.sensor_ph[0] == 7
    assert instant.sensor_orp[0] == 597
