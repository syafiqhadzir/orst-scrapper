"""Tests for export module."""

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.export import (
    ExportMetadata,
    export_to_csv,
    export_to_hunspell_dic,
    export_to_json,
    export_to_sqlite,
)


@pytest.fixture
def sample_words() -> list[str]:
    """Sample Thai words for testing."""
    return ["กรุงเทพ", "กระดาษ", "กล้วย", "ขนม", "คน"]


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Temporary directory for test outputs."""
    return tmp_path


class TestExportMetadata:
    """Tests for ExportMetadata dataclass."""

    def test_create_metadata(self) -> None:
        """Test creating metadata with word count."""
        metadata = ExportMetadata.create(100)

        assert metadata.total_words == 100
        assert metadata.source == "ORST Dictionary (dictionary.orst.go.th)"
        assert metadata.version == "1.2.0"
        assert metadata.export_date  # Should be non-empty

    def test_metadata_has_iso_date(self) -> None:
        """Test that export date is in ISO format."""
        metadata = ExportMetadata.create(50)

        # Should be parseable as ISO format
        assert "T" in metadata.export_date
        assert "Z" in metadata.export_date or "+" in metadata.export_date


class TestExportToJson:
    """Tests for JSON export."""

    def test_export_basic(self, sample_words: list[str], temp_dir: Path) -> None:
        """Test basic JSON export."""
        output_path = temp_dir / "output.json"
        export_to_json(sample_words, output_path)

        assert output_path.exists()
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert "words" in data
        assert "metadata" in data
        assert len(data["words"]) == len(sample_words)

    def test_export_without_metadata(
        self, sample_words: list[str], temp_dir: Path
    ) -> None:
        """Test JSON export without metadata."""
        output_path = temp_dir / "output.json"
        export_to_json(sample_words, output_path, include_metadata=False)

        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert "words" in data
        assert "metadata" not in data

    def test_export_preserves_thai_characters(
        self, sample_words: list[str], temp_dir: Path
    ) -> None:
        """Test that Thai characters are preserved correctly."""
        output_path = temp_dir / "output.json"
        export_to_json(sample_words, output_path)

        data = json.loads(output_path.read_text(encoding="utf-8"))
        # Should contain Thai text
        assert any("ก" in word for word in data["words"])

    def test_export_sorted(self, temp_dir: Path) -> None:
        """Test that words are sorted in Thai order."""
        words = ["ขนม", "กรุงเทพ", "คน"]  # Not in Thai order
        output_path = temp_dir / "output.json"
        export_to_json(words, output_path, sort_words=True)

        data = json.loads(output_path.read_text(encoding="utf-8"))
        # First word should start with ก (first in Thai alphabet)
        assert data["words"][0].startswith("ก")


class TestExportToCsv:
    """Tests for CSV export."""

    def test_export_basic(self, sample_words: list[str], temp_dir: Path) -> None:
        """Test basic CSV export."""
        output_path = temp_dir / "output.csv"
        export_to_csv(sample_words, output_path)

        assert output_path.exists()
        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        # Header + data rows
        assert len(lines) == len(sample_words) + 1

    def test_export_with_index(self, sample_words: list[str], temp_dir: Path) -> None:
        """Test CSV export with index column."""
        output_path = temp_dir / "output.csv"
        export_to_csv(sample_words, output_path, include_index=True)

        content = output_path.read_text(encoding="utf-8")
        assert "index,word" in content
        assert "1," in content

    def test_export_without_index(
        self, sample_words: list[str], temp_dir: Path
    ) -> None:
        """Test CSV export without index column."""
        output_path = temp_dir / "output.csv"
        export_to_csv(sample_words, output_path, include_index=False)

        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        assert lines[0] == "word"


class TestExportToSqlite:
    """Tests for SQLite export."""

    def test_export_basic(self, sample_words: list[str], temp_dir: Path) -> None:
        """Test basic SQLite export."""
        output_path = temp_dir / "dictionary.db"
        export_to_sqlite(sample_words, output_path)

        assert output_path.exists()

        # Verify database structure
        conn = sqlite3.connect(str(output_path))
        try:
            cursor = conn.cursor()

            # Check words table
            cursor.execute("SELECT COUNT(*) FROM words")
            count = cursor.fetchone()[0]
            assert count == len(sample_words)

            # Check metadata table
            cursor.execute("SELECT value FROM metadata WHERE key = 'total_words'")
            total = cursor.fetchone()[0]
            assert int(total) == len(sample_words)

        finally:
            conn.close()

    def test_export_with_custom_table_name(
        self, sample_words: list[str], temp_dir: Path
    ) -> None:
        """Test SQLite export with custom table name."""
        output_path = temp_dir / "dictionary.db"
        export_to_sqlite(sample_words, output_path, table_name="thai_words")

        conn = sqlite3.connect(str(output_path))
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM thai_words")
            count = cursor.fetchone()[0]
            assert count == len(sample_words)
        finally:
            conn.close()

    def test_export_includes_length(
        self, sample_words: list[str], temp_dir: Path
    ) -> None:
        """Test that SQLite export includes word length."""
        output_path = temp_dir / "dictionary.db"
        export_to_sqlite(sample_words, output_path)

        conn = sqlite3.connect(str(output_path))
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT word, length FROM words")
            for word, length in cursor.fetchall():
                assert length == len(word)
        finally:
            conn.close()


class TestExportToHunspellDic:
    """Tests for Hunspell .dic export."""

    def test_export_basic(self, sample_words: list[str], temp_dir: Path) -> None:
        """Test basic Hunspell export."""
        output_path = temp_dir / "test.dic"
        export_to_hunspell_dic(sample_words, output_path)

        assert output_path.exists()
        lines = output_path.read_text(encoding="utf-8").strip().split("\n")

        # First line should be word count
        assert int(lines[0]) == len(sample_words)
        # Should have word count + words lines
        assert len(lines) == len(sample_words) + 1

    def test_export_removes_duplicates(self, temp_dir: Path) -> None:
        """Test that Hunspell export removes duplicates."""
        words = ["กรุงเทพ", "กรุงเทพ", "กล้วย"]  # Duplicate
        output_path = temp_dir / "test.dic"
        export_to_hunspell_dic(words, output_path)

        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        # Should only have 2 unique words
        assert int(lines[0]) == 2

    def test_export_sorted(self, temp_dir: Path) -> None:
        """Test that Hunspell export sorts words."""
        words = ["ขนม", "กรุงเทพ"]  # Not sorted
        output_path = temp_dir / "test.dic"
        export_to_hunspell_dic(words, output_path, sort_words=True)

        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        # Second line (first word) should start with ก
        assert lines[1].startswith("ก")
