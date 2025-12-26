"""Unit tests for dictionary diff module."""

import tempfile
from pathlib import Path

from scripts.dictionary_diff import (
    DictionaryDiff,
    compare_dictionaries,
    generate_audit_report,
    save_word_list,
)


class TestDictionaryDiff:
    """Tests for DictionaryDiff dataclass."""

    def test_added_count(self):
        """Test added_count property."""
        diff = DictionaryDiff(
            added_words={"ก", "ข", "ค"},
            removed_words={"ง"},
            unchanged_words={"จ", "ฉ"},
            old_count=3,
            new_count=5,
        )
        assert diff.added_count == 3

    def test_removed_count(self):
        """Test removed_count property."""
        diff = DictionaryDiff(
            added_words={"ก"},
            removed_words={"ข", "ค"},
            unchanged_words={"ง"},
            old_count=3,
            new_count=2,
        )
        assert diff.removed_count == 2

    def test_unchanged_count(self):
        """Test unchanged_count property."""
        diff = DictionaryDiff(
            added_words=set(),
            removed_words=set(),
            unchanged_words={"ก", "ข", "ค", "ง"},
            old_count=4,
            new_count=4,
        )
        assert diff.unchanged_count == 4

    def test_has_changes_true(self):
        """Test has_changes returns True when there are changes."""
        diff = DictionaryDiff(
            added_words={"ก"},
            removed_words=set(),
            unchanged_words={"ข"},
            old_count=1,
            new_count=2,
        )
        assert diff.has_changes is True

    def test_has_changes_false(self):
        """Test has_changes returns False when no changes."""
        diff = DictionaryDiff(
            added_words=set(),
            removed_words=set(),
            unchanged_words={"ก", "ข"},
            old_count=2,
            new_count=2,
        )
        assert diff.has_changes is False


class TestCompareDictionaries:
    """Tests for compare_dictionaries function."""

    def test_compare_identical(self):
        """Test comparing identical word lists."""
        words = ["ก", "ข", "ค"]
        diff = compare_dictionaries(words, words)

        assert diff.added_count == 0
        assert diff.removed_count == 0
        assert diff.unchanged_count == 3
        assert diff.has_changes is False

    def test_compare_with_additions(self):
        """Test comparing with new words added."""
        old_words = ["ก", "ข"]
        new_words = ["ก", "ข", "ค", "ง"]

        diff = compare_dictionaries(old_words, new_words)

        assert diff.added_count == 2
        assert diff.removed_count == 0
        assert "ค" in diff.added_words
        assert "ง" in diff.added_words

    def test_compare_with_removals(self):
        """Test comparing with words removed (ghost words)."""
        old_words = ["ก", "ข", "ค", "ง"]
        new_words = ["ก", "ข"]

        diff = compare_dictionaries(old_words, new_words)

        assert diff.added_count == 0
        assert diff.removed_count == 2
        assert "ค" in diff.removed_words
        assert "ง" in diff.removed_words

    def test_compare_with_both_changes(self):
        """Test comparing with both additions and removals."""
        old_words = ["ก", "ข", "ค"]
        new_words = ["ก", "ง", "จ"]

        diff = compare_dictionaries(old_words, new_words)

        assert "ง" in diff.added_words
        assert "จ" in diff.added_words
        assert "ข" in diff.removed_words
        assert "ค" in diff.removed_words
        assert "ก" in diff.unchanged_words

    def test_compare_empty_lists(self):
        """Test comparing empty lists."""
        diff = compare_dictionaries([], [])

        assert diff.added_count == 0
        assert diff.removed_count == 0
        assert diff.unchanged_count == 0


class TestGenerateAuditReport:
    """Tests for generate_audit_report function."""

    def test_generate_report_creates_file(self):
        """Test that audit report file is created."""
        diff = DictionaryDiff(
            added_words={"ก", "ข"},
            removed_words={"ค"},
            unchanged_words={"ง", "จ"},
            old_count=3,
            new_count=4,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit_report.md"
            generate_audit_report(diff, output_path)

            assert output_path.exists()
            content = output_path.read_text(encoding="utf-8")
            assert "Audit Report" in content

    def test_generate_report_contains_statistics(self):
        """Test that report contains statistics."""
        diff = DictionaryDiff(
            added_words={"ก"},
            removed_words={"ข"},
            unchanged_words={"ค"},
            old_count=2,
            new_count=2,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"
            generate_audit_report(diff, output_path)

            content = output_path.read_text(encoding="utf-8")
            assert "Added" in content or "added" in content
            assert "Removed" in content or "removed" in content

    def test_generate_report_no_changes(self):
        """Test report generation when no changes."""
        diff = DictionaryDiff(
            added_words=set(),
            removed_words=set(),
            unchanged_words={"ก", "ข"},
            old_count=2,
            new_count=2,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"
            generate_audit_report(diff, output_path)

            assert output_path.exists()


class TestSaveWordList:
    """Tests for save_word_list function."""

    def test_save_word_list_creates_file(self):
        """Test that word list file is created."""
        words = {"ก", "ข", "ค"}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "words.txt"
            save_word_list(words, output_path, "Test Words")

            assert output_path.exists()

    def test_save_word_list_content(self):
        """Test that saved file contains all words."""
        words = {"ก", "ข", "ค"}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "words.txt"
            save_word_list(words, output_path)

            content = output_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            assert len(lines) == 3
            for word in words:
                assert word in lines

    def test_save_empty_word_list(self):
        """Test saving empty word set does not create file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.txt"
            save_word_list(set(), output_path)

            # Empty set returns early without creating file
            assert not output_path.exists()
