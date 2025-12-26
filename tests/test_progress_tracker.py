"""Unit tests for progress tracker module."""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.progress_tracker import ProgressState, ProgressTracker


class TestProgressState:
    """Tests for ProgressState dataclass."""

    def test_initial_state(self):
        """Test default initial state values."""
        state = ProgressState()

        assert state.current_char_index == 0
        assert state.completed_chars == set()
        assert state.total_words_scraped == 0
        assert state.last_update_time == ""
        assert state.partial_results == {}

    def test_mark_completed(self):
        """Test marking a character as completed."""
        state = ProgressState()
        words = ["ก", "กา", "กาก"]

        state.mark_completed("ก", words)

        assert "ก" in state.completed_chars
        assert state.partial_results["ก"] == words
        assert state.total_words_scraped == 3
        assert state.last_update_time != ""

    def test_mark_completed_multiple(self):
        """Test marking multiple characters as completed."""
        state = ProgressState()

        state.mark_completed("ก", ["ก", "กา"])
        state.mark_completed("ข", ["ข", "ขา", "ขาว"])

        assert len(state.completed_chars) == 2
        assert state.total_words_scraped == 5

    def test_is_completed_true(self):
        """Test is_completed returns True for completed char."""
        state = ProgressState()
        state.mark_completed("ก", ["ก"])

        assert state.is_completed("ก") is True

    def test_is_completed_false(self):
        """Test is_completed returns False for incomplete char."""
        state = ProgressState()

        assert state.is_completed("ก") is False

    def test_get_all_words(self):
        """Test get_all_words returns all scraped words."""
        state = ProgressState()
        state.mark_completed("ก", ["ก", "กา"])
        state.mark_completed("ข", ["ข", "ขา"])

        all_words = state.get_all_words()

        assert len(all_words) == 4
        assert "ก" in all_words
        assert "ขา" in all_words

    def test_get_all_words_empty(self):
        """Test get_all_words returns empty list when no results."""
        state = ProgressState()

        assert state.get_all_words() == []


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    @pytest.fixture
    def temp_progress_file(self):
        """Create a temporary progress file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "progress.json"

    def test_init_creates_fresh_state(self, temp_progress_file):
        """Test initialization creates fresh state."""
        tracker = ProgressTracker(temp_progress_file)

        assert tracker.state.current_char_index == 0
        assert tracker.state.total_words_scraped == 0

    def test_save_creates_file(self, temp_progress_file):
        """Test save creates progress file."""
        tracker = ProgressTracker(temp_progress_file)
        tracker.state.mark_completed("ก", ["ก", "กา"])

        tracker.save()

        assert temp_progress_file.exists()

    def test_save_content_is_valid_json(self, temp_progress_file):
        """Test saved file contains valid JSON."""
        tracker = ProgressTracker(temp_progress_file)
        tracker.state.mark_completed("ก", ["ก"])
        tracker.save()

        with temp_progress_file.open(encoding="utf-8") as f:
            data = json.load(f)

        assert "completed_chars" in data
        assert "total_words_scraped" in data

    def test_load_restores_state(self, temp_progress_file):
        """Test load restores saved state."""
        # Save state
        tracker1 = ProgressTracker(temp_progress_file)
        tracker1.state.mark_completed("ก", ["ก", "กา"])
        tracker1.state.current_char_index = 5
        tracker1.save()

        # Load in new tracker
        tracker2 = ProgressTracker(temp_progress_file)
        success = tracker2.load()

        assert success is True
        assert tracker2.state.current_char_index == 5
        assert "ก" in tracker2.state.completed_chars
        assert tracker2.state.total_words_scraped == 2

    def test_load_returns_false_when_no_file(self, temp_progress_file):
        """Test load returns False when no progress file exists."""
        tracker = ProgressTracker(temp_progress_file)

        success = tracker.load()

        assert success is False

    def test_load_handles_invalid_json(self, temp_progress_file):
        """Test load handles corrupt JSON file gracefully."""
        temp_progress_file.parent.mkdir(parents=True, exist_ok=True)
        temp_progress_file.write_text("not valid json {{{")

        tracker = ProgressTracker(temp_progress_file)
        success = tracker.load()

        assert success is False

    def test_clear_resets_state(self, temp_progress_file):
        """Test clear resets state and deletes file."""
        tracker = ProgressTracker(temp_progress_file)
        tracker.state.mark_completed("ก", ["ก"])
        tracker.save()

        tracker.clear()

        assert tracker.state.current_char_index == 0
        assert len(tracker.state.completed_chars) == 0
        assert not temp_progress_file.exists()

    def test_update_char_index(self, temp_progress_file):
        """Test update_char_index updates and saves."""
        tracker = ProgressTracker(temp_progress_file)

        tracker.update_char_index(10)

        assert tracker.state.current_char_index == 10
        assert temp_progress_file.exists()

    def test_mark_char_completed(self, temp_progress_file):
        """Test mark_char_completed updates state and saves."""
        tracker = ProgressTracker(temp_progress_file)

        tracker.mark_char_completed("ก", ["ก", "กา", "กาก"])

        assert "ก" in tracker.state.completed_chars
        assert tracker.state.total_words_scraped == 3
        assert temp_progress_file.exists()

    def test_persistence_across_instances(self, temp_progress_file):
        """Test state persists across tracker instances."""
        # First instance
        tracker1 = ProgressTracker(temp_progress_file)
        tracker1.mark_char_completed("ก", ["ก"])
        tracker1.mark_char_completed("ข", ["ข", "ขา"])

        # Second instance
        tracker2 = ProgressTracker(temp_progress_file)
        tracker2.load()

        assert tracker2.state.total_words_scraped == 3
        assert len(tracker2.state.completed_chars) == 2
