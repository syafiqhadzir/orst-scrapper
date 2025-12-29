import pytest
import requests
import responses

from scripts.api_client import ORSTAPIClient
from scripts.config import ScraperConfig


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
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[10, ["คำ", "คำคม", "คำถาม"]],
            status=200,
        )

        response = client.fetch_page("ค", page=1)
        words = response.words

        assert len(words) == 3
        assert "คำ" in words
        assert "คำคม" in words
        assert "คำถาม" in words

    @responses.activate
    def test_fetch_page_empty_response(self, client: ORSTAPIClient) -> None:
        """Test API response with no results."""
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[0, []],
            status=200,
        )

        response = client.fetch_page("ฯ", page=1)

        assert response.words == []

    @responses.activate
    def test_fetch_page_server_error_retry(self, client: ORSTAPIClient) -> None:
        """Test that client retries on server error."""
        # First request fails, second succeeds
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json={"error": "Internal Server Error"},
            status=500,
        )
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[2, ["ก", "ข"]],
            status=200,
        )

        response = client.fetch_page("ก", page=1)

        assert len(response.words) == 2
        assert len(responses.calls) == 2  # Retried once

    @responses.activate
    def test_fetch_all_pages_pagination(self, client: ORSTAPIClient) -> None:
        """Test fetching multiple pages of results."""
        # Page 1: 50 results (indicates more pages)
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[30, [f"word{i}" for i in range(50)]],
            status=200,
        )
        # Page 2: 50 more results
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[30, [f"word{i}" for i in range(50, 100)]],
            status=200,
        )
        # Page 3: No more results
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[30, []],
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
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json={"unexpected": "format"},
            status=200,
        )

        with pytest.raises(ValueError):
            client.fetch_page("ก", page=1)

    @responses.activate
    def test_fetch_page_network_timeout(self, client: ORSTAPIClient) -> None:
        """Test handling of network timeout."""
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            body=requests.exceptions.Timeout("Connection timed out"),
        )

        with pytest.raises(requests.exceptions.Timeout):
            client.fetch_page("ก", page=1)
