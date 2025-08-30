"""Request Status for async API client for SEKO Pooldose."""

from enum import Enum


class RequestStatus(Enum):
    """
    Enum for standardized return codes of API and client methods.

    Each status represents a specific result or error case:
    - SUCCESS: Operation was successful.
    - HOST_UNREACHABLE: The host could not be reached (e.g. network error).
    - PARAMS_FETCH_FAILED: params.js could not be fetched or parsed.
    - API_VERSION_UNSUPPORTED: The API version is not supported.
    - NO_DATA: No data was returned or found.
    - LAST_DATA: No new data was found, last valid data was returned.
    - CLIENT_ERROR_SET: Error while setting a value on the client/device.
    - UNKNOWN_ERROR: An unspecified or unexpected error occurred.
    """
    SUCCESS = "success"
    HOST_UNREACHABLE = "host_unreachable"
    PARAMS_FETCH_FAILED = "params_fetch_failed"
    API_VERSION_UNSUPPORTED = "api_version_unsupported"
    NO_DATA = "no_data"
    LAST_DATA = "last_data"
    CLIENT_ERROR_SET = "client_error_set"
    UNKNOWN_ERROR = "unknown_error"
