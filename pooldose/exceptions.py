class PooldoseGeneralError(Exception):
    """General error for Pooldose API requests."""

class PooldoseTimeoutError(Exception):
    """Timeout error for Pooldose API requests."""

class PooldoseCacheMissingError(Exception):
    """Value cache missing error for Pooldose API requests."""

class PooldoseInvalidResponseError(Exception):
    """Invalid response error for Pooldose API requests."""

class PooldoseWrongApiVersionError(Exception):
    """Wrong API version error for Pooldose API requests."""

class PooldoseFetchError(Exception):
    """Connection error for Pooldose API."""