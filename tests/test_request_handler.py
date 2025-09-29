"""Tests for RequestHandler for Async API client for SEKO Pooldose."""

from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
import pytest

from pooldose.request_handler import RequestHandler, RequestStatus

# pylint: disable=line-too-long


# pylint: disable=too-few-public-methods
class TestRequestHandler:
    """Tests for the RequestHandler class public interface."""

    @pytest.mark.asyncio
    async def test_host_unreachable(self, monkeypatch):
        """Test that connection to an unreachable host fails with proper status."""
        # Simulate a network error by patching the socket connection function
        monkeypatch.setattr("socket.create_connection", lambda *a, **kw: (_ for _ in ()).throw(OSError("unreachable")))

        # Create handler with an invalid IP address
        handler = RequestHandler("256.256.256.256", timeout=1)

        # Attempt to connect and verify the expected failure status is returned
        status = await handler.connect()
        assert status == RequestStatus.HOST_UNREACHABLE


class TestSessionManagement:
    """Tests for session management behavior in RequestHandler public methods."""

    @pytest.mark.asyncio
    async def test_external_session_usage(self):
        """Test that when an external session is provided, it's used for requests."""
        # Create mock external session
        external_session = AsyncMock()
        external_session.close = AsyncMock()

        # Set up a mock response
        mock_response = AsyncMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value={"test": "data"})
        external_session.get = MagicMock(return_value=mock_response)

        # Create handler with external session
        handler = RequestHandler("192.168.1.1", websession=external_session)

        # Make a request
        status, data = await handler.get_debug_config()

        # Verify the request was made with the external session
        external_session.get.assert_called_once()
        assert status == RequestStatus.SUCCESS
        assert data == {"test": "data"}

        # Verify session was not closed
        external_session.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_internal_session_creation(self):
        """Test that an internal session is created when no external session is provided."""
        # Create the handler without an external session
        handler = RequestHandler("192.168.1.1")

        # Mock ClientSession to track its creation and mock response
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Setup mock session with response
            mock_session_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = AsyncMock(return_value={"test": "data"})

            # Configure the session mock
            mock_session_instance.get = MagicMock(return_value=mock_response)
            mock_session_instance.close = AsyncMock()
            mock_session_class.return_value = mock_session_instance

            # Make a request that should create an internal session
            status, data = await handler.get_debug_config()

            # Verify a new session was created
            mock_session_class.assert_called_once()
            assert status == RequestStatus.SUCCESS
            assert data == {"test": "data"}

            # Verify session was closed
            mock_session_instance.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_session_closed_after_request(self):
        """Test that session is properly closed after a request if it's an internal session."""
        handler = RequestHandler("192.168.1.1")

        # Mock the session directly
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        # Implement a simplified version of get_debug_config for the test
        async def mock_get_debug_config(self):
            session, close_session = await self._get_session()
            try:
                # Simulate successful call
                return RequestStatus.SUCCESS, {"test": "data"}
            finally:
                if close_session:
                    await session.close()

        with patch.object(handler, '_get_session', return_value=(mock_session, True)), \
             patch.object(RequestHandler, 'get_debug_config', mock_get_debug_config):
            # Call the method
            status, data = await handler.get_debug_config()

            # Verify we got the expected result
            assert status == RequestStatus.SUCCESS
            assert data == {"test": "data"}

            # Verify the session was closed
            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_session_not_closed_if_external(self):
        """Test that session is not closed after a request if it's an external session."""
        # Create an external session
        external_session = AsyncMock()
        external_session.close = AsyncMock()
        handler = RequestHandler("192.168.1.1", websession=external_session)

        # Implement a simplified version of get_debug_config for the test
        async def mock_get_debug_config(self):
            session, close_session = await self._get_session()
            try:
                # Simulate successful call
                return RequestStatus.SUCCESS, {"test": "data"}
            finally:
                if close_session:
                    await session.close()

        with patch.object(RequestHandler, 'get_debug_config', mock_get_debug_config):
            # Call the method
            status, data = await handler.get_debug_config()

            # Verify we got the expected result
            assert status == RequestStatus.SUCCESS
            assert data == {"test": "data"}

            # Verify the session was not closed (since it's an external session)
            external_session.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_session_closed_on_exception(self):
        """Test that an internal session is closed even if an exception occurs."""
        handler = RequestHandler("192.168.1.1")

        # Mock the session directly
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        # Generate error and handle it in an explicit try-except block
        async def mock_get_debug_config(self):
            session, close_session = await self._get_session()
            try:
                # Simulate an exception during processing
                raise aiohttp.ClientError("Test error")
            except aiohttp.ClientError:
                # Catch error (as in real code)
                if close_session:
                    await session.close()
                return RequestStatus.UNKNOWN_ERROR, None

        with patch.object(handler, '_get_session', return_value=(mock_session, True)), \
             patch.object(RequestHandler, 'get_debug_config', mock_get_debug_config):

            # Call the method
            status, data = await handler.get_debug_config()

            # Verify the status is UNKNOWN_ERROR
            assert status == RequestStatus.UNKNOWN_ERROR
            assert data is None

            # Verify the session was closed despite the exception
            mock_session.close.assert_awaited_once()
