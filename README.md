# python-pooldose
Async Python client for SEKO Pooldose devices.

## Example

```python
import asyncio
from pooldose.client import PooldoseClient

HOST = "kommspot" #change to your device IP
TIMEOUT = 30

async def main():
    client = await PooldoseClient.create(host=HOST, timeout=TIMEOUT)

    # --- Static values ---
    static_values = client.static_values()
    print(f"Device Name: {static_values.sensor_name}")

    # --- Instant values ---
    instant_values = await client.instant_values()
    print(f"Temperature: {instant_values.sensor_temperature[0]} {instant_values.sensor_temperature[1]}")

    # --- Set values (examples for all categories) ---
    # Switch setter
    if await instant_values.switch_stop_pool_dosing_set(True):
        print("Stop pool dosing set to True.")

    # Number setter
    if await instant_values.number_ph_target_set(7.2):
        print("pH target set to 7.2.")

    # Select setter
    if await instant_values.select_water_meter_unit_set(1):
        print("Water meter unit set to 1.")

asyncio.run(main())
```
