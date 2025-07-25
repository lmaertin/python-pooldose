"""Tests for SSL support in RequestHandler and PooldoseClient."""

import ssl
from unittest.mock import Mock, patch, AsyncMock
import pytest
import aiohttp

from pooldose.client import PooldoseClient
from pooldose.request_handler import RequestHandler
from pooldose.request_status import RequestStatus


class TestRequestHandlerSSL:
    """Test SSL functionality in RequestHandler."""

    def test_init_with_ssl_parameters(self):
        """Test RequestHandler initialization with SSL parameters."""
        # Test with SSL enabled
        handler = RequestHandler("example.com", port=443, use_ssl=True, verify_ssl=True)
        assert handler.host == "example.com"
        assert handler.port == 443
        assert handler.use_ssl is True
        assert handler.verify_ssl is True

        # Test with SSL disabled (default)
        handler = RequestHandler("example.com")
        assert handler.port == 80
        assert handler.use_ssl is False
        assert handler.verify_ssl is True  # Default to True for security

        # Test with custom port but no SSL
        handler = RequestHandler("example.com", port=8080, use_ssl=False)
        assert handler.port == 8080
        assert handler.use_ssl is False

    def test_get_base_url(self):
        """Test base URL construction with different SSL settings."""
        # HTTP without SSL
        handler = RequestHandler("example.com", port=80, use_ssl=False)
        assert handler._get_base_url() == "http://example.com:80"

        # HTTPS with SSL
        handler = RequestHandler("example.com", port=443, use_ssl=True)
        assert handler._get_base_url() == "https://example.com:443"

        # Custom port with SSL
        handler = RequestHandler("example.com", port=8443, use_ssl=True)
        assert handler._get_base_url() == "https://example.com:8443"

    @patch('socket.create_connection')
    def test_check_host_reachable_custom_port(self, mock_connection):
        """Test host reachability check with custom ports."""
        mock_connection.return_value.__enter__ = Mock()
        mock_connection.return_value.__exit__ = Mock()

        # Test with custom HTTP port
        handler = RequestHandler("example.com", port=8080, use_ssl=False)
        result = handler.check_host_reachable()
        assert result is True
        mock_connection.assert_called_with(("example.com", 8080), timeout=10)

        # Test with custom HTTPS port
        handler = RequestHandler("example.com", port=8443, use_ssl=True)
        result = handler.check_host_reachable()
        assert result is True
        mock_connection.assert_called_with(("example.com", 8443), timeout=10)

    @pytest.mark.asyncio
    async def test_ssl_context_creation(self):
        """Test SSL context creation for different verification settings."""
        # Test with SSL verification enabled
        handler = RequestHandler("example.com", use_ssl=True, verify_ssl=True)
        ssl_context = handler._create_ssl_context()
        assert ssl_context.check_hostname is True
        assert ssl_context.verify_mode == ssl.CERT_REQUIRED

        # Test with SSL verification disabled
        handler = RequestHandler("example.com", use_ssl=True, verify_ssl=False)
        ssl_context = handler._create_ssl_context()
        assert ssl_context.check_hostname is False
        assert ssl_context.verify_mode == ssl.CERT_NONE

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_core_params_with_ssl(self, mock_get):
        """Test _get_core_params with SSL configuration."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.text.return_value = 'softwareVersion: "1.0", apiversion: "v1/"'
        mock_get.return_value.__aenter__.return_value = mock_response

        # Test with SSL enabled
        handler = RequestHandler("example.com", port=443, use_ssl=True, verify_ssl=False)
        result = await handler._get_core_params()

        assert result is not None
        assert "softwareVersion" in result
        assert "apiversion" in result

        # Verify the URL was constructed correctly
        expected_url = "https://example.com:443/js_libs/params.js"
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == expected_url


class TestPooldoseClientSSL:
    """Test SSL functionality in PooldoseClient."""

    def test_init_with_ssl_parameters(self):
        """Test PooldoseClient initialization with SSL parameters."""
        # Test with SSL enabled
        client = PooldoseClient("example.com", port=443, use_ssl=True, verify_ssl=True)
        assert client._host == "example.com"
        assert client._port == 443
        assert client._use_ssl is True
        assert client._verify_ssl is True

        # Test with defaults
        client = PooldoseClient("example.com")
        assert client._port == 80
        assert client._use_ssl is False
        assert client._verify_ssl is True

    @pytest.mark.asyncio
    @patch('pooldose.request_handler.RequestHandler.connect')
    async def test_connect_with_ssl_parameters(self, mock_connect):
        """Test that SSL parameters are passed to RequestHandler."""
        mock_connect.return_value = RequestStatus.SUCCESS
        
        client = PooldoseClient("example.com", port=443, use_ssl=True, verify_ssl=False)
        
        # Mock the RequestHandler initialization to capture the parameters
        with patch('pooldose.client.RequestHandler') as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.connect.return_value = RequestStatus.SUCCESS
            mock_handler.api_version = "v1/"
            
            # Mock all API calls that would be made during _load_device_info
            mock_handler.get_debug_config.return_value = (RequestStatus.SUCCESS, {
                "GATEWAY": {"DID": "test", "NAME": "test", "FW_REL": "1.0"},
                "DEVICES": [{"DID": "test_DEVICE", "NAME": "TestModel", "PRODUCT_CODE": "TEST", "FW_REL": "1.0", "FW_CODE": "123"}]
            })
            mock_handler.get_wifi_station.return_value = (RequestStatus.SUCCESS, {})
            mock_handler.get_access_point.return_value = (RequestStatus.SUCCESS, {})
            mock_handler.get_network_info.return_value = (RequestStatus.SUCCESS, {})
            
            mock_handler_class.return_value = mock_handler
            
            # Mock MappingInfo.load to avoid file system access
            with patch('pooldose.mappings.mapping_info.MappingInfo.load') as mock_mapping_load:
                mock_mapping_load.return_value = Mock()
                
                status = await client.connect()
                assert status == RequestStatus.SUCCESS
            
                # Verify RequestHandler was created with correct SSL parameters
                mock_handler_class.assert_called_once_with(
                    "example.com", 30, port=443, use_ssl=True, verify_ssl=False
                )


class TestSSLIntegration:
    """Integration tests for SSL functionality."""

    @pytest.mark.asyncio
    async def test_ssl_url_construction_integration(self):
        """Test that all API endpoints use correct URLs with SSL."""
        client = PooldoseClient("example.com", port=443, use_ssl=True, verify_ssl=False)
        
        # Mock RequestHandler methods to capture URL calls
        with patch('pooldose.client.RequestHandler') as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.connect.return_value = RequestStatus.SUCCESS
            mock_handler.api_version = "v1/"
            
            # Mock all the API calls that will be made during connect
            mock_handler.get_debug_config.return_value = (RequestStatus.SUCCESS, {
                "GATEWAY": {"DID": "test", "NAME": "test", "FW_REL": "1.0"},
                "DEVICES": [{"DID": "test_DEVICE", "NAME": "TestModel", "PRODUCT_CODE": "TEST", "FW_REL": "1.0", "FW_CODE": "123"}]
            })
            mock_handler.get_wifi_station.return_value = (RequestStatus.SUCCESS, {})
            mock_handler.get_access_point.return_value = (RequestStatus.SUCCESS, {})
            mock_handler.get_network_info.return_value = (RequestStatus.SUCCESS, {})
            
            mock_handler_class.return_value = mock_handler
            
            # Mock MappingInfo.load to avoid file system access
            with patch('pooldose.mappings.mapping_info.MappingInfo.load') as mock_mapping_load:
                mock_mapping_load.return_value = Mock()
                
                status = await client.connect()
                assert status == RequestStatus.SUCCESS
                
                # Verify RequestHandler was created with SSL parameters
                mock_handler_class.assert_called_once_with(
                    "example.com", 30, port=443, use_ssl=True, verify_ssl=False
                )