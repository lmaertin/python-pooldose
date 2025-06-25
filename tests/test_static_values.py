"""Tests for Static Values for Async API client for SEKO Pooldose."""

from pooldose.values.static_values import StaticValues

def test_static_values_properties():
    """Test all StaticValues properties."""
    device_info = {
        "NAME": "TestName",
        "SERIAL_NUMBER": "SN123",
        "DEVICE_ID": "ID123",
        "MODEL": "ModelX",
        "MODEL_ID": "MID123",
        "OWNERID": "Owner1",
        "GROUPNAME": "GroupA",
        "FW_VERSION": "FW1.0",
        "SW_VERSION": "SW1.0",
        "API_VERSION": "v1/",
        "FW_CODE": "FCODE",
        "MAC": "00:11:22:33:44:55",
        "IP": "192.168.1.2",
        "WIFI_SSID": "SSID",
        "WIFI_KEY": "WKEY",
        "AP_SSID": "APSSID",
        "AP_KEY": "APKEY"
    }
    static = StaticValues(device_info)
    assert static.sensor_name == "TestName"
    assert static.sensor_serial_number == "SN123"
    assert static.sensor_device_id == "ID123"
    assert static.sensor_model == "ModelX"
    assert static.sensor_model_id == "MID123"
    assert static.sensor_ownerid == "Owner1"
    assert static.sensor_groupname == "GroupA"
    assert static.sensor_fw_version == "FW1.0"
    assert static.sensor_sw_version == "SW1.0"
    assert static.sensor_api_version == "v1/"
    assert static.sensor_fw_code == "FCODE"
    assert static.sensor_mac == "00:11:22:33:44:55"
    assert static.sensor_ip == "192.168.1.2"
    assert static.sensor_wifi_ssid == "SSID"
    assert static.sensor_wifi_key == "WKEY"
    assert static.sensor_ap_ssid == "APSSID"
    assert static.sensor_ap_key == "APKEY"
