"""Tests for SSL support in RequestHandler and PooldoseClient."""
# pylint: disable=protected-access

import ssl
from unittest.mock import patch, Mock, AsyncMock

import pytest

from pooldose.request_handler import RequestHandler
from pooldose.client import PooldoseClient
from pooldose.request_status import RequestStatus


class TestRequestHandlerSSL:
    """Test SSL functionality in RequestHandler."""

    def test_ssl_initialization_default(self):
        """Test RequestHandler initialization with default SSL settings."""
        handler = RequestHandler("example.com")
        assert handler.use_ssl is False
        assert handler.port == 80
        assert handler.ssl_verify is True
        assert handler._ssl_context is None

    def test_ssl_initialization_enabled(self):
        """Test RequestHandler initialization with SSL enabled."""
        handler = RequestHandler("example.com", use_ssl=True)
        assert handler.use_ssl is True
        assert handler.port == 443
        assert handler.ssl_verify is True
        assert handler._ssl_context is not None
        assert isinstance(handler._ssl_context, ssl.SSLContext)

    def test_ssl_initialization_disabled_verification(self):
        """Test RequestHandler initialization with SSL enabled but verification disabled."""
        handler = RequestHandler("example.com", use_ssl=True, ssl_verify=False)
        assert handler.use_ssl is True
        assert handler.port == 443
        assert handler.ssl_verify is False
        assert handler._ssl_context is False

    def test_ssl_initialization_custom_port(self):
        """Test RequestHandler initialization with custom port."""
        handler = RequestHandler("example.com", use_ssl=True, port=8443)
        assert handler.use_ssl is True
        assert handler.port == 8443
        assert handler.ssl_verify is True
        assert handler._ssl_context is not None

    def test_build_url_http(self):
        """Test URL building for HTTP."""
        handler = RequestHandler("example.com")
        url = handler._build_url("/api/v1/test")
        assert url == "http://example.com/api/v1/test"

    def test_build_url_https(self):
        """Test URL building for HTTPS."""
        handler = RequestHandler("example.com", use_ssl=True)
        url = handler._build_url("/api/v1/test")
        assert url == "https://example.com/api/v1/test"

    def test_build_url_custom_port_http(self):
        """Test URL building for HTTP with custom port."""
        handler = RequestHandler("example.com", port=8080)
        url = handler._build_url("/api/v1/test")
        assert url == "http://example.com:8080/api/v1/test"

    def test_build_url_custom_port_https(self):
        """Test URL building for HTTPS with custom port."""
        handler = RequestHandler("example.com", use_ssl=True, port=8443)
        url = handler._build_url("/api/v1/test")
        assert url == "https://example.com:8443/api/v1/test"

    def test_build_url_default_port_no_suffix(self):
        """Test URL building with default ports don't include port in URL."""
        # HTTP default port
        handler = RequestHandler("example.com", port=80)
        url = handler._build_url("/api/v1/test")
        assert url == "http://example.com/api/v1/test"

        # HTTPS default port
        handler = RequestHandler("example.com", use_ssl=True, port=443)
        url = handler._build_url("/api/v1/test")
        assert url == "https://example.com/api/v1/test"

    @patch('socket.create_connection')
    def test_host_reachable_custom_port(self, mock_socket):
        """Test host reachability check uses configured port."""
        mock_socket.return_value.__enter__ = Mock()
        mock_socket.return_value.__exit__ = Mock()

        handler = RequestHandler("example.com", port=8080)
        result = handler.check_host_reachable()

        mock_socket.assert_called_once_with(("example.com", 8080), timeout=10)
        assert result is True

    @patch('socket.create_connection')
    def test_host_unreachable_custom_port(self, mock_socket):
        """Test host unreachable with custom port."""
        mock_socket.side_effect = OSError("Connection failed")

        handler = RequestHandler("example.com", port=8443, use_ssl=True)
        result = handler.check_host_reachable()

        mock_socket.assert_called_once_with(("example.com", 8443), timeout=10)
        assert result is False

    def test_ssl_context_configuration(self):
        """Test that SSL context is properly configured based on ssl_verify setting."""
        # SSL enabled with verification
        handler = RequestHandler("example.com", use_ssl=True, ssl_verify=True)
        assert handler._ssl_context is not None
        assert isinstance(handler._ssl_context, ssl.SSLContext)

        # SSL enabled without verification
        handler = RequestHandler("example.com", use_ssl=True, ssl_verify=False)
        assert handler._ssl_context is False

        # SSL disabled
        handler = RequestHandler("example.com", use_ssl=False)
        assert handler._ssl_context is None

    def test_ssl_connector_logic(self):
        """Test the logic for determining when to create SSL connectors."""
        # SSL enabled - connector logic should be applied
        handler = RequestHandler("example.com", use_ssl=True, ssl_verify=True)
        should_create_connector = handler.use_ssl
        assert should_create_connector is True

        # SSL disabled - no connector needed
        handler = RequestHandler("example.com", use_ssl=False)
        should_create_connector = handler.use_ssl
        assert should_create_connector is False


