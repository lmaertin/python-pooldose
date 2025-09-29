"""Tests for the pooldose client module."""

from unittest.mock import AsyncMock, patch

import pytest
from pooldose.client import PooldoseClient
from pooldose.request_status import RequestStatus
from pooldose.values.instant_values import InstantValues
from pooldose.values.static_values import StaticValues

# pylint: disable=line-too-long

class TestPooldoseClient:
    """Test PooldoseClient functionality."""

    @pytest.mark.asyncio
    async def test_init(self):
        """Test client initialization sets up the object with expected defaults."""
        # Create client with minimal parameters
        client = PooldoseClient(host="192.168.1.100")

        # Test public properties and behavior before connection
        assert client.is_connected is False
        assert client.device_info["NAME"] is None

        # We can't check private attributes in a black-box test, so we focus
        # on testing the behavior and public properties instead of implementation details

    @pytest.mark.asyncio
    async def test_connect_success(
        self, mock_request_handler, mock_debug_config, mock_mapping_info
    ):
        """Test successful connection."""
        client = PooldoseClient(host="192.168.1.100")

        mock_request_handler.get_debug_config.return_value = (
            RequestStatus.SUCCESS, mock_debug_config
        )
        mock_request_handler.get_wifi_station.return_value = (
            RequestStatus.SUCCESS, {"IP": "192.168.1.100"}
        )
        mock_request_handler.get_access_point.return_value = (RequestStatus.SUCCESS, {})
        mock_request_handler.get_network_info.return_value = (RequestStatus.SUCCESS, {})

        with patch('pooldose.client.RequestHandler', return_value=mock_request_handler):
            with patch(
                'pooldose.mappings.mapping_info.MappingInfo.load',
                return_value=mock_mapping_info
            ):
                status = await client.connect()

        assert status == RequestStatus.SUCCESS
        assert client.is_connected is True
        assert client.device_info["SERIAL_NUMBER"] == "TEST123"
        assert client.device_info["MODEL"] == "PDPR1H1HAW100"

    @pytest.mark.asyncio
    async def test_connect_request_handler_failure(self):
        """Test connection failure when RequestHandler fails."""
        client = PooldoseClient(host="192.168.1.100")

        mock_handler = AsyncMock()
        mock_handler.connect.return_value = RequestStatus.HOST_UNREACHABLE

        with patch('pooldose.client.RequestHandler', return_value=mock_handler):
            status = await client.connect()

        assert status == RequestStatus.HOST_UNREACHABLE
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_debug_config_failure(self):
        """Test connection failure when debug config fails."""
        client = PooldoseClient(host="192.168.1.100")

        mock_handler = AsyncMock()
        mock_handler.connect.return_value = RequestStatus.SUCCESS
        mock_handler.get_debug_config.return_value = (RequestStatus.PARAMS_FETCH_FAILED, None)

        with patch('pooldose.client.RequestHandler', return_value=mock_handler):
            status = await client.connect()

        assert status == RequestStatus.PARAMS_FETCH_FAILED
        assert client.is_connected is False

    def test_static_values(self, mock_device_info):
        """Test static values retrieval."""
        client = PooldoseClient(host="192.168.1.100")
        client.device_info.update(mock_device_info)

        status, static_values = client.static_values()

        assert status == RequestStatus.SUCCESS
        assert isinstance(static_values, StaticValues)
        assert static_values.sensor_name == "Test Device"
        assert static_values.sensor_serial_number == "TEST123"

    def test_static_values_error(self):
        """Test static values with exception during creation."""
        client = PooldoseClient(host="192.168.1.100")

        # Mock StaticValues to raise an exception
        with patch('pooldose.client.StaticValues') as mock_static_values:
            mock_static_values.side_effect = ValueError("Invalid device info")

            status, static_values = client.static_values()

            assert status == RequestStatus.UNKNOWN_ERROR
            assert static_values is None

    @pytest.mark.asyncio
    async def test_instant_values_success(self, mock_request_handler, mock_device_info,
                                         mock_mapping_info, mock_raw_data):
        """Test successful instant values retrieval."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = mock_request_handler
        client.device_info.update(mock_device_info)
        client._mapping_info = mock_mapping_info

        mock_request_handler.get_values_raw.return_value = (RequestStatus.SUCCESS, mock_raw_data)

        status, instant_values = await client.instant_values()

        assert status == RequestStatus.SUCCESS
        assert isinstance(instant_values, InstantValues)

    @pytest.mark.asyncio
    async def test_instant_values_failure(self, mock_request_handler, mock_device_info):
        """Test instant values retrieval failure."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = mock_request_handler
        client.device_info.update(mock_device_info)

        mock_request_handler.get_values_raw.return_value = (RequestStatus.HOST_UNREACHABLE, None)

        status, instant_values = await client.instant_values()

        assert status == RequestStatus.HOST_UNREACHABLE
        assert instant_values is None

    @pytest.mark.asyncio
    async def test_instant_values_no_mapping(self, mock_request_handler, mock_device_info,
                                            mock_raw_data):
        """Test instant values when mapping is None."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = mock_request_handler
        client.device_info.update(mock_device_info)
        client._mapping_info = None

        mock_request_handler.get_values_raw.return_value = (RequestStatus.SUCCESS, mock_raw_data)

        status, instant_values = await client.instant_values()

        assert status == RequestStatus.UNKNOWN_ERROR
        assert instant_values is None

    @pytest.mark.asyncio
    async def test_instant_values_structured_success(self, complete_client_setup):
        """Test successful structured instant values retrieval."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = complete_client_setup["request_handler"]
        client.device_info.update(complete_client_setup["device_info"])
        client._mapping_info = complete_client_setup["mapping_info"]

        complete_client_setup["request_handler"].get_values_raw.return_value = (
            RequestStatus.SUCCESS, complete_client_setup["raw_data"]
        )

        # Mock the InstantValues.to_structured_dict method directly
        with patch(
            'pooldose.values.instant_values.InstantValues.to_structured_dict'
        ) as mock_to_structured:
            mock_to_structured.return_value = complete_client_setup["structured_data"]
            status, structured_data = await client.instant_values_structured()

        assert status == RequestStatus.SUCCESS
        assert isinstance(structured_data, dict)
        assert "sensor" in structured_data
        assert "number" in structured_data
        assert "temperature" in structured_data["sensor"]
        assert "target_ph" in structured_data["number"]

    @pytest.mark.asyncio
    async def test_instant_values_structured_failure(self, mock_request_handler, mock_device_info):
        """Test structured instant values retrieval failure."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = mock_request_handler
        client.device_info.update(mock_device_info)

        mock_request_handler.get_values_raw.return_value = (RequestStatus.NO_DATA, None)

        status, structured_data = await client.instant_values_structured()

        assert status == RequestStatus.NO_DATA
        assert structured_data == {}

    @pytest.mark.asyncio
    async def test_instant_values_structured_error_in_processing(self, mock_request_handler,
                                                                mock_device_info, mock_mapping_info,
                                                                mock_raw_data):
        """Test structured instant values with error during processing."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = mock_request_handler
        client.device_info.update(mock_device_info)
        client._mapping_info = mock_mapping_info

        mock_request_handler.get_values_raw.return_value = (RequestStatus.SUCCESS, mock_raw_data)

        # Mock InstantValues.to_structured_dict to raise an exception
        with patch(
            'pooldose.values.instant_values.InstantValues.to_structured_dict'
        ) as mock_to_structured:
            mock_to_structured.side_effect = ValueError("Processing error")
            status, structured_data = await client.instant_values_structured()

        assert status == RequestStatus.UNKNOWN_ERROR
        assert structured_data == {}

    def test_check_apiversion_supported_success(self, mock_request_handler):
        """Test API version check success."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = mock_request_handler
        mock_request_handler.api_version = "v1/"

        status, result = client.check_apiversion_supported()

        assert status == RequestStatus.SUCCESS
        assert result["api_version_is"] == "v1/"
        assert result["api_version_should"] == "v1/"

    def test_check_apiversion_unsupported(self, mock_request_handler):
        """Test API version check with unsupported version."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = mock_request_handler
        mock_request_handler.api_version = "v2/"

        status, result = client.check_apiversion_supported()

        assert status == RequestStatus.API_VERSION_UNSUPPORTED
        assert result["api_version_is"] == "v2/"
        assert result["api_version_should"] == "v1/"

    def test_check_apiversion_no_data(self, mock_request_handler):
        """Test API version check with no version set."""
        client = PooldoseClient(host="192.168.1.100")
        # pylint: disable=protected-access
        client._request_handler = mock_request_handler
        mock_request_handler.api_version = None

        status, result = client.check_apiversion_supported()

        assert status == RequestStatus.NO_DATA
        assert result["api_version_is"] is None
        assert result["api_version_should"] == "v1/"

    def test_is_connected_property(self):
        """Test is_connected property."""
        client = PooldoseClient(host="192.168.1.100")

        assert client.is_connected is False

        # pylint: disable=protected-access
        client._connected = True
        assert client.is_connected is True
