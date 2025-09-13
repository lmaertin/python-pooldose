"""Demonstration for using the PooldoseClient."""

import asyncio
import sys

from demo_utils import display_structured_data, display_static_values
from pooldose.client import PooldoseClient, RequestStatus

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# pylint: disable=line-too-long,too-many-branches,too-many-statements

HOST = "192.168.178.137"  # Replace with your device's IP address

async def main() -> None:
    """Demonstrate all PooldoseClient calls."""
    client = PooldoseClient(host=HOST, include_mac_lookup=True)

    # Connect
    client_status = await client.connect()
    if client_status != RequestStatus.SUCCESS:
        print(f"Error connecting to PooldoseClient: {client_status}")
        return

    print(f"Connected to Pooldose device at {HOST}")

    # Static values
    print("\nFetching static values...")
    static_values_status, static_values = client.static_values()
    if static_values_status != RequestStatus.SUCCESS:
        print(f"Error fetching static values: {static_values_status}")
        return

    display_static_values(static_values)
    print(f"  IP: {static_values.sensor_ip}")
    print(f"  MAC: {static_values.sensor_mac}")

    # Structured instant values
    print("\nFetching instant values...")
    structured_status, structured_data = await client.instant_values_structured()
    if structured_status != RequestStatus.SUCCESS:
        print(f"Error fetching instant values: {structured_status}")
        return

    display_structured_data(structured_data)

    print("\nDemo completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
