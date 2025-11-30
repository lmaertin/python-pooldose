# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.1] - 2025-11-30

### Changed

- **Unit Standardization**: Chlorine values now consistently return "ppm" instead of "CL2" or "Chlorine"
  - Applied to both sensor and number types
  - Improved consistency across all chlorine measurements
- **Mapping Consistency**: Renamed OFA (Output Final Alarm) threshold mappings for better naming convention
  - `orp_ph_lower/upper` → `ofa_orp_lower/upper`
  - `cl_ph_lower/upper` → `ofa_cl_lower/upper`
  - Now consistent with existing `ofa_ph_lower/upper` naming pattern

### Enhanced

- **Test Coverage**: Added comprehensive tests for chlorine unit conversion
- **Code Quality**: All tests pass (123 total), mypy and pylint score 10.00/10

## [0.8.0] - 2025-11-26

### Changed

- **Entity Type Refinement**: `flow_rate_value` renamed to `flow_rate`

## [0.7.9] - 2025-11-26

### Changed

- **Simplified Entity Types**: Reduced complexity by moving read-only numeric values to sensor type
  - `water_meter_total_permanent` moved from number to sensor
  - `water_meter_total_resettable` moved from number to sensor
  - `flow_rate_value` moved from number to sensor
- **Streamlined Configuration**: Reduced select entities to essential configuration options only
  - Removed redundant read-only select types
  - Focused on user-configurable settings for better clarity
  - Improved entity organization and usability

### Enhanced

- **Entity Organization**: Better alignment between entity types and their actual usage patterns
- **API Clarity**: More intuitive distinction between read-only sensors and configurable numbers

## [0.7.8] - 2025-10-27

### Enhanced

- **Type Safety**: Complete integration of TypedDict definitions from `type_definitions.py`
  - `DeviceInfoDict` now used throughout for device information
  - `APIVersionResponse` properly returned from version checks
  - `StructuredValuesDict` correctly typed for structured instant values
  - `ValueDict` extended with min/max/step fields for number types
- **Home Assistant Compatibility**: Full strict typing compliance for HA integrations
  - All public API methods use proper TypedDict types
  - MyPy strict mode passes without any type: ignore comments
  - PEP-561 compliance maintained and enhanced
- **Code Quality**: Elegant use of string literals for TypedDict keys
  - Replaced runtime casting with compile-time type safety
  - Improved maintainability and readability
  - Better IDE support and autocompletion

### Fixed

- **StaticValues**: Now accepts DeviceInfoDict directly without casting
- **InstantValues**: to_structured_dict() returns proper StructuredValuesDict type
- **Constants**: get_default_device_info() returns correct DeviceInfoDict type

## [0.7.7] - 2025-10-27

### Added

- **CLI Debug Flag**: New `--print-payload` option for debugging HTTP payloads
  - Usage: `pooldose --host 192.168.1.100 --print-payload`
- **Payload Debugging**: Added `debug_payload` parameter and `get_last_payload()` method
- **Enhanced Demo**: Updated `examples/demo.py` with payload inspection (only shows payloads when operations succeed)

## [7.5.0] - 2025-10-20

### Added

- Convenience setters on the client: `set_switch`, `set_number`, `set_select` to avoid fetching InstantValues manually.
 - Mock client: now returns and stores the concrete POST payload for inspection (via `inspect_payload` / `get_last_payload`) and provides the same convenience setters as the real client.
 - Updated `examples/demo.py` to demonstrate usage for both real and mock clients (mock prints payloads when `inspect_payload` is enabled).
 - **New Device**: Added support for VA DOS EXACT (Model PDPR1H1HAR1V1, FW FW539224)

### Changed

- `InstantValues.set_number` now pairs `minT`/`maxT` fields and sends them as a single `[min,max]` payload when applicable.
- `RequestHandler.set_value` now always uses arrays for all value types, even for single values (e.g., `[{"value": 7, "type": "NUMBER"}]`, `[{"value": "O", "type": "STRING"}]`).
 - Mock client behavior adjusted: tests/demos can opt-in to inspect payloads; tests were updated to expect payload inspection by default.

### Enhanced

- **Fix**: Removed Chlorine Sensor from PDPR1H1HAR1V0, as this is not supported.

### Fixed

- Tests updated to expect inspectable mock payloads by default; test suite now passes.
 - Updated demo and tests; full test suite currently passes (119 tests).

---
## [0.7.0] - 2025-09-29

### Enhanced

- **Connection Handling**: Improved session management for more reliable connections
- **RequestHandler**: Centralized session management with internal _get_session method
- **Performance**: Reduced connection overhead for multiple consecutive API calls
- **Error Handling**: Better cleanup of HTTP sessions in error cases

