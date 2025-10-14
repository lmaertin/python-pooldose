"""Tests for CLI functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest


class TestExtractJson:
    """Test the extract_json function."""

    @patch('pooldose.__main__.requests.post')
    def test_extract_json_success(self, mock_post):
        """Test successful JSON extraction."""
        from pooldose.__main__ import extract_json

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            extract_json("192.168.1.100", False, 80, temp_file)

            # Verify file was created with correct data
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert data == {"test": "data"}

            # Verify correct URL was called
            mock_post.assert_called_once_with(
                "http://192.168.1.100:80/api/v1/DWI/getInstantValues",
                timeout=30,
                verify=False
            )
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch('pooldose.__main__.requests.post')
    def test_extract_json_https(self, mock_post):
        """Test JSON extraction with HTTPS."""
        from pooldose.__main__ import extract_json

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"secure": "data"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            extract_json("192.168.1.100", True, 443, temp_file)

            # Verify correct HTTPS URL was called
            mock_post.assert_called_once_with(
                "https://192.168.1.100:443/api/v1/DWI/getInstantValues",
                timeout=30,
                verify=False
            )
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch('pooldose.__main__.requests.post')
    def test_extract_json_http_error(self, mock_post):
        """Test HTTP error handling."""
        from pooldose.__main__ import extract_json
        import requests

        # Mock HTTP error
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            with pytest.raises(SystemExit) as exc_info:
                extract_json("192.168.1.100", False, 80, temp_file)
            assert exc_info.value.code == 1
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch('pooldose.__main__.requests.post')
    def test_extract_json_invalid_json(self, mock_post):
        """Test JSON decode error handling."""
        from pooldose.__main__ import extract_json
        import json as json_module

        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.json.side_effect = json_module.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            with pytest.raises(SystemExit) as exc_info:
                extract_json("192.168.1.100", False, 80, temp_file)
            assert exc_info.value.code == 1
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch('pooldose.__main__.requests.post')
    def test_extract_json_file_write_error(self, mock_post):
        """Test file write error handling."""
        from pooldose.__main__ import extract_json

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Use invalid file path
        with pytest.raises(SystemExit) as exc_info:
            extract_json("192.168.1.100", False, 80, "/invalid/path/file.json")
        assert exc_info.value.code == 1


class TestCLIArguments:
    """Test CLI argument parsing."""

    def test_help_option(self):
        """Test --help option."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "pooldose", "--help"],
            capture_output=True,
            text=True,
            check=False
        )
        assert result.returncode == 0
        assert "Python PoolDose Client" in result.stdout
        assert "--extract-json" in result.stdout
        assert "--out-file" in result.stdout

    def test_version_option(self):
        """Test --version option."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "pooldose", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        assert result.returncode == 0
        assert "python-pooldose" in result.stdout

    def test_extract_json_requires_host(self):
        """Test that --extract-json requires --host."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "pooldose", "--mock", "test.json", "--extract-json"],
            capture_output=True,
            text=True,
            check=False
        )
        assert result.returncode != 0
        # The --mock and --host are mutually exclusive, so this should fail

    def test_analyze_requires_host(self):
        """Test that --analyze requires --host."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "pooldose", "--mock", "test.json", "--analyze"],
            capture_output=True,
            text=True,
            check=False
        )
        assert result.returncode != 0
        # The --mock and --host are mutually exclusive, so this should fail
