# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.5] - 2025-01-25

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