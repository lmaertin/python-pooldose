"""Tests for Static Values for Async API client for SEKO Pooldose."""

from pooldose.values.static_values import StaticValues


def test_static_values_properties(mock_device_info):
    """Test all StaticValues properties."""
    static = StaticValues(mock_device_info)
    assert static.sensor_name == "Test Device"
    assert static.sensor_serial_number == "TEST123"
    assert static.sensor_device_id == "TEST123_DEVICE"
    assert static.sensor_model == "PDPR1H1HAW100"
    assert static.sensor_model_id == "PDPR1H1HAW100"
    assert static.sensor_ownerid == "Owner1"
    assert static.sensor_groupname == "GroupA"
    assert static.sensor_fw_version == "1.0.0"
    assert static.sensor_sw_version == "SW1.0"
    assert static.sensor_api_version == "v1/"
    assert static.sensor_fw_code == "FW539187"
    assert static.sensor_mac == "00:11:22:33:44:55"
    assert static.sensor_ip == "192.168.1.100"
    assert static.sensor_wifi_ssid == "TestSSID"
    assert static.sensor_wifi_key == "TestWifiKey"
    assert static.sensor_ap_ssid == "TestAPSSID"
    assert static.sensor_ap_key == "TestAPKey"
