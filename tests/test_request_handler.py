"""Tests for RequestHandler for Async API client for SEKO Pooldose."""

import pytest
from pooldose.request_handler import RequestHandler, RequestStatus

# pylint: disable=line-too-long

@pytest.mark.asyncio
async def test_host_unreachable(monkeypatch):
    """Test that unreachable host returns HOST_UNREACHABLE."""
    monkeypatch.setattr("socket.create_connection", lambda *a, **kw: (_ for _ in ()).throw(OSError("unreachable")))
    handler = RequestHandler("256.256.256.256", timeout=1)
    status = await handler.connect()
    assert status == RequestStatus.HOST_UNREACHABLE

@pytest.mark.asyncio
async def test_check_apiversion_supported():
    """Test API version check logic."""
    handler = RequestHandler("localhost")
    handler.api_version = "v1/"
    assert handler.check_apiversion_supported()[0] == RequestStatus.SUCCESS
    handler.api_version = "v2/"
    assert handler.check_apiversion_supported()[0] == RequestStatus.API_VERSION_UNSUPPORTED
    handler.api_version = None
    assert handler.check_apiversion_supported()[0] == RequestStatus.NO_DATA