## [0.6.9] - 2025-09-13

### Enhanced

- **Client**: Optional MAC lookup with include_mac_lookup flag

## [0.6.8] - 2025-09-13

### Enhanced

- **Client**: Implemented alternate method to retrieve MAC address of device. Before the MAC address of the router connected to the device has been returned.
- **Mapping**: Further fixes for PDPR1H1HAR1V0_FW539224

### Added

- **Values**: Added conversion for binary sensors

## [0.6.6] - 2025-09-08

### Enhanced

- **Mapping**: Fixed for PDPR1H1HAR1V0_FW539224

## [0.6.5] - 2025-09-06

### Added

- **Device Analyzer**: New CLI command `--analyze` for comprehensive device analysis
  - Widget extraction and type detection for unsupported devices
  - Support discovery: `pooldose --host IP --analyze` to analyze device capabilities
  - Detailed widget information including labels, values, and possible values
  - Option `--analyze-all` to show all widgets including hidden ones
  - Helps identify new device models and their supported features
- **Code Quality**: Achieved perfect Pylint 10.00/10 score
  - Complete PEP-561 compliance for Home Assistant integrations
  - Comprehensive type annotations with mypy strict mode
  - Enhanced error handling and documentation
  - Removed all linting issues (trailing whitespace, unused arguments, etc.)

### Enhanced

- **Documentation**: Added device analysis section with practical examples
- **Testing**: All 111 tests pass with enhanced test coverage
- **Type Safety**: Full mypy compliance with zero errors across codebase

## [0.6.0] - 2025-08-30

### Added

- **Command Line Interface**: Complete CLI implementation with `--host`, `--mock`, `--ssl`, and `--port` options
  - Real device connection: `pooldose --host 192.168.1.100`
  - Mock mode with JSON files: `pooldose --mock path/to/data.json`
  - HTTPS support: `pooldose --host 192.168.1.100 --ssl --port 8443`
  - Alternative module execution: `python -m pooldose --host IP`
- **Pip Installation Support**: Install as console script via `pip install python-pooldose`
- **Version and Help Commands**: `--version` and `--help` support in CLI
- **PEP-561 Type Compliance**: Package is now fully PEP-561 compliant for Home Assistant integrations
  - Added `py.typed` file marking the package as typed
  - Public API methods have comprehensive type annotations
  - mypy configuration included in pyproject.toml
  - Compatible with Home Assistant strict typing requirements

### Enhanced

- **Documentation Modernization**: Complete overhaul of all documentation
  - Centralized CLI documentation in main README
  - Removed all references to deprecated demo scripts
  - Updated examples and usage instructions
- **Code Quality Improvements**: Achieved Pylint 10.00/10 score
  - Strict typing implementation with PEP-561 compliance
  - Enhanced error handling and validation
  - Code deduplication and cleanup
  - mypy configuration for type checking
  - Type-safe public API for Home Assistant integrations
- **Mock Client Integration**: Seamless integration of mock functionality into CLI
  - No separate demo scripts needed
  - Same command interface for real and mock modes
  - Enhanced JSON data validation

### Removed

- **Deprecated Demo Scripts**: Removed `demo_mock.py` and related files
  - All functionality now available via CLI
  - Simplified project structure
  - Reduced maintenance overhead
- **Legacy References**: Cleaned up all user-specific and test data references

### Fixed

- **Documentation Consistency**: All documentation now accurately reflects current functionality
- **CLI Error Handling**: Improved error messages and validation
- **Examples Accuracy**: Updated all examples to use current API and CLI patterns

## [0.5.1] - 2025-08-29

### Added

- **Examples**: Demo scripts for real and mock clients (`examples/` directory)
- **Device Support**: Added mapping for model `PDPR1H1HAR***_FW53****`
- **Mock Client**: JSON-based testing framework for development without hardware

## [0.5.0] - 2025-08-24

### Changed
- **BREAKING**: Complete redesign of InstantValues API for improved usability and performance
  - Removed deprecated type-specific getter methods (`get_sensors()`, `get_switches()`, etc.)
  - Removed deprecated `available_types()` method and similar discovery methods
  - Simplified API to focus on dictionary-style access and structured data retrieval

### Added
- Enhanced dictionary-style access with full dict-like interface
  - `instant_values["key"]` for direct value access
  - `instant_values.get("key", default)` for safe access with defaults
  - `"key" in instant_values` for existence checks
  - Improved caching mechanism for better performance
