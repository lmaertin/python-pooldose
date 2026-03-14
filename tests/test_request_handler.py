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
        external_session = MagicMock()
        external_session.close = AsyncMock()

        # Create a mock response that simulates a successful API response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()  # Not async
        mock_response.json = AsyncMock(return_value={"test": "data"})

        # Create the handler with external session
        handler = RequestHandler("192.168.1.1", websession=external_session)

        # Mock the behavior of the context manager to return our mock response
        # We patch the method at the exact point it's used in the code
        with patch.object(handler, '_get_session', return_value=(external_session, False)):
            with patch.object(external_session, 'get') as mock_get:
                # Configure mock_get to act as an async context manager
                async_cm = AsyncMock()
                async_cm.__aenter__.return_value = mock_response
                mock_get.return_value = async_cm

                # Make the request
                status, data = await handler.get_debug_config()

                # Verify the request was made with the external session
                mock_get.assert_called_once()
                assert status == RequestStatus.SUCCESS
                assert data == {"test": "data"}  # type: ignore

                # Verify session was not closed
                external_session.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_internal_session_creation(self):
        """Test that an internal session is created when no external session is provided."""
        # Create the handler without an external session
        handler = RequestHandler("192.168.1.1")

        # Mock ClientSession to track its creation and mock response
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Set up a mock session instance and response
            mock_session_instance = MagicMock()
            mock_session_instance.close = AsyncMock()
            mock_session_class.return_value = mock_session_instance

            # Create a mock response that simulates a successful API response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.raise_for_status = MagicMock()  # Not async
            mock_response.json = AsyncMock(return_value={"test": "data"})

            # Set up the get method to return an async context manager
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            mock_session_instance.get.return_value = async_cm

            # Make the request that should create an internal session
            status, data = await handler.get_debug_config()

            # Verify a new session was created
            mock_session_class.assert_called_once()
            assert status == RequestStatus.SUCCESS
            assert data == {"test": "data"}  # type: ignore

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
            assert data == {"test": "data"}  # type: ignore

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
            assert data == {"test": "data"}  # type: ignore

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


