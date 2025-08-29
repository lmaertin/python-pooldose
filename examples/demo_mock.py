#!/usr/bin/env python3
"""Demonstration for using the MockPooldoseClient with JSON files."""

import argparse
import asyncio
import sys
import traceback
from pathlib import Path

from demo_utils import display_structured_data, display_static_values
from pooldose.mock_client import MockPooldoseClient

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# pylint: disable=line-too-long,too-many-branches,too-many-statements

def validate_json_file(json_file_path: str):
    """Validate and return JSON file path."""
    if not json_file_path:
        print("Error: Please provide a valid JSON file path.")
        return None

    json_file = Path(json_file_path)
    if not json_file.exists():
        print(f"Error: Specified JSON file not found: {json_file}")
        return None

    return json_file


async def main(json_file_path: str = None) -> None:
    """Demonstrate all MockPooldoseClient calls."""
    print("Mock Pooldose Client Demo")
    print("=" * 50)

    # Validate input file
    json_file = validate_json_file(json_file_path)
    if not json_file:
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

        display_static_values(static_values)
        print(f"  API Version: {static_values.sensor_api_version}")

        # Structured instant values
        print("\nFetching instant values...")
        structured_status, structured_data = await client.instant_values_structured()
        if structured_status.name != "SUCCESS":
            print(f"Error fetching instant values: {structured_status}")
            return

        display_structured_data(structured_data)

        print("\nDemo completed successfully!")

    except (FileNotFoundError, ValueError, ImportError) as e:
        print(f"Error during demo: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Pooldose Client Demo")
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to JSON data file"
    )

    args = parser.parse_args()
    asyncio.run(main(args.json_file))
