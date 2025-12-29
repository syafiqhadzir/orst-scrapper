import dataclasses
from collections.abc import Generator
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from scripts.api_client import APIResponse, ORSTAPIClient
from scripts.config import ScraperConfig


class TestORSTAPIClient:
    """Tests for ORSTAPIClient class."""

    @pytest.fixture
    def client(self, mock_config: ScraperConfig) -> Generator[ORSTAPIClient]:
        """Create a client with mocked session."""
        with patch("scripts.api_client.requests.Session") as mock_session_cls:
            client = ORSTAPIClient(mock_config)
            client.session = mock_session_cls.return_value
            yield client

    def test_fetch_page_success(self, client: ORSTAPIClient) -> None:
        """Test successful page fetch."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = [100, ["ก", "กา", "กาก"]]
        cast(MagicMock, client.session.get).return_value = mock_response

        result = client.fetch_page("ก", 1)

        assert isinstance(result, APIResponse)
        assert result.total_count == 100
        assert len(result.words) == 3
        assert result.page == 1
        assert result.domain == "ก"

    def test_fetch_page_error(self, client: ORSTAPIClient) -> None:
        """Test error handling during fetch."""
        cast(MagicMock, client.session.get).side_effect = requests.RequestException(
            "Network Error"
        )

        with pytest.raises(requests.RequestException):
            client.fetch_page("ก", 1)

    def test_fetch_page_invalid_response(self, client: ORSTAPIClient) -> None:
        """Test handling of invalid API response format."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid format"}  # Not a list
        cast(MagicMock, client.session.get).return_value = mock_response

        with pytest.raises(ValueError, match="Unexpected API response format"):
            client.fetch_page("ก", 1)

    def test_rate_limiting(self, client: ORSTAPIClient) -> None:
        """Test that rate limiting wait is called."""
        client.config = dataclasses.replace(client.config, delay_ms=100)

        with (
            patch("time.sleep") as mock_sleep,
            patch("time.time", side_effect=[100.05]),
        ):
            # Simulate a previous request happened at time 100.0
            client.last_request_time = 100.0

            # Setup mock response
            mock_response = Mock()
            mock_response.json.return_value = [10, ["word"]]
            cast(MagicMock, client.session.get).return_value = mock_response

            client._wait_for_rate_limit()
            mock_sleep.assert_called()

    def test_api_response_properties(self) -> None:
        """Test APIResponse properties."""
        resp = APIResponse(total_count=25, words=["a"] * 10, page=1, domain="ก")
        assert resp.total_pages == 3  # 25 / 10 = 2.5 -> 3
        assert resp.has_more_pages is True

        resp2 = APIResponse(total_count=10, words=["a"] * 10, page=1, domain="ก")
        assert resp2.total_pages == 1
        assert resp2.has_more_pages is False

    def test_context_manager(self, mock_config: ScraperConfig) -> None:
        """Test ORSTAPIClient context manager."""
        with patch("scripts.api_client.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            with ORSTAPIClient(mock_config) as client:
                assert client.session is not None

            mock_session.close.assert_called_once()

    def test_caching_logic(self, client: ORSTAPIClient, tmp_path: Path) -> None:
        """Test cache save and load."""
        with patch("scripts.api_client.CACHE_DIR", tmp_path):
            resp = APIResponse(total_count=1, words=["test"], page=1, domain="ก")
            client.config = dataclasses.replace(client.config, cache_enabled=True)

            # Save to cache
            client._save_to_cache(resp)

            # Check file exists
            char_code = ord("ก")
            cache_file = tmp_path / f"domain_{char_code:04x}_page_001.json"
            assert cache_file.exists()

            # Load from cache
            cached = client._load_from_cache("ก", 1)
            assert cached is not None
            assert cached.words == ["test"]

            # Fetch page should hit cache
            result = client.fetch_page("ก", 1)
            assert result.words == ["test"]

    def test_cache_errors(self, client: ORSTAPIClient, tmp_path: Path) -> None:
        """Test cache handling of IO/JSON errors."""
        with patch("scripts.api_client.CACHE_DIR", tmp_path):
            client.config = dataclasses.replace(client.config, cache_enabled=True)

            # 1. Load from non-existent cache
            assert client._load_from_cache("ข", 1) is None

            # 2. Corrupt cache file
            char_code = ord("ข")
            cache_file = tmp_path / f"domain_{char_code:04x}_page_001.json"
            cache_file.write_text("invalid json")
            assert client._load_from_cache("ข", 1) is None

            # 3. Save error (mock open to fail)
            with patch("pathlib.Path.open", side_effect=OSError("Disk full")):
                resp = APIResponse(total_count=1, words=["x"], page=1, domain="ก")
                client._save_to_cache(resp)  # Should not raise

    def test_fetch_page_invalid_data_types(self, client: ORSTAPIClient) -> None:
        """Test validation of data types in API response."""
        mock_response = Mock()
        # total_count should be int, words should be list
        mock_response.json.return_value = ["10", "not a list"]
        cast(MagicMock, client.session.get).return_value = mock_response

        with pytest.raises(ValueError, match="Invalid data types in response"):
            client.fetch_page("ก", 1)
