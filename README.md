# python-pooldose
Async Python client for SEKO Pooldose devices.

## Example

```python
import asyncio
from pooldose import PooldoseClient

async def main():
    client = PooldoseClient("192.168.1.100")
    info = await client.get_info_release()
    print(info)

asyncio.run(main())
