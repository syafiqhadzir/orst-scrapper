from collections.abc import Generator
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from scripts.config import ScraperConfig
from scripts.orst_scraper import ORSTScraper


class TestORSTScraper:
    """Tests for ORSTScraper class."""

    @pytest.fixture
    def scraper(self, mock_config: ScraperConfig) -> Generator[ORSTScraper]:
        """Fixture providing ORSTScraper with mocked client."""
        with patch("scripts.orst_scraper.ORSTAPIClient") as mock_client_cls:
            scraper = ORSTScraper(mock_config, resume=False)
            scraper.client = mock_client_cls.return_value
            yield scraper

    def test_scrape_character_success(self, scraper: ORSTScraper) -> None:
        """Test scraping a single character."""
        # Use MagicMock explicitly if needed or rely on return_value
        cast_client = MagicMock()
        cast_client.fetch_all_pages.return_value = ["คำ", "คำคม"]
        scraper.client = cast_client

        words = scraper.scrape_character("ค")

        assert len(words) == 2
        assert "คำ" in words
        scraper.client.fetch_all_pages.assert_called_once_with("ค")

    def test_process_words(self, scraper: ORSTScraper) -> None:
        """Test word processing (deduplication, sorting, filtering)."""
        raw_words = ["ก", "ข", "ก", "a", " "]  # specific mix
        processed = scraper.process_words(raw_words)

        assert "a" not in processed  # English removed
        assert processed.count("ก") == 1  # Deduplicated
        assert processed == ["ก", "ข"]  # Sorted Thai order

    def test_context_manager(self, mock_config: ScraperConfig) -> None:
        """Test usage as context manager."""
        with patch("scripts.orst_scraper.ORSTAPIClient") as mock_client_cls:
            with ORSTScraper(mock_config, resume=False) as scraper:
                assert scraper.client is not None
                mock_client = mock_client_cls.return_value

            # Verify client closed on exit
            mock_client.close.assert_called_once()

    def test_resume_from_progress(self) -> None:
        """Test initializing with resume=True loads progress."""
        from scripts.config import ScraperConfig

        config = ScraperConfig(resume_enabled=True)

        with patch("scripts.orst_scraper.ProgressTracker") as mock_tracker_cls:
            mock_tracker = mock_tracker_cls.return_value
            mock_tracker.load.return_value = True
            mock_tracker.state.get_all_words.return_value = ["old"]
            mock_tracker.state.current_char_index = 5

            scraper = ORSTScraper(config, resume=True)

            assert scraper.all_words == ["old"]
            mock_tracker.load.assert_called_once()

    def test_scrape_character_skips_completed(self, scraper: ORSTScraper) -> None:
        """Test that already completed characters are skipped."""
        scraper.progress.state.completed_chars = {"ก"}
        scraper.progress.state.partial_results = {"ก": ["ก"]}

        # This should return immediately without calling API
        scraper.scrape_character("ก")

        cast(MagicMock, scraper.client.fetch_all_pages).assert_not_called()

    def test_scrape_all_handles_error(self, scraper: ORSTScraper) -> None:
        """Test error handling during scrape loop."""
        with (
            patch("scripts.orst_scraper.THAI_ALPHABET", ("ก",)),
            patch.object(
                scraper, "scrape_character", side_effect=ValueError("Scrape error")
            ),
            pytest.raises(ValueError, match="Scrape error"),
        ):
            scraper.scrape_all()

    def test_run_keyboard_interrupt(self, scraper: ORSTScraper) -> None:
        """Test KeyboardInterrupt in run method."""
        with (
            patch.object(scraper, "scrape_all", side_effect=KeyboardInterrupt()),
            pytest.raises(KeyboardInterrupt),
        ):
            scraper.run()

        cast(MagicMock, scraper.client.close).assert_called()

    def test_run_general_exception(self, scraper: ORSTScraper) -> None:
        """Test general exception in run method."""
        with (
            patch.object(scraper, "scrape_all", side_effect=RuntimeError("Fatal")),
            pytest.raises(RuntimeError, match="Fatal"),
        ):
            scraper.run()

        cast(MagicMock, scraper.client.close).assert_called()
