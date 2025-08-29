#!/usr/bin/env python3
"""Simple test script for MockPooldoseClient."""

import asyncio
from pathlib import Path
from pooldose.mock_client import MockPooldoseClient

async def main():
    """Simple test of mock client functionality."""
    print("Simple Mock Client Test")
    print("-" * 30)
    
    # Load data
    json_file = Path(__file__).parent.parent / "references" / "testdaten" / "suplere" / "test.json"
    
    if not json_file.exists():
        print(f"Test file not found: {json_file}")
        return
    
    # Create mock client
    client = MockPooldoseClient(json_file_path=json_file)
    
    # Connect
    print("Connecting...")
    status = await client.connect()
    print(f"Status: {status.name}")
    
    if not client.is_connected:
        print("Connection failed")
        return
    
    # Get sensor values
    print("\nLive Sensor Values:")
    status, instant_values = await client.instant_values()
    
    if status.name == "SUCCESS" and instant_values:
        print(f"  Temperature: {instant_values['temperature']}")
        print(f"  pH: {instant_values['ph']}")
        print(f"  ORP: {instant_values['orp']}")
        print(f"  Chlorine: {instant_values['cl']}")
    else:
        print(f"  Failed: {status}")
    
    # Get device info
    print(f"\nDevice: {client.device_info['NAME']}")
    print(f"   Serial: {client.device_info['SERIAL_NUMBER']}")
    print(f"   Model: {client.device_info['MODEL']}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main())
