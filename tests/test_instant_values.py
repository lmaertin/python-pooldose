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

def test_ph_values_no_units():
    """Test that pH values return None for units even when device provides units."""
    # Device data with pH values that have units provided by device
    device_raw_data = {
        "PDPR1H1HAW100_FW539187_w_1ekeigkin": {
            "current": 7.2,
            "magnitude": ["pH", "PH_UNIT"],  # Device incorrectly provides pH unit
        },
        "PDPR1H1HAW100_FW539187_w_1ekeiqfat": {
            "current": 7.5,
            "magnitude": ["pH", "PH_UNIT"],  # Device incorrectly provides pH unit for target
            "absMin": 6.0,
            "absMax": 8.5,
            "resolution": 0.1,
        },
        "PDPR1H1HAW100_FW539187_w_1eo1ttmft": {
            "current": 7.1,
            "magnitude": ["pH", "PH_UNIT"],  # Device incorrectly provides pH unit for OFA
        },
        "PDPR1H1HAW100_FW539187_w_1eklhs3b4": {
            "current": 0.02,
            "magnitude": ["pH", "PH_UNIT"],  # pH calibration offset
        },
        "PDPR1H1HAW100_FW539187_w_1eklhs65u": {
            "current": 1.0,
            "magnitude": ["pH", "PH_UNIT"],  # pH calibration slope
        },
        "PDPR1H1HAW100_FW539187_w_1eommf39k": {
            "current": 27.5,
            "magnitude": ["°C", "CDEG"],  # Temperature should keep its unit
        }
    }
    
    mapping = {
        "ph": {"key": "w_1ekeigkin", "type": "sensor"},
        "ph_target": {"key": "w_1ekeiqfat", "type": "number"},
        "ofa_ph_value": {"key": "w_1eo1ttmft", "type": "sensor"},
        "ph_calibration_offset": {"key": "w_1eklhs3b4", "type": "sensor"},
        "ph_calibration_slope": {"key": "w_1eklhs65u", "type": "sensor"},
        "temperature": {"key": "w_1eommf39k", "type": "sensor"},
    }
    
    prefix = "PDPR1H1HAW100_FW539187_"
    instant = InstantValues(device_raw_data, mapping, prefix, "TESTDEVICE", None)
    
    # pH sensor should have None unit
    ph_value = instant["ph"]
    assert ph_value[0] == 7.2
    assert ph_value[1] is None
    
    # pH target (number) should have None unit
    ph_target = instant["ph_target"]
    assert ph_target[0] == 7.5
    assert ph_target[1] is None
    
    # OFA pH value should have None unit
    ofa_ph = instant["ofa_ph_value"]
    assert ofa_ph[0] == 7.1
    assert ofa_ph[1] is None
    
    # pH calibration values should have None unit
    ph_offset = instant["ph_calibration_offset"]
    assert ph_offset[0] == 0.02
    assert ph_offset[1] is None
    
    ph_slope = instant["ph_calibration_slope"]
    assert ph_slope[0] == 1.0
    assert ph_slope[1] is None
    
    # Temperature should keep its unit (verify we didn't break other sensors)
    temp_value = instant["temperature"]
    assert temp_value[0] == 27.5
    assert temp_value[1] == "°C"
