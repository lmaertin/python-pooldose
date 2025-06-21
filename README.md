# python-pooldose
Async Python client for SEKO Pooldose devices.

## Example

> **Note:** Replace `KOMMSPOT` with your device's hostname or IP address.

```python
import asyncio
import json
from pooldose.client import PooldoseClient

HOST = "KOMMSPOT"  # Change this to your device's host or IP address
TIMEOUT = 30

async def main() -> None:
    """Demonstrate all PooldoseClient calls."""

    # Create the client instance (connects to your Pooldose device)
    client = await PooldoseClient.create(host=HOST, timeout=TIMEOUT)

    # --- Print all device info in a pretty format ---
    print("Device Info:")
    print(json.dumps(client.device_info, indent=2))

    # --- Static values example ---
    # Retrieve and print static device information
    static_values = client.static_values()
    print(f"Device Name: {static_values.sensor_name}")
    print(f"Serial Number: {static_values.sensor_serial_number}")
    print(f"Firmware Version: {static_values.sensor_fw_version}")

    # --- Instant values example ---
    # Retrieve and print current sensor and binary sensor values
    instant_values = await client.instant_values()
    print(f"Temperature: {instant_values.sensor_temperature[0]} {instant_values.sensor_temperature[1]}")
    print(f"pH: {instant_values.sensor_ph[0]} {instant_values.sensor_ph[1]}")
    print(f"ORP: {instant_values.sensor_orp[0]} {instant_values.sensor_orp[1]}")
    print(f"Pump Running: {instant_values.binary_sensor_pump_running}")

    # --- Set switch example ---
    # Set the stop pool dosing switch to True and print the result
    result = await instant_values.switch_stop_pool_dosing_set(True)
    print(f"Stop pool dosing set: {result}")

    # --- Set number example ---
    # Set the pH target value to 7.2 and print the result
    result = await instant_values.number_ph_target_set(7.2)
    print(f"pH target set: {result}")

    # --- Set select example ---
    # Set the water meter unit (example value: 1) and print the result if successful
    result = await instant_values.select_water_meter_unit_set(1)
    if result:
        print("Water meter unit set to 1.")

if __name__ == "__main__":
    # Run the demonstration using asyncio
    asyncio.run(main())
```
