#!/usr/bin/env python3
"""Demonstration for using the MockPooldoseClient with JSON files."""

import asyncio
import sys
from pathlib import Path
from pooldose.mock_client import MockPooldoseClient

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# pylint: disable=line-too-long

async def main(json_file_path: str = None) -> None:
    """Demonstrate all MockPooldoseClient calls."""
    print("Mock Pooldose Client Demo")
    print("=" * 50)
    
    # Use provided path or default test JSON file
    if json_file_path:
        json_file = Path(json_file_path)
        if not json_file.exists():
            print(f"Error: Specified JSON file not found: {json_file}")
            return
    else:
        print("Error: Please provide a valid JSON file path.")
        return

    try:
        # Initialize mock client
        print(f"Loading mock data from: {json_file}")
        client = MockPooldoseClient(
            json_file_path=json_file,
            include_sensitive_data=True
        )
        
        # Connect (load mapping data)
        print("\nConnecting to mock device...")
        status = await client.connect()
        
        if status.name != "SUCCESS":
            print(f"Error connecting to MockPooldoseClient: {status}")
            return

        print("Connected to mock Pooldose device")
        print(f"Device: {client.device_info.get('NAME', 'Unknown')}")
        print(f"Model: {client.device_info.get('MODEL', 'Unknown')}")

        # Static values
        print("\nFetching static values...")
        static_values_status, static_values = client.static_values()
        if static_values_status.name != "SUCCESS":
            print(f"Error fetching static values: {static_values_status}")
            return

        print("\nDevice Information:")
        print(f"  Name: {static_values.sensor_name}")
        print(f"  Serial: {static_values.sensor_serial_number}")
        print(f"  Model: {static_values.sensor_model}")
        print(f"  Firmware: {static_values.sensor_fw_version}")
        print(f"  API Version: {static_values.sensor_api_version}")

        # Structured instant values
        print("\nFetching instant values...")
        structured_status, structured_data = await client.instant_values_structured()
        if structured_status.name != "SUCCESS":
            print(f"Error fetching instant values: {structured_status}")
            return

        # Display sensors
        sensors = structured_data.get("sensor", {})
        if sensors:
            print("\nSensor Values:")
            for key, sensor_data in sensors.items():
                value = sensor_data.get("value")
                unit = sensor_data.get("unit")
                if unit:
                    print(f"  {key.replace('_', ' ').title()}: {value} {unit}")
                else:
                    print(f"  {key.replace('_', ' ').title()}: {value}")

        # Display binary sensors
        binary_sensors = structured_data.get("binary_sensor", {})
        if binary_sensors:
            print("\nAlarms & Status:")
            for key, sensor_data in binary_sensors.items():
                value = sensor_data.get("value")
                status = "ACTIVE" if value else "OK"
                print(f"  {key.replace('_', ' ').title()}: {status}")

        # Display numbers (setpoints)
        numbers = structured_data.get("number", {})
        if numbers:
            print("\nSetpoints:")
            for key, number_data in numbers.items():
                value = number_data.get("value")
                unit = number_data.get("unit")
                min_val = number_data.get("min")
                max_val = number_data.get("max")

                if unit:
                    print(f"  {key.replace('_', ' ').title()}: {value} {unit} (Range: {min_val}-{max_val})")
                else:
                    print(f"  {key.replace('_', ' ').title()}: {value} (Range: {min_val}-{max_val})")

        # Display switches
        switches = structured_data.get("switch", {})
        if switches:
            print("\nSwitches:")
            for key, switch_data in switches.items():
                value = switch_data.get("value")
                status = "ON" if value else "OFF"
                print(f"  {key.replace('_', ' ').title()}: {status}")

        # Display selects
        selects = structured_data.get("select", {})
        if selects:
            print("\nSettings:")
            for key, select_data in selects.items():
                value = select_data.get("value")
                print(f"  {key.replace('_', ' ').title()}: {value}")

        print("\nDemo completed successfully!")
        
    except (FileNotFoundError, ValueError, ImportError) as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mock Pooldose Client Demo")
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to JSON data file"
    )
    
    args = parser.parse_args()
    asyncio.run(main(args.json_file))
