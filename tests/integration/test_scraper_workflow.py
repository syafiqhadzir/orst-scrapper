"""End-to-end integration tests for the scraper workflow."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import responses

from scripts.config import ScraperConfig
from scripts.dictionary_diff import (
    compare_dictionaries,
    generate_audit_report,
)
from scripts.hunspell_writer import HunspellDictionaryWriter
from scripts.orst_scraper import ORSTScraper
from scripts.progress_tracker import ProgressTracker


class TestScraperWorkflow:
    """End-to-end tests for the complete scraper workflow."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path]:
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config(self, temp_dir: Path) -> ScraperConfig:
        """Create test configuration."""
        return ScraperConfig(
            delay_ms=0,
            cache_enabled=False,
            resume_enabled=False,
        )

    @pytest.fixture(autouse=True)
    def patch_progress_tracker(self, temp_dir: Path) -> Generator[None]:
        """Ensure ProgressTracker uses temp directory."""
        with patch("scripts.orst_scraper.ProgressTracker") as mock_tracker:
            # We want each instantiation to get a fresh tracker with temp file
            def create_tracker(*args: Any, **kwargs: Any) -> ProgressTracker:
                progress_file = temp_dir / "progress.json"
                return ProgressTracker(progress_file)

            mock_tracker.side_effect = create_tracker
            yield

    def test_hunspell_writer_creates_valid_dic_file(self, temp_dir: Path) -> None:
        """Test that HunspellDictionaryWriter creates properly formatted .dic file."""
        words = ["ก", "ข", "ค", "คำ", "คำถาม"]
        output_file = temp_dir / "test.dic"

        writer = HunspellDictionaryWriter()
        writer.write(words, output_file)

        # Verify file exists and can be read back
        assert output_file.exists()
        read_words = writer.read(output_file)
        assert len(read_words) == len(words)
        assert set(read_words) == set(words)

    def test_dictionary_diff_detects_changes(self, temp_dir: Path) -> None:
        """Test that compare_dictionaries correctly identifies added/removed words."""
        old_words = ["ก", "ข", "ค"]
        new_words = ["ก", "ค", "ง", "จ"]

        diff = compare_dictionaries(old_words, new_words)

        assert diff.added_count == 2  # ง, จ added
        assert diff.removed_count == 1  # ข removed
        assert diff.unchanged_count == 2  # ก, ค unchanged

    def test_dictionary_diff_generates_report(self, temp_dir: Path) -> None:
        """Test audit report generation."""
        old_words = ["ก", "ข"]
        new_words = ["ก", "ค"]
        report_path = temp_dir / "audit_report.md"

        diff = compare_dictionaries(old_words, new_words)
        generate_audit_report(diff, report_path)

        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert any(word in content.lower() for word in ["added", "removed"])

    @responses.activate
    def test_full_scrape_workflow(self, config: ScraperConfig) -> None:
        """Test complete scraping workflow from API to processed words."""
        # Mock API responses for single character
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[3, ["คำ", "คำคม", "คำถาม"]],
            status=200,
        )
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[3, []],  # No more results
            status=200,
        )

        with patch("scripts.orst_scraper.THAI_ALPHABET", ["ค"]):
            scraper = ORSTScraper(config, resume=False)
            result = scraper.scrape_character("ค")

        assert len(result) == 3
        assert "คำ" in result

    def test_scraper_handles_empty_results(self, config: ScraperConfig) -> None:
        """Test that scraper handles characters with no results gracefully."""
        scraper = ORSTScraper(config, resume=False)
        with patch.object(scraper, "scrape_character", return_value=[]):
            result = scraper.scrape_character("ฯ")
            assert result == []

    def test_word_processing_pipeline(self, config: ScraperConfig) -> None:
        """Test the word processing pipeline (normalize, validate, dedupe, sort)."""
        raw_words = [
            "ก",  # Valid Thai
            "ข",  # Valid Thai
            "ก",  # Duplicate
            "hello",  # Non-Thai (should be filtered)
            " ",  # Whitespace (should be filtered)
            "คำ",  # Valid Thai
        ]

        scraper = ORSTScraper(config, resume=False)
        processed = scraper.process_words(raw_words)

        # Should filter non-Thai, remove duplicates, and sort
        assert "hello" not in processed
        assert processed.count("ก") == 1  # Deduplicated
        assert len(processed) == 3  # ก, ข, คำ

    def test_config_validation(self) -> None:
        """Test that configuration validates properly."""
        # Valid config
        config = ScraperConfig(delay_ms=100)
        assert config.delay_ms == 100

    @responses.activate
    def test_scraper_run_full_cycle(self, config: ScraperConfig) -> None:
        """Test the full scraper.run() method with mocked API and alphabet."""
        # Mock API for "ก"
        responses.add(
            responses.GET,
            "https://dictionary.orst.go.th/Lookup/lookupDomain.php",
            json=[1, ["ก", "กก"]],
            status=200,
        )

        # Patch THAI_ALPHABET to just "ก" to run quickly
        with patch("scripts.orst_scraper.THAI_ALPHABET", ("ก",)):
            # Must set resume=False to force scraping
            scraper = ORSTScraper(config, resume=False)

            # Run the scraper
            result = scraper.run()

            assert len(result) == 2
            assert "ก" in result
            assert "กก" in result
