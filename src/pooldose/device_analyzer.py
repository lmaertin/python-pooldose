"""Device Analyzer for unknown Pooldose devices."""

import re
from typing import Any, Dict, List, Optional, Tuple

from pooldose.request_handler import RequestHandler
from pooldose.request_status import RequestStatus

# Constants for device analysis
SKIP_KEYS = ["deviceInfo", "collapsed_bar"]
UNKNOWN_MODEL = "UNKNOWN"
UNKNOWN_FW_CODE = "UNKNOWN"
DEFAULT_LABEL = "N/A"
SEPARATOR_LENGTH = 150
DETAIL_SEPARATOR_LENGTH = 100


class DeviceInfo:  # pylint: disable=too-few-public-methods
    """Container for device information."""

    def __init__(self, device_id: str, model: str, fw_code: str):
        self.device_id = device_id
        self.model = model
        self.fw_code = fw_code


class WidgetInfo:  # pylint: disable=too-few-public-methods
    """Container for widget information."""

    # pylint: disable=too-many-arguments
    def __init__(self, *, key: str, short_key: str, label: str, raw_value: Any,
                 details: Dict[str, Any]):
        self.key = key
        self.short_key = short_key
        self.label = label
        self.raw_value = raw_value
        self.details = details


class DeviceAnalyzer:
    """Analyzer for unknown Pooldose devices."""

    def __init__(self, request_handler: RequestHandler):
        self.handler = request_handler

    def _extract_device_info(self, instant_values_data: dict) -> Optional[DeviceInfo]:
        """
        Extract device information from instant values data.

        Args:
            instant_values_data (dict): Raw instant values data

        Returns:
            DeviceInfo | None: Device information or None if extraction failed
        """
        try:
            device_data = instant_values_data.get("devicedata", {})
            if not device_data:
                return None

            # Get device ID (first key in devicedata)
            device_id = list(device_data.keys())[0]

            # Extract model and FW code from widget keys
            # Look for the first widget key that matches the pattern
            for key in device_data.get(device_id, {}):
                if key in SKIP_KEYS:
                    continue

                # Pattern: {MODEL}_{FW_CODE}_w_{SHORT_ID}
                match = re.match(r"^([A-Z0-9]+)_(FW[A-Z0-9]+)_", key)
                if match:
                    model = match.group(1)
                    fw_code = match.group(2)
                    return DeviceInfo(device_id, model, fw_code)

            return DeviceInfo(device_id, UNKNOWN_MODEL, UNKNOWN_FW_CODE)

        except (KeyError, IndexError, AttributeError) as e:
            print(f"Error extracting device info: {e}")
            return None

    def _extract_short_key(self, full_key: str, model: str, fw_code: str) -> str:
        """
        Extract short key from full widget key.

        Args:
            full_key (str): Full widget key (e.g., "PDPR1H1HAW100_FW539187_w_1ekeigkin")
            model (str): Device model
            fw_code (str): Firmware code

        Returns:
            str: Short key (e.g., "w_1ekeigkin")
        """
        prefix = f"{model}_{fw_code}_"
        if full_key.startswith(prefix):
            return full_key[len(prefix):]
        return full_key

    def _extract_possible_values_from_labels(self, short_key: str,
                                           labels_data: Dict[str, str]) -> List[str]:
        """
        Extract possible values for a widget from device language labels.

        Args:
            short_key (str): Short widget key (e.g., "w_1eklj6euj")
            labels_data (Dict[str, str]): Device language dictionary

        Returns:
            List[str]: List of possible values found in labels with full keys
        """
        possible_values = []

        # Look for LABEL_ and COMBO_ patterns associated with this widget
        for label_key, label_value in labels_data.items():
            # Pattern 1: LABEL_w_[widget_id]_[value]
            if f"LABEL_{short_key}_" in label_key:
                # Show the full key and its value
                possible_values.append(f"{label_key}: {label_value}")

            # Pattern 2: COMBO_w_[widget_id]_[value]
            elif f"COMBO_{short_key}_" in label_key:
                # Show the full key and its value
                possible_values.append(f"{label_key}: {label_value}")

        return possible_values

    def _format_widget_details(self, widget_data: Any) -> Dict[str, Any]:
        """
        Format widget details for display.

        Args:
            widget_data: Raw widget data

        Returns:
            Dict[str, Any]: Formatted widget details
        """
        if not isinstance(widget_data, dict):
            return {"type": "simple", "data": widget_data}

        details = {}

        # Handle different widget types
        if "magnitude" in widget_data:
            unit = widget_data["magnitude"][0] if widget_data["magnitude"] else ""
            details["unit"] = unit

        if "absMin" in widget_data and "absMax" in widget_data:
            details["range"] = f"{widget_data['absMin']} - {widget_data['absMax']}"

        if "minT" in widget_data and "maxT" in widget_data:
            details["target_range"] = f"{widget_data['minT']} - {widget_data['maxT']}"

        if "resolution" in widget_data:
            details["resolution"] = widget_data["resolution"]

        if "visible" in widget_data:
            details["visible"] = widget_data["visible"]

        if "alarm" in widget_data:
            details["alarm"] = widget_data["alarm"]

        if "warning" in widget_data:
            details["warning"] = widget_data["warning"]

        if "set" in widget_data:
            details["set_value"] = widget_data["set"]

        if "comboitems" in widget_data:
            # Format combo items
            combo_items = []
            for item in widget_data["comboitems"]:
                if isinstance(item, list) and len(item) >= 2:
                    combo_items.append(f"{item[0]}: {item[1]}")
            details["combo_items"] = combo_items

        return details

    def _get_widget_value(self, widget_data: Any) -> Any:
        """
        Extract the current value from widget data.

        Args:
            widget_data: Raw widget data

        Returns:
            Any: Current widget value
        """
        if isinstance(widget_data, dict):
            return widget_data.get("current", widget_data)
        return widget_data

    async def analyze_device(self) -> Tuple[Optional[DeviceInfo], List[WidgetInfo],
                                         RequestStatus]:
        """
        Analyze an unknown device by fetching raw data and labels.

        Returns:
            Tuple containing:
            - DeviceInfo: Device information (None if failed)
            - List[WidgetInfo]: List of widget information
            - RequestStatus: Overall operation status
        """
        print("Fetching raw device data...")

        # Get raw instant values
        status, instant_data = await self.handler.get_values_raw()
        if status != RequestStatus.SUCCESS:
            print(f"Failed to fetch instant values: {status}")
            return None, [], status

        print("Raw data fetched successfully")

        # Extract device info
        if instant_data is None:
            print("No instant data received")
            return None, [], RequestStatus.NO_DATA

        device_info = self._extract_device_info(instant_data)
        if not device_info:
            print("Failed to extract device information")
            return None, [], RequestStatus.NO_DATA

        print(f"Device identified: {device_info.device_id}")
        print(f"   Model: {device_info.model}")
        print(f"   FW Code: {device_info.fw_code}")

        # Get device labels
        print("Fetching device labels...")
        label_status, labels_data = await self.handler.get_device_language(
            device_info.device_id)
        if label_status != RequestStatus.SUCCESS:
            print(f"Warning: Could not fetch labels: {label_status}")
            labels_data = {}
        else:
            print(f"Labels fetched successfully ({len(labels_data)} labels)")

        # Process widgets
        print("Processing widgets...")
        widgets = self._process_widgets(instant_data, device_info, labels_data)

        print(f"Processed {len(widgets)} widgets")

        return device_info, widgets, RequestStatus.SUCCESS

    def _process_widgets(self, instant_data: dict, device_info: DeviceInfo,
                        labels_data: Dict[str, str]) -> List[WidgetInfo]:
        """Process widgets from instant data."""
        widgets = []
        device_data = instant_data.get("devicedata", {}).get(device_info.device_id, {})

        for full_key, widget_data in device_data.items():
            if full_key in SKIP_KEYS:
                continue

            short_key = self._extract_short_key(full_key, device_info.model,
                                              device_info.fw_code)

            # Try to find label
            label = self._find_widget_label(full_key, short_key, labels_data)

            # Get current value and details
            raw_value = self._get_widget_value(widget_data)
            details = self._format_widget_details(widget_data)

            # Extract possible values from device language labels
            possible_values = self._extract_possible_values_from_labels(short_key,
                                                                       labels_data)
            if possible_values:
                details["possible_values"] = possible_values

            widgets.append(WidgetInfo(
                key=full_key,
                short_key=short_key,
                label=label,
                raw_value=raw_value,
                details=details
            ))

        return widgets

    def _find_widget_label(self, full_key: str, short_key: str,
                          labels_data: Dict[str, str]) -> str:
        """Find label for a widget."""
        for label_key, label_value in labels_data.items():
            if full_key in label_key or short_key in label_key:
                return label_value
        return DEFAULT_LABEL

    def display_analysis(self, device_info: DeviceInfo, widgets: List[WidgetInfo],
                        show_all: bool = False) -> None:
        """
        Display the analysis results in a formatted table.

        Args:
            device_info (DeviceInfo): Device information
            widgets (List[WidgetInfo]): List of widget information
            show_all (bool): If True, show all widgets including hidden ones
        """
        # Filter widgets based on show_all flag
        if show_all:
            filtered_widgets = widgets
            filter_info = "ALL widgets (including hidden)"
        else:
            filtered_widgets = [w for w in widgets if w.details.get("visible", True)]
            filter_info = "VISIBLE widgets only"

        self._print_header(device_info, widgets, filtered_widgets, filter_info)

        if not filtered_widgets:
            print("\nNo widgets to display.")
            return

        self._print_widgets(filtered_widgets)
        self._print_footer(widgets, filtered_widgets, show_all)

    def _print_header(self, device_info: DeviceInfo, widgets: List[WidgetInfo],  # pylint: disable=unused-argument
                     filtered_widgets: List[WidgetInfo], filter_info: str) -> None:
        """Print analysis header."""
        print("\n" + "=" * SEPARATOR_LENGTH)
        print("DEVICE ANALYSIS RESULTS")
        print("=" * SEPARATOR_LENGTH)

        print(f"Total Widgets: {len(widgets)}")
        print(f"Showing: {len(filtered_widgets)} {filter_info}")

    def _print_widgets(self, filtered_widgets: List[WidgetInfo]) -> None:
        """Print widget details."""
        print(f"\n{'='*SEPARATOR_LENGTH}")
        print("WIDGET DETAILS")
        print(f"{'='*SEPARATOR_LENGTH}")

        for i, widget in enumerate(filtered_widgets, 1):
            self._print_single_widget(widget, i, len(filtered_widgets))

    def _print_single_widget(self, widget: WidgetInfo, index: int,
                           total: int) -> None:
        """Print details for a single widget."""
        print(f"\n[{index:2}] Key: {widget.short_key}")
        print(f"     Label: {widget.label}")
        print(f"     Value: {widget.raw_value}")

        # Show details
        details = self._format_widget_detail_string(widget.details)
        if details:
            print(f"     Details: {' | '.join(details)}")

        # Show combo items separately for clarity
        if widget.details.get("combo_items"):
            print("     Combo Items:")
            for item in widget.details["combo_items"]:
                print(f"       - {item}")

        # Show possible values from device language labels
        if widget.details.get("possible_values"):
            print("     Possible Values:")
            for value in widget.details["possible_values"]:
                print(f"       - {value}")

        # Add separator between widgets
        if index < total:
            print(f"     {'-'*DETAIL_SEPARATOR_LENGTH}")

    def _format_widget_detail_string(self, details: Dict[str, Any]) -> List[str]:
        """Format widget details into a list of strings."""
        detail_strings = []

        if details.get("unit"):
            detail_strings.append(f"Unit: {details['unit']}")

        if details.get("range"):
            detail_strings.append(f"Range: {details['range']}")
        elif details.get("target_range"):
            detail_strings.append(f"Target Range: {details['target_range']}")

        if details.get("resolution", 1) != 1:
            detail_strings.append(f"Resolution: {details['resolution']}")

        if details.get("set_value") is not None:
            detail_strings.append(f"Set Value: {details['set_value']}")

        if not details.get("visible", True):
            detail_strings.append("HIDDEN")

        if details.get("alarm"):
            detail_strings.append("ALARM")

        if details.get("warning"):
            detail_strings.append("WARNING")

        return detail_strings

    def _print_footer(self, widgets: List[WidgetInfo],
                      filtered_widgets: List[WidgetInfo],
                      show_all: bool) -> None:
        """Print analysis footer."""
        print(f"\n{'='*SEPARATOR_LENGTH}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*SEPARATOR_LENGTH}")
        print("\nLegend:")
        print("  - HIDDEN: Widget is not visible in UI")
        print("  - ALARM/WARNING: Widget has alarm/warning status")
        print("  - Set Value: Widget has a configured set value")
        print("  - Resolution: Widget measurement precision")
        print("  - Range: Valid value range")
        print("  - Target Range: Recommended operating range")

        if not show_all:
            hidden_count = len(widgets) - len(filtered_widgets)
            if hidden_count > 0:
                print(f"\nNote: {hidden_count} hidden widgets not shown. "
                      "Use --analyze-all to see all widgets.")
