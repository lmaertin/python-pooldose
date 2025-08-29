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

### `demo_mock.py` - Mock Client Demo

Shows how to use the mock client with JSON files for development and testing.

**Usage:**

```bash
# Use custom JSON file
python demo_mock.py path/to/your/data.json

# Show help
python demo_mock.py --help
```

**Features:**

- No hardware required
- Uses real device data from JSON files
- Same API as real client
- Perfect for development and CI/CD
- Command-line argument support for custom data files

## Running the Examples

From the project root directory:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the mock demo with custom data
python examples/demo_mock.py path/to/your/data.json

# Run the real device demo (edit HOST first!)
python examples/demo.py
```

## Documentation

For detailed information about the mock client system, see the [Mock Client System section](../README.md#mock-client-system) in the main README.

For the complete API documentation, see the main [../README.md](../README.md).
