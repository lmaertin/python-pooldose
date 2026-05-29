# python-pooldose

[![PyPI version](https://img.shields.io/pypi/v/python-pooldose)](https://pypi.org/project/python-pooldose/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://pypi.org/project/python-pooldose/)
[![License: MIT](https://img.shields.io/github/license/lmaertin/python-pooldose)](LICENSE)
[![Pylint](https://github.com/lmaertin/python-pooldose/actions/workflows/pylint.yml/badge.svg)](https://github.com/lmaertin/python-pooldose/actions/workflows/pylint.yml)
[![Mypy](https://github.com/lmaertin/python-pooldose/actions/workflows/mypy.yml/badge.svg)](https://github.com/lmaertin/python-pooldose/actions/workflows/mypy.yml)
[![Tests](https://github.com/lmaertin/python-pooldose/actions/workflows/python-app.yml/badge.svg)](https://github.com/lmaertin/python-pooldose/actions/workflows/python-app.yml)

Unofficial async Python client for [SEKO](https://www.seko.com/) Pooldosing systems. SEKO is a manufacturer of various monitoring and control devices for pools and spas. Some devices from [VÁGNER POOL](https://www.vagnerpool.com/web/en/) are compatible as well.

This client uses an undocumented local HTTP API. It provides live readings for pool sensors such as temperature, pH, ORP/Redox, as well as status information and control over the dosing logic.

> **Disclaimer:** Use at your own risk. No liability for damages or malfunctions.


## Features

- **Async/await support** for non-blocking operations
- **Dynamic sensor discovery** based on device model and firmware
- **Dictionary-style access** to instant values
- **Structured data API** with type-based organization
- **Device analyzer** for discovering unsupported device capabilities
- **PEP-561 compliant** with full type hints for Home Assistant integrations
- **Command-line interface** for direct device interaction and testing
- **Secure by default** - WiFi passwords excluded unless explicitly requested
- **Comprehensive error handling** with detailed logging
- **Cloud connection** status
- **WiFi RSSI** signal

Each method queries the device live and returns the current value.
- **SSL/HTTPS support** for secure communication

## Prerequisites

1. Install and set-up the PoolDose devices according to the user manual.
   1. In particular, connect the device to your WiFi network.
   2. Identify the IP address or hostname of the device.
2. Browse to the IP address or hostname (default port: 80).
   1. Try to log in to the web interface with the default password (0000).
   2. Check availability of data in the web interface.
3. Optionally: Block the device from internet access to ensure cloudless-only operation.

## Installation

```bash
pip install python-pooldose
```

## Quick Start

```python
import asyncio
from pooldose.client import PooldoseClient
from pooldose.request_status import RequestStatus

async def main():
    client = PooldoseClient(host="192.168.1.100")
    status = await client.connect()
    if status != RequestStatus.SUCCESS:
        print(f"Connection failed: {status}")
        return

    # Dictionary-style access
    status, values = await client.instant_values()
    if status == RequestStatus.SUCCESS and values:
        print(f"Temperature: {values['temperature']}")
        print(f"pH: {values.get('ph', 'N/A')}")

    # Structured data (grouped by type)
    status, data = await client.instant_values_structured()
    if status == RequestStatus.SUCCESS:
        for sensor, info in data.get("sensor", {}).items():
            print(f"{sensor}: {info['value']} {info.get('unit', '')}")

asyncio.run(main())
```

## Command Line Usage

```bash
# Connect to device
pooldose --host 192.168.1.100

# With HTTPS
pooldose --host 192.168.1.100 --ssl

# Analyze device capabilities
pooldose --host 192.168.1.100 --analyze

# Mock mode (testing without hardware)
pooldose --mock path/to/data.json

# Show help / version
pooldose --help
pooldose --version
```

See [docs/cli.md](docs/cli.md) for full CLI documentation and device analysis details.

## Supported Devices

| Device | PRODUCT_CODE | FW Code | Notes |
|---|---|---|---|
| SEKO PoolDose Double | PDPR1H1HAW100 | 539187 | |
| SEKO PoolDose Double Spa | PDPR1H04AW100 | 539292 | |
| SEKO POOLDOSE pH+ORP CF Group Wi-Fi | PDPR1H1HAW102 | 539187 | Alias for PDPR1H1HAW100 mapping |
| SEKO PoolDose pH | PDPH1H1HAW100 | 539176 | pH-only device |
| VÁGNER POOL VA DOS BASIC | PDHC1H1HAR1V0 | 539224 | |
| VÁGNER POOL VA DOS EXACT | PDHC1H1HAR1V1 | 539224 | Alias for PDPR1H1HAR1V0 mapping |

Other models may work but are untested. See [docs/device-support.md](docs/device-support.md) for how to request support for new devices.

## Documentation

| Topic | Description |
|---|---|
| [API Reference](docs/api-reference.md) | Constructor, methods, properties, data formats |
| [CLI & Device Analysis](docs/cli.md) | Command line usage and device analyzer |
| [Examples](docs/examples.md) | Basic and advanced usage examples |
| [Mock Client](docs/mock-client.md) | Testing without hardware using JSON files |
| [SSL/HTTPS](docs/ssl.md) | SSL configuration and migration guide |
| [Security](docs/security.md) | Data classification and sensitive data handling |
| [Type Hints & HA](docs/type-hints.md) | PEP-561 compliance and Home Assistant integration |

## Changelog

For detailed release notes and version history, please see [CHANGELOG.md](CHANGELOG.md).
