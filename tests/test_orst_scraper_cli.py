import logging
import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.orst_scraper import main, setup_logging


class TestORSTScraperCLI:
    """Tests for ORSTScraper CLI."""

    @pytest.fixture
    def mock_scraper_cls(self) -> Generator[MagicMock]:
        """Mock ORSTScraper class."""
        with patch("scripts.orst_scraper.ORSTScraper") as mock:
            yield mock

    @pytest.fixture
    def mock_logger(self) -> Generator[MagicMock]:
        """Mock logger."""
        with patch("scripts.orst_scraper.logger") as mock:
            yield mock

    def test_main_default_args(
        self, mock_scraper_cls: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test main with default arguments."""
        with patch.object(sys, "argv", ["orst-scraper"]):
            exit_code = main()

        assert exit_code == 0
        mock_scraper_cls.assert_called_once()
        _, kwargs = mock_scraper_cls.call_args
        config = kwargs["config"]
        assert config.delay_ms == 200
        assert config.include_compound_words is True
        assert config.resume_enabled is True
        assert config.cache_enabled is True

    def test_main_custom_args(
        self, mock_scraper_cls: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test main with custom arguments."""
        args = [
            "orst-scraper",
            "--no-resume",
            "--no-cache",
            "--no-compounds",
            "--delay",
            "500",
            "--output",
            "output.txt",
            "--verbose",
        ]
        with patch.object(sys, "argv", args):
            exit_code = main()

        assert exit_code == 0
        _, kwargs = mock_scraper_cls.call_args
        config = kwargs["config"]
        assert config.delay_ms == 500
        assert config.include_compound_words is False
        assert config.resume_enabled is False
        assert config.cache_enabled is False

    def test_main_output_file(
        self, mock_scraper_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test output to file."""
        output_file = tmp_path / "results.txt"

        # Setup mock scraper to return some words
        instance = mock_scraper_cls.return_value
        instance.__enter__.return_value = instance
        instance.run.return_value = ["word1", "word2"]

        args = ["orst-scraper", "--output", str(output_file)]
        with patch.object(sys, "argv", args):
            exit_code = main()

        assert exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert content == "word1\nword2\n"

    def test_main_keyboard_interrupt(
        self, mock_scraper_cls: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test KeyboardInterrupt handling in main."""
        instance = mock_scraper_cls.return_value
        instance.__enter__.return_value = instance
        instance.run.side_effect = KeyboardInterrupt()

        with patch.object(sys, "argv", ["orst-scraper"]):
            exit_code = main()

        assert exit_code == 130
        mock_logger.info.assert_called_with("Interrupted by user")

    def test_main_general_exception(
        self, mock_scraper_cls: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test general exception handling in main."""
        instance = mock_scraper_cls.return_value
        instance.__enter__.return_value = instance
        instance.run.side_effect = ValueError("Something wrong")

        with patch.object(sys, "argv", ["orst-scraper"]):
            exit_code = main()

        assert exit_code == 1
        mock_logger.error.assert_called()

    def test_setup_logging(self) -> None:
        """Test logging setup."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(verbose=True)
            mock_basic_config.assert_called()
            call_args = mock_basic_config.call_args[1]
            assert call_args["level"] == logging.DEBUG

            setup_logging(verbose=False)
            call_args = mock_basic_config.call_args[1]
            assert call_args["level"] == logging.INFO
