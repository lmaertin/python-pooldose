# Examples

This directory contains demonstration scripts showing how to use the python-pooldose library.

## Files

### `demo.py` - Real Device Demo

Demonstrates connecting to a real PoolDose device and accessing all types of data.

**Usage:**

```bash
# Edit the HOST variable in the file first
python demo.py
```

**Features:**

- Connects to actual hardware
- Shows device information and static values
- Displays all sensor readings, alarms, setpoints, and settings
- Demonstrates error handling and SSL support

## Mock Client Usage

The mock client functionality is now integrated into the main CLI. No separate demo file needed:

```bash
# Use mock client with JSON file
pooldose --mock path/to/your/data.json

# Or as Python module
python -m pooldose --mock path/to/your/data.json

# Show help
pooldose --help
```

**Features:**

- No hardware required
- Uses real device data from JSON files
- Same API as real client
- Perfect for development and CI/CD
- Integrated command-line interface

## Running the Examples

From the project root directory:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the real device demo (edit HOST first!)
python examples/demo.py

# For mock client testing, use the CLI instead:
pooldose --mock path/to/your/data.json
```

## Documentation

For detailed information about the mock client system, see the [Mock Client System section](../README.md#mock-client-system) in the main README.

For the complete API documentation, see the main [../README.md](../README.md).
