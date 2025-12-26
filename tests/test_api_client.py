from unittest.mock import Mock, patch

import pytest
import requests

from scripts.api_client import APIResponse, ORSTAPIClient


class TestORSTAPIClient:
    @pytest.fixture
    def client(self, mock_config):
        with patch("scripts.api_client.requests.Session") as mock_session_cls:
            client = ORSTAPIClient(mock_config)
            client.session = mock_session_cls.return_value
            yield client

    def test_fetch_page_success(self, client):
        """Test successful page fetch."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = [100, ["ก", "กา", "กาก"]]
        client.session.get.return_value = mock_response

        result = client.fetch_page("ก", 1)

        assert isinstance(result, APIResponse)
        assert result.total_count == 100
        assert len(result.words) == 3
        assert result.page == 1
        assert result.domain == "ก"

    def test_fetch_page_error(self, client):
        """Test error handling during fetch."""
        client.session.get.side_effect = requests.RequestException("Network Error")

        with pytest.raises(requests.RequestException):
            client.fetch_page("ก", 1)

    def test_fetch_page_invalid_response(self, client):
        """Test handling of invalid API response format."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid format"}  # Not a list
        client.session.get.return_value = mock_response

        with pytest.raises(ValueError, match="Unexpected API response format"):
            client.fetch_page("ก", 1)

    def test_rate_limiting(self, client):
        """Test that rate limiting wait is called."""
        # Config is frozen, so we create a new config with desired delay
        # We need to bypass the frozen nature by replacing the whole object
        import dataclasses

        client.config = dataclasses.replace(client.config, delay_ms=100)

        with patch("time.sleep") as mock_sleep:
            # Simulate a previous request happened at time 100.0
            client.last_request_time = 100.0

            # Setup mock response
            mock_response = Mock()
            mock_response.json.return_value = [10, ["word"]]
            client.session.get.return_value = mock_response

            # We mock time.time to return 100.05 (50ms later)
            # elapsed = 100.05 - 100.0 = 0.05
            # delay = 0.1 (100ms)
            # elapsed < delay -> should sleep

            with patch("time.time", side_effect=[100.05]):
                client._wait_for_rate_limit()
                mock_sleep.assert_called()
