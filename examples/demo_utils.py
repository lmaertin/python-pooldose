#!/usr/bin/env python3
"""Utility functions for demo scripts."""

# pylint: disable=too-many-branches,too-many-locals


def _display_data_type(data_dict, type_name, title):
    """Helper function to display a specific data type."""
    if not data_dict:
        return

    print(f"\n{title}:")
    for key, data in data_dict.items():
        formatted_key = key.replace('_', ' ').title()

        if type_name in ["sensor", "number"]:
            value = data.get("value")
            unit = data.get("unit")

            if type_name == "number":
                min_val = data.get("min")
                max_val = data.get("max")
                value_str = f"{value} {unit}" if unit else str(value)
                print(f"  {formatted_key}: {value_str} (Range: {min_val}-{max_val})")
            else:
                value_str = f"{value} {unit}" if unit else str(value)
                print(f"  {formatted_key}: {value_str}")

        elif type_name in ["switch", "binary_sensor"]:
            value = data.get("value")
            if type_name == "binary_sensor":
                status = "ACTIVE" if value else "OK"
            else:
                status = "ON" if value else "OFF"
            print(f"  {formatted_key}: {status}")

        elif type_name == "select":
            value = data.get("value")
            print(f"  {formatted_key}: {value}")


def display_structured_data(structured_data):
    """Display structured data in a formatted way."""
    _display_data_type(structured_data.get("sensor", {}), "sensor", "Sensor Values")
    _display_data_type(structured_data.get("binary_sensor", {}), "binary_sensor", "Alarms & Status")
    _display_data_type(structured_data.get("number", {}), "number", "Setpoints")
    _display_data_type(structured_data.get("switch", {}), "switch", "Switches")
    _display_data_type(structured_data.get("select", {}), "select", "Settings")


def display_static_values(static_values):
    """Display static device values."""
    print("\nDevice Information:")
    print(f"  Name: {static_values.sensor_name}")
    print(f"  Serial: {static_values.sensor_serial_number}")
    print(f"  Model: {static_values.sensor_model}")
    print(f"  Firmware: {static_values.sensor_fw_version}")
