"""Integration tests for DeviceAnalyzer CLI functionality."""
# pylint: disable=redefined-outer-name,protected-access,line-too-long

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pooldose.__main__ import run_device_analyzer
from pooldose.request_handler import RequestHandler
from pooldose.request_status import RequestStatus


@pytest.fixture
def sample_test_data():
    """Sample test data for integration tests."""
    instant_values = {
        "devicedata": {
            "TEST_DEVICE_001": {
                "deviceInfo": {"version": "2.10"},
                "collapsed_bar": True,
                "TESTMODEL_FW123_w_test1": {
                    "current": 7.2,
                    "magnitude": ["pH"],
                    "absMin": 6.0,
                    "absMax": 8.0,
                    "resolution": 0.1,
                    "visible": True
                },
                "TESTMODEL_FW123_w_test2": {
                    "current": "|TESTMODEL_FW123_LABEL_w_test2_ENABLED|",
                    "magnitude": ["UNDEFINED"],
                    "absMin": 0,
                    "absMax": 1,
                    "visible": True,
                    "comboitems": [
                        [0, "TESTMODEL_FW123_LABEL_w_test2_DISABLED"],
                        [1, "TESTMODEL_FW123_LABEL_w_test2_ENABLED"]
                    ]
                },
                "TESTMODEL_FW123_w_test3": {
                    "current": 25.5,
                    "magnitude": ["°C"],
                    "absMin": 0,
                    "absMax": 50,
                    "visible": False  # Hidden widget
                }
            }
        }
    }

    device_language = {
        "TESTMODEL_FW123_w_test1_PH": "pH Level",
        "TESTMODEL_FW123_w_test2_STATUS": "System Status",
        "TESTMODEL_FW123_LABEL_w_test2_DISABLED": "Disabled",
        "TESTMODEL_FW123_LABEL_w_test2_ENABLED": "Enabled",
        "TESTMODEL_FW123_w_test3_TEMP": "Temperature"
    }

    return instant_values, device_language


