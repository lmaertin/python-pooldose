"""Tests for DeviceAnalyzer functionality."""
# pylint: disable=redefined-outer-name,protected-access,line-too-long,too-few-public-methods,too-many-public-methods

from unittest.mock import AsyncMock, MagicMock

import pytest

from pooldose.device_analyzer import DeviceAnalyzer, DeviceInfo, WidgetInfo
from pooldose.request_handler import RequestHandler
from pooldose.request_status import RequestStatus


@pytest.fixture
def mock_request_handler():
    """Create a mock request handler for testing."""
    handler = MagicMock(spec=RequestHandler)
    handler.get_values_raw = AsyncMock()
    handler.get_device_language = AsyncMock()
    return handler


@pytest.fixture
def sample_instant_values():
    """Sample instant values data for testing."""
    return {
        "devicedata": {
            "01220000095B_DEVICE": {
                "deviceInfo": {"version": "2.10"},
                "collapsed_bar": True,
                "PDPR1H1HAW100_FW539187_w_1ekeigkin": {
                    "current": 7.2,
                    "magnitude": ["pH"],
                    "absMin": 0,
                    "absMax": 14,
                    "resolution": 0.1,
                    "visible": True
                },
                "PDPR1H1HAW100_FW539187_w_1eklenb23": {
                    "current": 729,
                    "magnitude": ["mV"],
                    "absMin": -99,
                    "absMax": 999,
                    "visible": True
                },
                "PDPR1H1HAW100_FW539187_w_1eklj6euj": {
                    "current": "|PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_PROPORTIONAL|",
                    "magnitude": ["UNDEFINED"],
                    "absMin": 0,
                    "absMax": 3,
                    "visible": True,
                    "comboitems": [
                        [0, "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_OFF"],
                        [1, "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_PROPORTIONAL"],
                        [2, "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_ON_OFF"],
                        [3, "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_TIMED"]
                    ]
                },
                "PDPR1H1HAW100_FW539187_w_1eklinki6": {
                    "current": 0,
                    "magnitude": ["UNDEFINED"],
                    "absMin": 0,
                    "absMax": 1,
                    "visible": False,
                    "comboitems": [
                        [0, "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_M_"],
                        [1, "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_LITER"]
                    ]
                }
            }
        }
    }


@pytest.fixture
def sample_device_language():
    """Sample device language data for testing."""
    return {
        "PDPR1H1HAW100_FW539187_w_1ekeigkin_PH_0": "pH",
        "PDPR1H1HAW100_FW539187_w_1eklenb23_ORP_1": "ORP",
        "PDPR1H1HAW100_FW539187_w_1eklj6euj_PERISTALTICDOSING_30": "Peristaltic pH Dosing",
        "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_OFF": "Off",
        "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_PROPORTIONAL": "Proportional",
        "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_ON_OFF": "On/Off",
        "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_TIMED": "Timed",
        "PDPR1H1HAW100_FW539187_w_1eklinki6_WATERMETERUNIT_27": "Water meter Unit",
        "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_M_": "m³",
        "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_LITER": "Liter"
    }


class TestDeviceInfo:
    """Test DeviceInfo class."""

    def test_device_info_creation(self):
        """Test DeviceInfo object creation."""
        device_info = DeviceInfo("test_device", "TEST_MODEL", "FW123")
        assert device_info.device_id == "test_device"
        assert device_info.model == "TEST_MODEL"
        assert device_info.fw_code == "FW123"


class TestWidgetInfo:
    """Test WidgetInfo class."""

    def test_widget_info_creation(self):
        """Test WidgetInfo object creation."""
        details = {"unit": "pH", "range": "0-14"}
        widget_info = WidgetInfo(
            key="full_key",
            short_key="short_key",
            label="Test Label",
            raw_value=7.2,
            details=details
        )
        assert widget_info.key == "full_key"
        assert widget_info.short_key == "short_key"
        assert widget_info.label == "Test Label"
        assert widget_info.raw_value == 7.2
        assert widget_info.details == details