- New `to_structured_dict()` method for type-organized data access
  - Returns data grouped by type: `sensor`, `number`, `switch`, `binary_sensor`, `select`
  - Clean, consistent data structure with value/unit/constraints information
  - Replaces all previous type-specific methods with single unified approach
- Enhanced async setter methods with comprehensive validation
  - `await instant_values.set_number()` with range and step validation
  - `await instant_values.set_switch()` with boolean type checking
  - `await instant_values.set_select()` with option validation
- Improved error handling and logging throughout InstantValues class
  - Better type checking and validation messages
  - Graceful handling of missing or invalid data
  - Enhanced debugging information for troubleshooting

### Enhanced
- Complete code cleanup and modernization
  - All comments and documentation converted to English
  - Improved type hints with Union and Tuple types
  - Better method organization and code structure
  - Removed obsolete number conversion logic (factor/offset)
- Robust data processing with comprehensive error handling
  - Enhanced validation for all data types
  - Better handling of edge cases and malformed data
  - Improved conversion logic for select values
- Updated comprehensive test suite
  - Full coverage for new InstantValues interface
  - Tests for both success and error scenarios
  - Proper mocking of async operations and dependencies
  - Updated to use correct RequestStatus enum values

### Migration Guide
**From 0.4.x to 0.5.x:**

```python
# OLD (0.4.x) - DEPRECATED
sensors = instant_values.get_sensors()
switches = instant_values.get_switches()
numbers = instant_values.get_numbers()

# NEW (0.5.0) - Dictionary-style access
temperature = instant_values["temperature"]  # Direct access
ph = instant_values.get("ph", "Not available")  # With default
has_temp = "temperature" in instant_values  # Existence check

# NEW (0.5.0) - Structured data access
status, structured_data = await client.instant_values_structured()
sensors = structured_data.get("sensor", {})
switches = structured_data.get("switch", {})
numbers = structured_data.get("number", {})
```

## [0.4.7] - 2025-08-04

### Enhanced
- Minor: Fixed no unit issue for pH number values as well

## [0.4.6] - 2025-07-26

### Enhanced
- Pooldose device returns unit for pH values, which have physically no unit. 
- Fixed by replacing such occurrences with None.

## [0.4.5] - 2025-07-25

### Added
- Complete SSL/HTTPS support for secure device communication (PR #3)
  - SSL certificate verification with configurable options
  - Custom port support for HTTPS connections
  - Backward compatibility for HTTP connections
  - Comprehensive SSL test coverage
- Pylint integration with CI/CD pipeline (PR #4)
  - Automated code quality checks across Python 3.11, 3.12, and 3.13
  - Enhanced code standards and consistency
  - Continuous integration for pull requests

### Enhanced
- Security model with configurable SSL verification
- Documentation with comprehensive SSL configuration examples
- Code quality improvements through automated linting

## [0.4.2] - 2025-07-19

### Fixed
- Corrected imports of RequestStatus class
- Fixing broken release 0.4.1

## [0.4.1] - 2025-07-17

### Changed
- **BREAKING**: Moved all RequestStatus into client module - import from `pooldose.client` instead of `pooldose.request_handler`
- Moved all connect checks into client (incl. API Version check) to avoid public access to requesthandler
- Clean up code and improved encapsulation

## [0.4.0] - 2025-07-11

### Changed
- **BREAKING**: Removed `create()` factory method
- **BREAKING**: Changed client initialization pattern to separate `__init__` and async `connect()` methods
- Changed default timeout to 30s
- Simplified RequestHandler by removing factory method pattern

### Added
- Added `is_connected` property to check connection status
- Improved flexibility for testing and connection management
- Improved unit handling (No Unit is 'None')

## [0.3.1] - 2025-07-04

### Added
- First official release, published on PyPi
- Install with `pip install python-pooldose`

## [0.3.0] - 2025-07-02

### Changed
- **BREAKING**: Changed from dataclass properties to dictionary-based access for instant values

### Added
- Added dynamic sensor discovery based on device mapping files
- Added type-specific getter methods (get_sensors, get_switches, etc.)
- Added type-specific setter methods with validation (set_number, set_switch, etc.)
- Added dictionary-style access (__getitem__, __setitem__, get, __contains__)
- Added configurable sensitive data handling (excludes WiFi passwords by default)
- Improved async file loading to prevent event loop blocking
- Enhanced error handling and logging
- Added comprehensive type annotations

## [0.2.0] - 2024-06-25

### Added
- Added query feature to list all available sensors and actuators

## [0.1.5] - 2024-06-24

### Added
- First working prototype for PoolDose Double/Dual WiFi supported
- All sensors and actuators for PoolDose Double/Dual WiFi supported