class TestDeviceAnalyzerIntegration:
    """Integration tests for DeviceAnalyzer CLI functionality."""

    @pytest.mark.asyncio
    async def test_run_device_analyzer_success(self, sample_test_data, capsys):
        """Test successful device analyzer run with visible widgets only."""
        instant_values, device_language = sample_test_data

        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(return_value=RequestStatus.SUCCESS)
            mock_handler.get_values_raw = AsyncMock(return_value=(RequestStatus.SUCCESS, instant_values))
            mock_handler.get_device_language = AsyncMock(return_value=(RequestStatus.SUCCESS, device_language))
            mock_handler.software_version = "2.10"
            mock_handler.api_version = "v1/"
            mock_handler_class.return_value = mock_handler

            # Run analyzer
            await run_device_analyzer("test_host", False, 80, show_all=False)

            # Check output
            captured = capsys.readouterr()

            # Verify basic output structure
            assert "Analyzing unknown device at test_host" in captured.out
            assert "Using HTTP on port 80" in captured.out
            assert "Showing only VISIBLE widgets" in captured.out
            assert "Testing connection..." in captured.out
            assert "Host is reachable" in captured.out
            assert "Connected successfully" in captured.out
            assert "Software Version: 2.10" in captured.out
            assert "API Version: v1/" in captured.out
            assert "DEVICE ANALYSIS RESULTS" in captured.out

            # Verify widget output - should show only visible widgets
            assert "pH Level" in captured.out
            assert "System Status" in captured.out
            assert "Temperature" not in captured.out  # Hidden widget
            assert "1 hidden widgets not shown" in captured.out

    @pytest.mark.asyncio
    async def test_run_device_analyzer_show_all(self, sample_test_data, capsys):
        """Test device analyzer run showing all widgets including hidden ones."""
        instant_values, device_language = sample_test_data

        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(return_value=RequestStatus.SUCCESS)
            mock_handler.get_values_raw = AsyncMock(return_value=(RequestStatus.SUCCESS, instant_values))
            mock_handler.get_device_language = AsyncMock(return_value=(RequestStatus.SUCCESS, device_language))
            mock_handler.software_version = "2.10"
            mock_handler.api_version = "v1/"
            mock_handler_class.return_value = mock_handler

            # Run analyzer with show_all=True
            await run_device_analyzer("test_host", False, 80, show_all=True)

            # Check output
            captured = capsys.readouterr()

            # Verify that all widgets are shown
            assert "Showing ALL widgets (including hidden ones)" in captured.out
            assert "pH Level" in captured.out
            assert "System Status" in captured.out
            assert "Temperature" in captured.out  # Hidden widget should now be shown
            assert "HIDDEN" in captured.out  # Should mark hidden widget
            assert "hidden widgets not shown" not in captured.out

    @pytest.mark.asyncio
    async def test_run_device_analyzer_https(self, sample_test_data, capsys):
        """Test device analyzer run with HTTPS."""
        instant_values, device_language = sample_test_data

        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(return_value=RequestStatus.SUCCESS)
            mock_handler.get_values_raw = AsyncMock(return_value=(RequestStatus.SUCCESS, instant_values))
            mock_handler.get_device_language = AsyncMock(return_value=(RequestStatus.SUCCESS, device_language))
            mock_handler.software_version = "2.10"
            mock_handler.api_version = "v1/"
            mock_handler_class.return_value = mock_handler

            # Run analyzer with HTTPS
            await run_device_analyzer("test_host", True, 443, show_all=False)

            # Check output
            captured = capsys.readouterr()

            # Verify HTTPS configuration
            assert "Using HTTPS on port 443" in captured.out

            # Verify RequestHandler was created with correct SSL settings
            mock_handler_class.assert_called_once_with(
                host="test_host",
                timeout=30,
                use_ssl=True,
                port=443,
                ssl_verify=False
            )

    @pytest.mark.asyncio
    async def test_run_device_analyzer_host_unreachable(self, capsys):
        """Test device analyzer when host is unreachable."""
        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = False
            mock_handler_class.return_value = mock_handler

            # Run analyzer
            await run_device_analyzer("unreachable_host", False, 80, show_all=False)

            # Check output
            captured = capsys.readouterr()

            assert "Testing connection..." in captured.out
            assert "Host not reachable!" in captured.out
            # Should not proceed to connection
            assert "Connecting and initializing..." not in captured.out

    @pytest.mark.asyncio
    async def test_run_device_analyzer_connection_failed(self, capsys):
        """Test device analyzer when connection fails."""
        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(return_value=RequestStatus.UNKNOWN_ERROR)
            mock_handler_class.return_value = mock_handler

            # Run analyzer
            await run_device_analyzer("test_host", False, 80, show_all=False)

            # Check output
            captured = capsys.readouterr()

            assert "Host is reachable" in captured.out
            assert "Connecting and initializing..." in captured.out
            assert "Connection failed: RequestStatus.UNKNOWN_ERROR" in captured.out
            # Should not proceed to analysis
            assert "DEVICE ANALYSIS RESULTS" not in captured.out

    @pytest.mark.asyncio
    async def test_run_device_analyzer_analysis_failed(self, capsys):
        """Test device analyzer when analysis fails."""
        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(return_value=RequestStatus.SUCCESS)
            mock_handler.get_values_raw = AsyncMock(return_value=(RequestStatus.UNKNOWN_ERROR, {}))
            mock_handler.software_version = "2.10"
            mock_handler.api_version = "v1/"
            mock_handler_class.return_value = mock_handler

            # Run analyzer
            await run_device_analyzer("test_host", False, 80, show_all=False)

            # Check output
            captured = capsys.readouterr()

            assert "Connected successfully" in captured.out
            assert "Analysis failed: RequestStatus.UNKNOWN_ERROR" in captured.out
            # Should not show analysis results
            assert "DEVICE ANALYSIS RESULTS" not in captured.out

    @pytest.mark.asyncio
    async def test_run_device_analyzer_network_error(self, capsys):
        """Test device analyzer when network error occurs."""
        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(side_effect=ConnectionError("Network error"))
            mock_handler_class.return_value = mock_handler

            # Run analyzer
            await run_device_analyzer("test_host", False, 80, show_all=False)

            # Check output
            captured = capsys.readouterr()

            assert "Network error: Network error" in captured.out

    @pytest.mark.asyncio
    async def test_run_device_analyzer_unexpected_error(self, capsys):
        """Test device analyzer when unexpected error occurs."""
        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(side_effect=ValueError("Unexpected error"))
            mock_handler_class.return_value = mock_handler

            # Run analyzer
            await run_device_analyzer("test_host", False, 80, show_all=False)

            # Check output
            captured = capsys.readouterr()

            assert "Error during analysis: Unexpected error" in captured.out

    @pytest.mark.asyncio
    async def test_run_device_analyzer_with_possible_values(self, capsys):
        """Test device analyzer output includes possible values."""
        # Extended test data with more complex device language
        instant_values = {
            "devicedata": {
                "TEST_DEVICE_001": {
                    "TESTMODEL_FW123_w_combo": {
                        "current": "|TESTMODEL_FW123_LABEL_w_combo_OPTION1|",
                        "magnitude": ["UNDEFINED"],
                        "absMin": 0,
                        "absMax": 2,
                        "visible": True,
                        "comboitems": [
                            [0, "TESTMODEL_FW123_LABEL_w_combo_OPTION1"],
                            [1, "TESTMODEL_FW123_LABEL_w_combo_OPTION2"],
                            [2, "TESTMODEL_FW123_LABEL_w_combo_OPTION3"]
                        ]
                    }
                }
            }
        }

        device_language = {
            "TESTMODEL_FW123_w_combo_SELECTOR": "Test Selector",
            "TESTMODEL_FW123_LABEL_w_combo_OPTION1": "Option 1",
            "TESTMODEL_FW123_LABEL_w_combo_OPTION2": "Option 2",
            "TESTMODEL_FW123_LABEL_w_combo_OPTION3": "Option 3"
        }

        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(return_value=RequestStatus.SUCCESS)
            mock_handler.get_values_raw = AsyncMock(return_value=(RequestStatus.SUCCESS, instant_values))
            mock_handler.get_device_language = AsyncMock(return_value=(RequestStatus.SUCCESS, device_language))
            mock_handler.software_version = "2.10"
            mock_handler.api_version = "v1/"
            mock_handler_class.return_value = mock_handler

            # Run analyzer
            await run_device_analyzer("test_host", False, 80, show_all=True)

            # Check output
            captured = capsys.readouterr()

            # Verify combo items are shown
            assert "Combo Items:" in captured.out
            assert "0: TESTMODEL_FW123_LABEL_w_combo_OPTION1" in captured.out

            # Verify possible values are shown
            assert "Possible Values:" in captured.out
            assert "TESTMODEL_FW123_LABEL_w_combo_OPTION1: Option 1" in captured.out
            assert "TESTMODEL_FW123_LABEL_w_combo_OPTION2: Option 2" in captured.out
            assert "TESTMODEL_FW123_LABEL_w_combo_OPTION3: Option 3" in captured.out

    @pytest.mark.asyncio
    async def test_run_device_analyzer_no_labels(self, sample_test_data, capsys):
        """Test device analyzer when label fetch fails."""
        instant_values, _ = sample_test_data

        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(return_value=RequestStatus.SUCCESS)
            mock_handler.get_values_raw = AsyncMock(return_value=(RequestStatus.SUCCESS, instant_values))
            mock_handler.get_device_language = AsyncMock(return_value=(RequestStatus.UNKNOWN_ERROR, {}))
            mock_handler.software_version = "2.10"
            mock_handler.api_version = "v1/"
            mock_handler_class.return_value = mock_handler

            # Run analyzer
            await run_device_analyzer("test_host", False, 80, show_all=False)

            # Check output
            captured = capsys.readouterr()

            # Should still show analysis but with default labels
            assert "DEVICE ANALYSIS RESULTS" in captured.out
            assert "Warning: Could not fetch labels" in captured.out
            # All widgets should have default label
            lines = captured.out.split('\n')
            label_lines = [line for line in lines if "Label: " in line]
            assert all("N/A" in line for line in label_lines)

    @pytest.mark.asyncio
    async def test_run_device_analyzer_custom_port(self, sample_test_data, capsys):
        """Test device analyzer with custom port."""
        instant_values, device_language = sample_test_data

        with patch('pooldose.__main__.RequestHandler') as mock_handler_class:
            # Setup mocks
            mock_handler = MagicMock(spec=RequestHandler)
            mock_handler.check_host_reachable.return_value = True
            mock_handler.connect = AsyncMock(return_value=RequestStatus.SUCCESS)
            mock_handler.get_values_raw = AsyncMock(return_value=(RequestStatus.SUCCESS, instant_values))
            mock_handler.get_device_language = AsyncMock(return_value=(RequestStatus.SUCCESS, device_language))
            mock_handler.software_version = "2.10"
            mock_handler.api_version = "v1/"
            mock_handler_class.return_value = mock_handler

            # Run analyzer with custom port
            await run_device_analyzer("test_host", False, 8080, show_all=False)

            # Check output
            captured = capsys.readouterr()

            # Verify custom port is shown
            assert "Using HTTP on port 8080" in captured.out

            # Verify RequestHandler was created with correct port
            mock_handler_class.assert_called_once_with(
                host="test_host",
                timeout=30,
                use_ssl=False,
                port=8080,
                ssl_verify=False
            )
