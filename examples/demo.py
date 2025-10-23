"""Demo showing common usage of PooldoseClient and the mock client.

This script fetches static and instant values and demonstrates how to use
the typed setters on `InstantValues` (switch, number, select). When the
mock client is used, setter calls print the concrete POST payload that
would be sent to the device.
"""

import asyncio
import sys


from demo_utils import display_structured_data, display_static_values
from pooldose.client import PooldoseClient, RequestStatus
from pooldose.mock_client import MockPooldoseClient

# Ensure stdout is using UTF-8 encoding for consistent output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# pylint: disable=line-too-long,too-many-branches,too-many-statements

# Load optional demo configuration from demo_config.py (not checked in)
try:
    from demo_config import HOST, USE_MOCK_CLIENT, FILE, MODEL_ID, FW_CODE, DEBUG_PAYLOAD
except ImportError:
    # Fallback defaults when no config file is present
    USE_MOCK_CLIENT = False
    HOST = "kommspot"
    FILE = None
    MODEL_ID = None
    FW_CODE = None
    DEBUG_PAYLOAD = True


async def main() -> None:
    """Demonstrate all PooldoseClient calls."""
    # Choose real or mock client based on configuration
    if USE_MOCK_CLIENT:
        print("Using MockPooldoseClient with JSON file", FILE)
        # Enable payload inspection so the demo can print the mock POST body
        client = MockPooldoseClient(json_file_path=FILE, model_id=MODEL_ID, fw_code=FW_CODE, include_sensitive_data=True, inspect_payload=DEBUG_PAYLOAD)
    else:
        print("Using real PooldoseClient with network connection. Host:", HOST)
        client = PooldoseClient(host=HOST, include_mac_lookup=True, debug_payload=DEBUG_PAYLOAD)  # pylint: disable=no-value-for-parameter
    # Connect to the device (real or mock)
    client_status = await client.connect()
    if client_status != RequestStatus.SUCCESS:
        print(f"Error connecting to PooldoseClient: {client_status}")
        return
    print("Connected to Pooldose device.")

    # Fetch and display static values
    print("\nFetching static values...")
    static_values_status, static_values = client.static_values()
    if static_values_status != RequestStatus.SUCCESS:
        print(f"Error fetching static values: {static_values_status}")
        return

    display_static_values(static_values)
    print(f"  IP: {static_values.sensor_ip}")
    print(f"  MAC: {static_values.sensor_mac}")

    # Fetch and display structured instant values
    print("\nFetching instant values...")
    structured_status, structured_data = await client.instant_values_structured()
    if structured_status != RequestStatus.SUCCESS:
        print(f"Error fetching instant values: {structured_status}")
        return

    display_structured_data(structured_data)

    # Demonstrate setting values using the client's setters.
    print("\n" + "="*50)
    print("DEMONSTRATING VALUE SETTERS")
    print("="*50)
    
    print("\nSetting switch 'stop_pool_dosing' -> True")
    ok = await client.set_switch('stop_pool_dosing', True)
    print("Result:", ok)
    if ok and DEBUG_PAYLOAD and hasattr(client, 'get_last_payload'):
        last_payload = client.get_last_payload()
        if last_payload:
            print("Payload sent:", last_payload)

    print("\nSetting number 'ph_target' -> 7.2")
    ok = await client.set_number('ph_target', 7.2)
    print("Result:", ok)
    if ok and DEBUG_PAYLOAD and hasattr(client, 'get_last_payload'):
        last_payload = client.get_last_payload()
        if last_payload:
            print("Payload sent:", last_payload)

    print("\nSetting select 'water_meter_unit' -> 'L'")
    ok = await client.set_select('water_meter_unit', 'L')
    print("Result:", ok)
    if ok and DEBUG_PAYLOAD and hasattr(client, 'get_last_payload'):
        last_payload = client.get_last_payload()
        if last_payload:
            print("Payload sent:", last_payload)

    print("\nSetting lower/upper limits of 'ofa_ph' (pairing handled internally)")
    ok = await client.set_number('ofa_ph_lower', 6.2)
    print("ofa_ph_lower set result:", ok)
    if ok and DEBUG_PAYLOAD and hasattr(client, 'get_last_payload'):
        last_payload = client.get_last_payload()
        if last_payload:
            print("Payload sent:", last_payload)
            
    ok = await client.set_number('ofa_ph_upper', 8.1)
    print("ofa_ph_upper set result:", ok)
    if ok and DEBUG_PAYLOAD and hasattr(client, 'get_last_payload'):
        last_payload = client.get_last_payload()
        if last_payload:
            print("Payload sent:", last_payload)

    print("\nDemo completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
