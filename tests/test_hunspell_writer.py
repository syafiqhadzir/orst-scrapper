"""Unit tests for Hunspell dictionary writer module."""

import tempfile
from pathlib import Path

import pytest

from scripts.config import HunspellConfig
from scripts.hunspell_writer import HunspellDictionaryWriter


class TestHunspellDictionaryWriter:
    """Tests for HunspellDictionaryWriter class."""

    @pytest.fixture
    def writer(self):
        """Create a writer with default config."""
        return HunspellDictionaryWriter()

    @pytest.fixture
    def custom_writer(self):
        """Create a writer with custom config."""
        config = HunspellConfig(
            encoding="utf-8",
            use_count_header=False,
            one_word_per_line=True,
        )
        return HunspellDictionaryWriter(config)

    def test_write_creates_file(self, writer):
        """Test that write creates a dictionary file."""
        words = ["ก", "ข", "ค"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            writer.write(words, output_path)

            assert output_path.exists()

    def test_write_includes_count_header(self, writer):
        """Test that write includes word count header."""
        words = ["ก", "ข", "ค"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            writer.write(words, output_path)

            content = output_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            assert lines[0].strip() == "# 3"

    def test_write_without_count_header(self, custom_writer):
        """Test writing without count header."""
        words = ["ก", "ข"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            custom_writer.write(words, output_path)

            content = output_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            # First line should be the first word, not a count
            assert lines[0] == "ก"

    def test_write_with_header_comment(self, writer):
        """Test writing with optional header comment."""
        words = ["ก"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            writer.write(words, output_path, header_comment="Test comment")

            content = output_path.read_text(encoding="utf-8")
            assert "# Test comment" in content

    def test_write_empty_list_raises_error(self, writer):
        """Test that writing empty list raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            with pytest.raises(ValueError, match="empty word list"):
                writer.write([], output_path)

    def test_write_word_with_newline_raises_error(self, writer):
        """Test that word containing newline raises error."""
        words = ["ก\nข"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            with pytest.raises(ValueError, match="contains newline"):
                writer.write(words, output_path)

    def test_read_dictionary(self, writer):
        """Test reading words from dictionary file."""
        words = ["ก", "ข", "ค"]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.dic"
            writer.write(words, file_path)

            read_words = writer.read(file_path)
            assert read_words == words

    def test_read_nonexistent_file_raises_error(self, writer):
        """Test reading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            writer.read(Path("/nonexistent/path/file.dic"))

    def test_read_skips_comments(self, writer):
        """Test that read skips comment lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.dic"
            content = "# 2\n# This is a comment\nก\nข\n"
            file_path.write_text(content, encoding="utf-8")

            words = writer.read(file_path)
            assert words == ["ก", "ข"]

    def test_read_handles_affix_flags(self, writer):
        """Test that read strips affix flags from words."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.dic"
            content = "# 2\nก/ABC\nข/XYZ\n"
            file_path.write_text(content, encoding="utf-8")

            words = writer.read(file_path)
            assert words == ["ก", "ข"]


class TestValidateFormat:
    """Tests for validate_format static method."""

    def test_validate_valid_file(self):
        """Test validation of valid dictionary file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "valid.dic"
            content = "# 3\nก\nข\nค\n"
            file_path.write_text(content, encoding="utf-8")

            is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
            assert is_valid is True
            assert len(errors) == 0

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file."""
        is_valid, errors = HunspellDictionaryWriter.validate_format(
            Path("/nonexistent/file.dic")
        )
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_empty_file(self):
        """Test validation of empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "empty.dic"
            file_path.write_text("", encoding="utf-8")

            is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
            assert is_valid is False
            assert "empty" in errors[0].lower()

    def test_validate_count_mismatch(self):
        """Test validation detects count mismatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "mismatch.dic"
            content = "# 10\nก\nข\n"  # Says 10 but only has 2 words
            file_path.write_text(content, encoding="utf-8")

            is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
            assert is_valid is False
            assert any("mismatch" in e.lower() for e in errors)

    def test_validate_numeric_header(self):
        """Test validation accepts plain numeric header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "numeric.dic"
            content = "2\nก\nข\n"
            file_path.write_text(content, encoding="utf-8")

            is_valid, _ = HunspellDictionaryWriter.validate_format(file_path)
            assert is_valid is True