class TestPooldoseClientSSL:
    """Test SSL functionality in PooldoseClient."""

    def test_client_ssl_initialization_default(self):
        """Test PooldoseClient initialization with default SSL settings."""
        client = PooldoseClient("example.com")
        assert client._use_ssl is False
        assert client._port is None
        assert client._ssl_verify is True

    def test_client_ssl_initialization_enabled(self):
        """Test PooldoseClient initialization with SSL enabled."""
        client = PooldoseClient("example.com", use_ssl=True, port=8443, ssl_verify=False)
        assert client._use_ssl is True
        assert client._port == 8443
        assert client._ssl_verify is False

    @pytest.mark.asyncio
    @patch('pooldose.client.RequestHandler')
    async def test_client_passes_ssl_params_to_handler(self, mock_handler_class):
        """Test that PooldoseClient passes SSL parameters to RequestHandler."""
        mock_handler = AsyncMock()
        mock_handler.connect.return_value = RequestStatus.HOST_UNREACHABLE
        mock_handler_class.return_value = mock_handler

        client = PooldoseClient(
            "example.com",
            timeout=15,
            use_ssl=True,
            port=8443,
            ssl_verify=False
        )

        status = await client.connect()

        # Verify RequestHandler was created with correct SSL parameters
        mock_handler_class.assert_called_once_with(
            "example.com",
            15,
            websession=None,
            use_ssl=True,
            port=8443,
            ssl_verify=False
        )
        assert status == RequestStatus.HOST_UNREACHABLE

    @pytest.mark.asyncio
    @patch('pooldose.client.RequestHandler')
    async def test_client_default_ssl_params_to_handler(self, mock_handler_class):
        """Test that PooldoseClient passes default SSL parameters to RequestHandler."""
        mock_handler = AsyncMock()
        mock_handler.connect.return_value = RequestStatus.HOST_UNREACHABLE
        mock_handler_class.return_value = mock_handler

        client = PooldoseClient("example.com", timeout=20)
        status = await client.connect()

        # Verify RequestHandler was created with default SSL parameters
        mock_handler_class.assert_called_once_with(
            "example.com",
            20,
            websession=None,
            use_ssl=False,
            port=None,
            ssl_verify=True
        )
        assert status == RequestStatus.HOST_UNREACHABLE


class TestSSLIntegration:
    """Integration tests for SSL functionality."""

    @pytest.mark.asyncio
    async def test_ssl_host_unreachable(self):
        """Test SSL connection to unreachable host."""
        client = PooldoseClient("256.256.256.256", timeout=1, use_ssl=True)
        status = await client.connect()
        assert status == RequestStatus.HOST_UNREACHABLE

    @pytest.mark.asyncio
    async def test_ssl_with_custom_port_unreachable(self):
        """Test SSL connection with custom port to unreachable host."""
        client = PooldoseClient("256.256.256.256", timeout=1, use_ssl=True, port=8443)
        status = await client.connect()
        assert status == RequestStatus.HOST_UNREACHABLE

    def test_ssl_backward_compatibility(self):
        """Test that existing code without SSL parameters still works."""
        # This should work exactly as before
        client = PooldoseClient("example.com", timeout=30, include_sensitive_data=True)
        assert client._use_ssl is False
        assert client._port is None
        assert client._ssl_verify is True

        handler = RequestHandler("example.com", timeout=10)
        assert handler.use_ssl is False
        assert handler.port == 80
        assert handler.ssl_verify is True
        assert handler._ssl_context is None