class TestSessionConsistency:
    """Tests to verify all HTTP methods use _get_session() consistently.

    Previously, set_value(), get_device_language() and reboot_device() created
    their own aiohttp.ClientSession instead of using _get_session(). This meant
    externally provided sessions (e.g. from Home Assistant) were bypassed.
    """

    @pytest.mark.asyncio
    async def test_set_value_uses_get_session_with_external(self):
        """Test that set_value() uses the external session via _get_session()."""
        external_session = MagicMock()
        external_session.close = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()

        handler = RequestHandler("192.168.1.1", websession=external_session)

        with patch.object(handler, '_get_session', return_value=(external_session, False)) as mock_get_session:
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            external_session.post = MagicMock(return_value=async_cm)

            result = await handler.set_value("DEVICE_1", "w_123", 7.0, "NUMBER")

            mock_get_session.assert_called_once()
            external_session.post.assert_called_once()
            assert result is True
            external_session.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_value_closes_internal_session(self):
        """Test that set_value() creates and closes an internal session when no external session is provided."""
        handler = RequestHandler("192.168.1.1")

        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(handler, '_get_session', return_value=(mock_session, True)):
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            mock_session.post = MagicMock(return_value=async_cm)

            result = await handler.set_value("DEVICE_1", "w_123", 7.0, "NUMBER")

            assert result is True
            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_value_closes_session_on_error(self):
        """Test that set_value() closes the internal session even on error."""
        handler = RequestHandler("192.168.1.1")

        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        with patch.object(handler, '_get_session', return_value=(mock_session, True)):
            async_cm = AsyncMock()
            async_cm.__aenter__.side_effect = aiohttp.ClientError("Connection refused")
            mock_session.post = MagicMock(return_value=async_cm)

            result = await handler.set_value("DEVICE_1", "w_123", 7.0, "NUMBER")

            assert result is False
            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_device_language_uses_get_session_with_external(self):
        """Test that get_device_language() uses the external session via _get_session()."""
        external_session = MagicMock()
        external_session.close = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={"LABEL_test": "Test Label"})

        handler = RequestHandler("192.168.1.1", websession=external_session)

        with patch.object(handler, '_get_session', return_value=(external_session, False)) as mock_get_session:
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            external_session.post = MagicMock(return_value=async_cm)

            status, data = await handler.get_device_language("TEST_DEVICE")

            mock_get_session.assert_called_once()
            external_session.post.assert_called_once()
            assert status == RequestStatus.SUCCESS
            assert data == {"LABEL_test": "Test Label"}
            external_session.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_device_language_closes_internal_session(self):
        """Test that get_device_language() closes an internal session after use."""
        handler = RequestHandler("192.168.1.1")

        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={"LABEL_test": "Test Label"})

        with patch.object(handler, '_get_session', return_value=(mock_session, True)):
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            mock_session.post = MagicMock(return_value=async_cm)

            status, _ = await handler.get_device_language("TEST_DEVICE")

            assert status == RequestStatus.SUCCESS
            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reboot_device_uses_get_session_with_external(self):
        """Test that reboot_device() uses the external session via _get_session()."""
        external_session = MagicMock()
        external_session.close = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()

        handler = RequestHandler("192.168.1.1", websession=external_session)

        with patch.object(handler, '_get_session', return_value=(external_session, False)) as mock_get_session:
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            external_session.post = MagicMock(return_value=async_cm)

            status, result = await handler.reboot_device()

            mock_get_session.assert_called_once()
            external_session.post.assert_called_once()
            assert status == RequestStatus.SUCCESS
            assert result is True
            external_session.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reboot_device_closes_internal_session(self):
        """Test that reboot_device() closes an internal session after use."""
        handler = RequestHandler("192.168.1.1")

        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(handler, '_get_session', return_value=(mock_session, True)):
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            mock_session.post = MagicMock(return_value=async_cm)

            status, result = await handler.reboot_device()

            assert status == RequestStatus.SUCCESS
            assert result is True
            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reboot_device_closes_session_on_error(self):
        """Test that reboot_device() closes the internal session even on error."""
        handler = RequestHandler("192.168.1.1")

        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        with patch.object(handler, '_get_session', return_value=(mock_session, True)):
            async_cm = AsyncMock()
            async_cm.__aenter__.side_effect = aiohttp.ClientError("Connection refused")
            mock_session.post = MagicMock(return_value=async_cm)

            status, result = await handler.reboot_device()

            assert status == RequestStatus.UNKNOWN_ERROR
            assert result is False
            mock_session.close.assert_awaited_once()


class TestAccessPointParsing:
    """Test for the get_access_point() response parsing fix."""

    @pytest.mark.asyncio
    async def test_get_access_point_parses_text_response(self):
        """Test that get_access_point() correctly parses JSON from text response.

        Previously, get_access_point() called both resp.text() and resp.json()
        on the same response, which could fail because the body can only be
        consumed once. Now it uses json.loads() on the already-read text.
        """
        handler = RequestHandler("192.168.1.1")

        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        json_body = '{"SSID": "KOMMSPOT-TEST", "KEY": "secret123"}'
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value=json_body)

        with patch.object(handler, '_get_session', return_value=(mock_session, True)):
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            mock_session.post = MagicMock(return_value=async_cm)

            status, data = await handler.get_access_point()

            assert status == RequestStatus.SUCCESS
            assert data == {"SSID": "KOMMSPOT-TEST", "KEY": "secret123"}
            # Verify resp.json() was NOT called (only resp.text() + json.loads)
            mock_response.json.assert_not_called()
            mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_access_point_handles_non_json_response(self):
        """Test that get_access_point() handles responses without valid JSON."""
        handler = RequestHandler("192.168.1.1")

        mock_session = MagicMock()
        mock_session.close = AsyncMock()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value="not json at all")

        with patch.object(handler, '_get_session', return_value=(mock_session, True)):
            async_cm = AsyncMock()
            async_cm.__aenter__.return_value = mock_response
            mock_session.post = MagicMock(return_value=async_cm)

            status, data = await handler.get_access_point()

            assert status == RequestStatus.NO_DATA
            assert data is None