class TestDeviceAnalyzer:
    """Test DeviceAnalyzer class."""

    def test_analyzer_creation(self, mock_request_handler):
        """Test DeviceAnalyzer creation with proper initialization."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        # In a black-box test, we should test behavior, not implementation details
        # So we check that the analyzer instance was created successfully
        assert isinstance(analyzer, DeviceAnalyzer)
        # We can't test handler directly as that's an implementation detail

    @pytest.mark.asyncio
    async def test_analyze_device_info(self, mock_request_handler, sample_instant_values, sample_device_language):
        """Test device info is correctly analyzed from raw device data."""
        # Setup
        analyzer = DeviceAnalyzer(mock_request_handler)
        mock_request_handler.get_values_raw.return_value = (RequestStatus.SUCCESS, sample_instant_values)
        mock_request_handler.get_device_language.return_value = (RequestStatus.SUCCESS, sample_device_language)

        # Exercise the public analyze_device method which should internally call _extract_device_info
        device_info, _, status = await analyzer.analyze_device()  # widgets not needed for this test

        # Verify the results via the public interface
        assert status == RequestStatus.SUCCESS
        assert device_info is not None
        assert device_info.device_id == "01220000095B_DEVICE"
        assert device_info.model == "PDPR1H1HAW100"
        assert device_info.fw_code == "FW539187"

    @pytest.mark.asyncio
    async def test_analyze_device_with_no_data(self, mock_request_handler):
        """Test device analysis when no data is available."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        mock_request_handler.get_values_raw.return_value = (RequestStatus.SUCCESS, {})

        device_info, _, status = await analyzer.analyze_device()

        # Based on implementation, it returns NO_DATA when device info can't be extracted
        assert status == RequestStatus.NO_DATA
        # Device_info should be None because no valid data was found
        assert device_info is None

    @pytest.mark.asyncio
    async def test_analyze_device_with_empty_devicedata(self, mock_request_handler):
        """Test device analysis when devicedata is empty."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        mock_request_handler.get_values_raw.return_value = (RequestStatus.SUCCESS, {"devicedata": {}})

        device_info, _, status = await analyzer.analyze_device()

        # Based on implementation, it returns NO_DATA when device info can't be extracted
        assert status == RequestStatus.NO_DATA
        # Device_info should be None because no valid device data was found
        assert device_info is None

    def test_extract_device_info_no_matching_pattern(self, mock_request_handler):
        """Test device info extraction with no matching pattern."""
        data = {
            "devicedata": {
                "test_device": {
                    "invalid_key": "value",
                    "another_invalid": "value"
                }
            }
        }
        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info = analyzer._extract_device_info(data)

        assert device_info is not None
        assert device_info.device_id == "test_device"
        assert device_info.model == "UNKNOWN"
        assert device_info.fw_code == "UNKNOWN"

    def test_extract_short_key(self, mock_request_handler):
        """Test short key extraction."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        full_key = "PDPR1H1HAW100_FW539187_w_1ekeigkin"
        short_key = analyzer._extract_short_key(full_key, "PDPR1H1HAW100", "FW539187")
        assert short_key == "w_1ekeigkin"

    def test_extract_short_key_no_prefix(self, mock_request_handler):
        """Test short key extraction when prefix doesn't match."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        full_key = "DIFFERENT_PREFIX_w_1ekeigkin"
        short_key = analyzer._extract_short_key(full_key, "PDPR1H1HAW100", "FW539187")
        assert short_key == "DIFFERENT_PREFIX_w_1ekeigkin"

    def test_extract_possible_values_from_labels(
        self, mock_request_handler, sample_device_language
    ):
        """Test extraction of possible values from device language."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        possible_values = analyzer._extract_possible_values_from_labels(
            "w_1eklj6euj", sample_device_language
        )

        expected_values = [
            "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_OFF: Off",
            "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_PROPORTIONAL: Proportional",
            "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_ON_OFF: On/Off",
            "PDPR1H1HAW100_FW539187_LABEL_w_1eklj6euj_TIMED: Timed"
        ]
        assert possible_values == expected_values

    def test_extract_possible_values_combo(
        self, mock_request_handler, sample_device_language
    ):
        """Test extraction of possible values for combo items."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        possible_values = analyzer._extract_possible_values_from_labels(
            "w_1eklinki6", sample_device_language
        )

        expected_values = [
            "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_M_: m³",
            "PDPR1H1HAW100_FW539187_COMBO_w_1eklinki6_LITER: Liter"
        ]
        assert possible_values == expected_values

    def test_extract_possible_values_no_matches(
        self, mock_request_handler, sample_device_language
    ):
        """Test extraction of possible values with no matches."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        possible_values = analyzer._extract_possible_values_from_labels(
            "w_nonexistent", sample_device_language
        )
        assert not possible_values

    def test_format_widget_details_simple(self, mock_request_handler):
        """Test formatting of simple widget details."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        widget_data = "simple_value"
        details = analyzer._format_widget_details(widget_data)

        expected = {"type": "simple", "data": "simple_value"}
        assert details == expected

    def test_format_widget_details_complex(self, mock_request_handler):
        """Test formatting of complex widget details."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        widget_data = {
            "magnitude": ["pH"],
            "absMin": 0,
            "absMax": 14,
            "resolution": 0.1,
            "visible": True,
            "alarm": False,
            "warning": True,
            "set": 7.0,
            "comboitems": [
                [0, "Option1"],
                [1, "Option2"]
            ]
        }
        details = analyzer._format_widget_details(widget_data)

        assert details["unit"] == "pH"
        assert details["range"] == "0 - 14"
        assert details["resolution"] == 0.1
        assert details["visible"] is True
        assert details["alarm"] is False
        assert details["warning"] is True
        assert details["set_value"] == 7.0
        assert details["combo_items"] == ["0: Option1", "1: Option2"]

    def test_format_widget_details_target_range(self, mock_request_handler):
        """Test formatting of widget details with target range."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        widget_data = {
            "minT": 6.0,
            "maxT": 8.0,
            "magnitude": ["pH"]
        }
        details = analyzer._format_widget_details(widget_data)

        assert details["target_range"] == "6.0 - 8.0"
        assert "range" not in details

    def test_get_widget_value_dict(self, mock_request_handler):
        """Test getting widget value from dict."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        widget_data = {"current": 7.2, "other": "value"}
        value = analyzer._get_widget_value(widget_data)
        assert value == 7.2

    def test_get_widget_value_dict_no_current(self, mock_request_handler):
        """Test getting widget value from dict without current key."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        widget_data = {"other": "value"}
        value = analyzer._get_widget_value(widget_data)
        assert value == widget_data

    def test_get_widget_value_simple(self, mock_request_handler):
        """Test getting widget value from simple value."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        widget_data = "simple_value"
        value = analyzer._get_widget_value(widget_data)
        assert value == "simple_value"

    def test_find_widget_label_found(
        self, mock_request_handler, sample_device_language
    ):
        """Test finding widget label when match exists."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        label = analyzer._find_widget_label(
            "PDPR1H1HAW100_FW539187_w_1ekeigkin",
            "w_1ekeigkin",
            sample_device_language
        )
        assert label == "pH"

    def test_find_widget_label_not_found(
        self, mock_request_handler, sample_device_language
    ):
        """Test finding widget label when no match exists."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        label = analyzer._find_widget_label(
            "nonexistent_key",
            "nonexistent",
            sample_device_language
        )
        assert label == "N/A"

    @pytest.mark.asyncio
    async def test_analyze_device_success(
        self, mock_request_handler, sample_instant_values, sample_device_language
    ):
        """Test successful device analysis."""
        mock_request_handler.get_values_raw.return_value = (
            RequestStatus.SUCCESS, sample_instant_values
        )
        mock_request_handler.get_device_language.return_value = (
            RequestStatus.SUCCESS, sample_device_language
        )

        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info, widgets, status = await analyzer.analyze_device()

        assert status == RequestStatus.SUCCESS
        assert device_info is not None
        assert device_info.device_id == "01220000095B_DEVICE"
        assert device_info.model == "PDPR1H1HAW100"
        assert device_info.fw_code == "FW539187"
        assert len(widgets) == 4  # 4 widgets in sample data (excluding skipped keys)

        # Check widget details
        ph_widget = next((w for w in widgets if w.short_key == "w_1ekeigkin"), None)
        assert ph_widget is not None
        assert ph_widget.label == "pH"
        assert ph_widget.raw_value == 7.2
        assert ph_widget.details["unit"] == "pH"
        assert ph_widget.details["range"] == "0 - 14"

    @pytest.mark.asyncio
    async def test_analyze_device_failed_instant_values(self, mock_request_handler):
        """Test device analysis when instant values fetch fails."""
        mock_request_handler.get_values_raw.return_value = (RequestStatus.UNKNOWN_ERROR, {})

        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info, widgets, status = await analyzer.analyze_device()

        assert status == RequestStatus.UNKNOWN_ERROR
        assert device_info is None
        assert widgets == []

    @pytest.mark.asyncio
    async def test_analyze_device_no_device_info(self, mock_request_handler):
        """Test device analysis when device info extraction fails."""
        mock_request_handler.get_values_raw.return_value = (RequestStatus.SUCCESS, {})

        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info, widgets, status = await analyzer.analyze_device()

        assert status == RequestStatus.NO_DATA
        assert device_info is None
        assert widgets == []

    @pytest.mark.asyncio
    async def test_analyze_device_failed_labels(
        self, mock_request_handler, sample_instant_values
    ):
        """Test device analysis when label fetch fails."""
        mock_request_handler.get_values_raw.return_value = (
            RequestStatus.SUCCESS, sample_instant_values
        )
        mock_request_handler.get_device_language.return_value = (
            RequestStatus.UNKNOWN_ERROR, {}
        )

        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info, widgets, status = await analyzer.analyze_device()

        assert status == RequestStatus.SUCCESS
        assert device_info is not None
        assert len(widgets) == 4  # Should still process widgets

        # All widgets should have default label
        for widget in widgets:
            assert widget.label == "N/A"

    def test_process_widgets(
        self, mock_request_handler, sample_instant_values, sample_device_language
    ):
        """Test widget processing."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info = DeviceInfo(
            "01220000095B_DEVICE", "PDPR1H1HAW100", "FW539187"
        )

        widgets = analyzer._process_widgets(
            sample_instant_values, device_info, sample_device_language
        )

        assert len(widgets) == 4

        # Check that skipped keys are not included
        widget_keys = [w.short_key for w in widgets]
        assert "deviceInfo" not in widget_keys
        assert "collapsed_bar" not in widget_keys

        # Check specific widgets
        ph_widget = next((w for w in widgets if w.short_key == "w_1ekeigkin"), None)
        assert ph_widget is not None
        assert ph_widget.label == "pH"

        combo_widget = next((w for w in widgets if w.short_key == "w_1eklj6euj"), None)
        assert combo_widget is not None
        assert "possible_values" in combo_widget.details
        assert len(combo_widget.details["possible_values"]) == 4

    def test_format_widget_detail_string(self, mock_request_handler):
        """Test formatting widget details into strings."""
        analyzer = DeviceAnalyzer(mock_request_handler)

        details = {
            "unit": "pH",
            "range": "0-14",
            "resolution": 0.1,
            "set_value": 7.0,
            "visible": False,
            "alarm": True,
            "warning": False
        }

        detail_strings = analyzer._format_widget_detail_string(details)

        expected = [
            "Unit: pH",
            "Range: 0-14",
            "Resolution: 0.1",
            "Set Value: 7.0",
            "HIDDEN",
            "ALARM"
        ]
        assert detail_strings == expected

    def test_format_widget_detail_string_target_range(self, mock_request_handler):
        """Test formatting widget details with target range instead of range."""
        analyzer = DeviceAnalyzer(mock_request_handler)

        details = {
            "target_range": "6.0-8.0",
            "unit": "pH"
        }

        detail_strings = analyzer._format_widget_detail_string(details)

        expected = [
            "Unit: pH",
            "Target Range: 6.0-8.0"
        ]
        assert detail_strings == expected

    def test_display_analysis_visible_only(self, mock_request_handler, capsys):
        """Test display analysis showing only visible widgets."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info = DeviceInfo("test_device", "TEST_MODEL", "FW123")

        # Create test widgets - one visible, one hidden
        visible_widget = WidgetInfo(
            key="visible_key",
            short_key="visible",
            label="Visible Widget",
            raw_value=123,
            details={"visible": True, "unit": "test"}
        )

        hidden_widget = WidgetInfo(
            key="hidden_key",
            short_key="hidden",
            label="Hidden Widget",
            raw_value=456,
            details={"visible": False, "unit": "test"}
        )

        widgets = [visible_widget, hidden_widget]

        analyzer.display_analysis(device_info, widgets, show_all=False)

        captured = capsys.readouterr()
        assert "Visible Widget" in captured.out
        assert "Hidden Widget" not in captured.out
        assert "1 hidden widgets not shown" in captured.out

    def test_display_analysis_show_all(self, mock_request_handler, capsys):
        """Test display analysis showing all widgets."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info = DeviceInfo("test_device", "TEST_MODEL", "FW123")

        # Create test widgets - one visible, one hidden
        visible_widget = WidgetInfo(
            key="visible_key",
            short_key="visible",
            label="Visible Widget",
            raw_value=123,
            details={"visible": True, "unit": "test"}
        )

        hidden_widget = WidgetInfo(
            key="hidden_key",
            short_key="hidden",
            label="Hidden Widget",
            raw_value=456,
            details={"visible": False, "unit": "test"}
        )

        widgets = [visible_widget, hidden_widget]

        analyzer.display_analysis(device_info, widgets, show_all=True)

        captured = capsys.readouterr()
        assert "Visible Widget" in captured.out
        assert "Hidden Widget" in captured.out
        assert "hidden widgets not shown" not in captured.out

    def test_display_analysis_no_widgets(self, mock_request_handler, capsys):
        """Test display analysis with no widgets to display."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info = DeviceInfo("test_device", "TEST_MODEL", "FW123")

        # Create only hidden widgets
        hidden_widget = WidgetInfo(
            key="hidden_key",
            short_key="hidden",
            label="Hidden Widget",
            raw_value=456,
            details={"visible": False, "unit": "test"}
        )

        widgets = [hidden_widget]

        analyzer.display_analysis(device_info, widgets, show_all=False)

        captured = capsys.readouterr()
        assert "No widgets to display" in captured.out

    def test_display_analysis_with_possible_values(self, mock_request_handler, capsys):
        """Test display analysis with possible values."""
        analyzer = DeviceAnalyzer(mock_request_handler)
        device_info = DeviceInfo("test_device", "TEST_MODEL", "FW123")

        widget = WidgetInfo(
            key="test_key",
            short_key="test",
            label="Test Widget",
            raw_value=0,
            details={
                "visible": True,
                "unit": "test",
                "combo_items": ["0: Option1", "1: Option2"],
                "possible_values": [
                    "TEST_MODEL_FW123_LABEL_test_OPT1: Option 1",
                    "TEST_MODEL_FW123_LABEL_test_OPT2: Option 2"
                ]
            }
        )

        widgets = [widget]

        analyzer.display_analysis(device_info, widgets, show_all=True)

        captured = capsys.readouterr()
        assert "Combo Items:" in captured.out
        assert "0: Option1" in captured.out
        assert "Possible Values:" in captured.out
        assert "TEST_MODEL_FW123_LABEL_test_OPT1: Option 1" in captured.out
