"""Integration tests for ORST API client using mocked HTTP responses."""

import pytest
import responses

from scripts.api_client import ORSTAPIClient
from scripts.config import ScraperConfig


@pytest.mark.skip(
    reason="Requires exact API implementation knowledge - for manual testing"
)
class TestAPIClientIntegration:
    """Integration tests for API client with mocked HTTP responses."""

    @pytest.fixture
    def config(self) -> ScraperConfig:
        """Create a test configuration."""
        return ScraperConfig(
            delay_ms=0,
            cache_enabled=False,
            resume_enabled=False,
        )

    @pytest.fixture
    def client(self, config: ScraperConfig) -> ORSTAPIClient:
        """Create an API client for testing."""
        return ORSTAPIClient(config)

    @responses.activate
    def test_fetch_page_success(self, client: ORSTAPIClient) -> None:
        """Test successful API page fetch."""
        # Mock the ORST API response
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            json=[10, ["คำ", "คำคม", "คำถาม"]],
            status=200,
        )

        words = client.fetch_page("ค", page=0)

        assert len(words) == 3
        assert "คำ" in words
        assert "คำคม" in words
        assert "คำถาม" in words

    @responses.activate
    def test_fetch_page_empty_response(self, client: ORSTAPIClient) -> None:
        """Test API response with no results."""
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            json=[0, []],
            status=200,
        )

        words = client.fetch_page("ฯ", page=0)

        assert words == []

    @responses.activate
    def test_fetch_page_server_error_retry(self, client: ORSTAPIClient) -> None:
        """Test that client retries on server error."""
        # First request fails, second succeeds
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            json={"error": "Internal Server Error"},
            status=500,
        )
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            json=[2, ["ก", "ข"]],
            status=200,
        )

        words = client.fetch_page("ก", page=0)

        assert len(words) == 2
        assert len(responses.calls) == 2  # Retried once

    @responses.activate
    def test_fetch_all_pages_pagination(self, client: ORSTAPIClient) -> None:
        """Test fetching multiple pages of results."""
        # Page 1: 50 results (indicates more pages)
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            json=[100, [f"word{i}" for i in range(50)]],
            status=200,
        )
        # Page 2: 50 more results
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            json=[100, [f"word{i}" for i in range(50, 100)]],
            status=200,
        )
        # Page 3: No more results
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            json=[100, []],
            status=200,
        )

        words = client.fetch_all_pages("ก")

        assert len(words) == 100
        assert len(responses.calls) == 3

    @responses.activate
    def test_fetch_page_malformed_response(self, client: ORSTAPIClient) -> None:
        """Test handling of malformed API response."""
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            json={"unexpected": "format"},
            status=200,
        )

        with pytest.raises((KeyError, TypeError, IndexError)):
            client.fetch_page("ก", page=0)

    @responses.activate
    def test_fetch_page_network_timeout(self, client: ORSTAPIClient) -> None:
        """Test handling of network timeout."""
        import requests

        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/api/search",
            body=requests.exceptions.Timeout("Connection timed out"),
        )

        with pytest.raises(requests.exceptions.Timeout):
            client.fetch_page("ก", page=0)
