#!/usr/bin/env python3
"""Command-line interface for python-pooldose."""

import argparse
import asyncio
import sys
from pathlib import Path

from pooldose import __version__
from pooldose.client import PooldoseClient, RequestStatus
from pooldose.mock_client import MockPooldoseClient

# Import demo utilities if available
try:
    from examples.demo_utils import (display_static_values,
                                     display_structured_data)
except ImportError:
    # Fallback implementations for when installed via pip
    def display_static_values(static_values):
        """Display static device values (fallback implementation)."""
        device_info = [
            ("Name", static_values.sensor_name),
            ("Serial", static_values.sensor_serial_number),
            ("Model", static_values.sensor_model),
            ("Firmware", static_values.sensor_fw_version),
        ]
        print("\nDevice Information:")
        for label, value in device_info:
            print(f"  {label}: {value}")

    def display_structured_data(structured_data):
        """Display structured data in a simple format."""
        for data_type, items in structured_data.items():
            if not items:
                continue
            print(f"\n{data_type.title()}:")
            for key, data in items.items():
                value = data.get("value")
                unit = data.get("unit", "")
                if unit:
                    print(f"  {key}: {value} {unit}")
                else:
                    print(f"  {key}: {value}")


async def run_real_client(host: str, use_ssl: bool, port: int) -> None:
    """Run the real PooldoseClient."""
    print(f"Connecting to PoolDose device at {host}")
    if use_ssl:
        print(f"Using HTTPS on port {port}")
    else:
        print(f"Using HTTP on port {port}")

    client = PooldoseClient(
        host=host,
        use_ssl=use_ssl,
        port=port if port != 0 else None,
        timeout=30
    )

    try:
        # Connect
        status = await client.connect()
        if status != RequestStatus.SUCCESS:
            print(f"Error connecting to device: {status}")
            return

        print("Connected successfully!")

        # Get static values
        static_status, static_values = client.static_values()
        if static_status == RequestStatus.SUCCESS:
            display_static_values(static_values)

        # Get instant values
        instant_status, instant_data = await client.instant_values_structured()
        if instant_status == RequestStatus.SUCCESS:
            display_structured_data(instant_data)

        print("\nConnection completed successfully!")

    except (ConnectionError, TimeoutError, OSError) as e:
        print(f"Network error: {e}")
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error during connection: {e}")


async def run_mock_client(json_file: str) -> None:
    """Run the MockPooldoseClient."""
    json_path = Path(json_file)
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_file}")
        return

    print(f"Loading mock data from: {json_file}")

    client = MockPooldoseClient(
        json_file_path=json_path,
        include_sensitive_data=True
    )

    try:
        # Connect
        status = await client.connect()
        if status.name != "SUCCESS":
            print(f"Error connecting to mock device: {status}")
            return

        print("Connected to mock device successfully!")

        # Get static values
        static_status, static_values = client.static_values()
        if static_status.name == "SUCCESS":
            display_static_values(static_values)

        # Get instant values
        instant_status, instant_data = await client.instant_values_structured()
        if instant_status.name == "SUCCESS":
            display_structured_data(instant_data)

        print("\nMock demo completed successfully!")

    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"File or data error: {e}")
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error during mock demo: {e}")


def main() -> None:
    """Main entry point for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Python PoolDose Client - Connect to SEKO PoolDose devices",
        epilog="""
Examples:
  # Connect to real device
  python -m pooldose --host 192.168.1.100

  # Connect with HTTPS
  python -m pooldose --host 192.168.1.100 --ssl --port 443

  # Use mock client with JSON file
  python -m pooldose --mock path/to/your/data.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--host",
        type=str,
        help="IP address or hostname of PoolDose device"
    )
    mode_group.add_argument(
        "--mock",
        type=str,
        metavar="JSON_FILE",
        help="Path to JSON file for mock mode"
    )

    # Connection options
    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Use HTTPS instead of HTTP"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Custom port (default: 80 for HTTP, 443 for HTTPS)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"python-pooldose {__version__}"
    )

    args = parser.parse_args()

    # Set UTF-8 encoding for output
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    print("Python PoolDose Client")
    print("=" * 40)

    try:
        if args.host:
            # Real device mode
            port = args.port if args.port != 0 else (443 if args.ssl else 80)
            asyncio.run(run_real_client(args.host, args.ssl, port))
        elif args.mock:
            # Mock mode
            asyncio.run(run_mock_client(args.mock))

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:  # pylint: disable=broad-except
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
