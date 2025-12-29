"""Unit tests for Hunspell dictionary writer module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.config import HunspellConfig
from scripts.hunspell_writer import HunspellDictionaryWriter


class TestHunspellDictionaryWriter:
    """Tests for HunspellDictionaryWriter class."""

    @pytest.fixture
    def writer(self) -> HunspellDictionaryWriter:
        """Create a writer with default config."""
        return HunspellDictionaryWriter()

    @pytest.fixture
    def custom_writer(self) -> HunspellDictionaryWriter:
        """Create a writer with custom config."""
        config = HunspellConfig(
            encoding="utf-8",
            use_count_header=False,
            one_word_per_line=True,
        )
        return HunspellDictionaryWriter(config)

    def test_write_creates_file(self, writer: HunspellDictionaryWriter) -> None:
        """Test that write creates a dictionary file."""
        words = ["ก", "ข", "ค"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            writer.write(words, output_path)
            assert output_path.exists()

    def test_write_includes_count_header(
        self, writer: HunspellDictionaryWriter
    ) -> None:
        """Test that write includes word count header."""
        words = ["ก", "ข", "ค"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            writer.write(words, output_path)

            content = output_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            assert lines[0].strip() == "# 3"

    def test_write_without_count_header(
        self, custom_writer: HunspellDictionaryWriter
    ) -> None:
        """Test writing without count header."""
        words = ["ก", "ข"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            custom_writer.write(words, output_path)

            content = output_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            # First line should be the first word, not a count
            assert lines[0] == "ก"

    def test_write_with_header_comment(self, writer: HunspellDictionaryWriter) -> None:
        """Test writing with optional header comment."""
        words = ["ก"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            writer.write(words, output_path, header_comment="Test comment")

            content = output_path.read_text(encoding="utf-8")
            assert "# Test comment" in content

    def test_write_empty_list_raises_error(
        self, writer: HunspellDictionaryWriter
    ) -> None:
        """Test that writing empty list raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            with pytest.raises(ValueError, match="empty word list"):
                writer.write([], output_path)

    def test_write_word_with_newline_raises_error(
        self, writer: HunspellDictionaryWriter
    ) -> None:
        """Test that word containing newline raises error."""
        words = ["ก\nข"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.dic"
            with pytest.raises(ValueError, match="contains newline"):
                writer.write(words, output_path)

    def test_read_dictionary(self, writer: HunspellDictionaryWriter) -> None:
        """Test reading words from dictionary file."""
        words = ["ก", "ข", "ค"]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.dic"
            writer.write(words, file_path)

            read_words = writer.read(file_path)
            assert read_words == words

    def test_read_nonexistent_file_raises_error(
        self, writer: HunspellDictionaryWriter
    ) -> None:
        """Test reading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            writer.read(Path("/nonexistent/path/file.dic"))

    def test_read_skips_comments(self, writer: HunspellDictionaryWriter) -> None:
        """Test that read skips comment lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.dic"
            content = "# 2\n# This is a comment\nก\nข\n"
            file_path.write_text(content, encoding="utf-8")

            words = writer.read(file_path)
            assert words == ["ก", "ข"]

    def test_read_handles_affix_flags(self, writer: HunspellDictionaryWriter) -> None:
        """Test that read strips affix flags from words."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.dic"
            content = "# 2\nก/ABC\nข/XYZ\n"
            file_path.write_text(content, encoding="utf-8")

            words = writer.read(file_path)
            assert words == ["ก", "ข"]

    def test_write_os_error(
        self, writer: HunspellDictionaryWriter, tmp_path: Path
    ) -> None:
        """Test OSError during write."""
        output_path = tmp_path / "protected.dic"
        with (
            patch("pathlib.Path.open", side_effect=OSError("Read-only file system")),
            pytest.raises(OSError, match="Read-only file system"),
        ):
            writer.write(["word"], output_path)

    def test_read_os_error(
        self, writer: HunspellDictionaryWriter, tmp_path: Path
    ) -> None:
        """Test OSError during read."""
        file_path = tmp_path / "test.dic"
        file_path.write_text("# 1\nword")
        with (
            patch("pathlib.Path.open", side_effect=OSError("Disk failure")),
            pytest.raises(OSError, match="Disk failure"),
        ):
            writer.read(file_path)

    def test_read_skips_empty_lines(
        self, writer: HunspellDictionaryWriter, tmp_path: Path
    ) -> None:
        """Test that read skips empty lines (line 108 coverage)."""
        file_path = tmp_path / "test.dic"
        file_path.write_text("# 1\n\nword\n\n")
        words = writer.read(file_path)
        assert words == ["word"]


class TestValidateFormat:
    """Tests for validate_format static method."""

    def test_validate_valid_file(self, tmp_path: Path) -> None:
        """Test validation of valid dictionary file."""
        file_path = tmp_path / "valid.dic"
        content = "# 3\nก\nข\nค\n"
        file_path.write_text(content, encoding="utf-8")

        is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_nonexistent_file(self) -> None:
        """Test validation of nonexistent file."""
        is_valid, errors = HunspellDictionaryWriter.validate_format(
            Path("/nonexistent/file.dic")
        )
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_empty_file(self, tmp_path: Path) -> None:
        """Test validation of empty file."""
        file_path = tmp_path / "empty.dic"
        file_path.write_text("", encoding="utf-8")

        is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
        assert is_valid is False
        assert any("empty" in e.lower() for e in errors)

    def test_validate_count_mismatch(self, tmp_path: Path) -> None:
        """Test validation detects count mismatch."""
        file_path = tmp_path / "mismatch.dic"
        content = "# 10\nก\nข\n"  # Says 10 but only has 2 words
        file_path.write_text(content, encoding="utf-8")

        is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
        assert is_valid is False
        assert any("mismatch" in e.lower() for e in errors)

    def test_validate_non_numeric_header(self, tmp_path: Path) -> None:
        """Test validation with non-numeric count header."""
        file_path = tmp_path / "bad_header.dic"
        file_path.write_text("# many\nword")
        is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
        assert is_valid is False
        assert any("Invalid count header" in e for e in errors)

    def test_validate_missing_header_char(self, tmp_path: Path) -> None:
        """Test validation with missing header tag/digits."""
        file_path = tmp_path / "no_header.dic"
        file_path.write_text("not-a-number\nword")
        is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
        assert is_valid is False
        assert any("First line should be word count" in e for e in errors)

    def test_validate_unicode_error(self, tmp_path: Path) -> None:
        """Test validation with UnicodeEncodeError."""
        file_path = tmp_path / "test.dic"
        file_path.write_text("# 1\nword")

        # Mock lines to contain an object that raises UnicodeEncodeError on encode
        mock_line = MagicMock()
        mock_line.encode.side_effect = UnicodeEncodeError("utf-8", "", 0, 1, "bad")
        mock_line.strip.return_value = "word"

        with patch("scripts.hunspell_writer.Path.open") as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            # First line is a valid header, second line raises on encode
            mock_file.readlines.return_value = ["# 1\n", mock_line]

            is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
            assert is_valid is False
            assert any("Non-UTF-8 character" in e for e in errors)

    def test_validate_general_exception(self, tmp_path: Path) -> None:
        """Test validate_format handles general exception (line 117-118)."""
        file_path = tmp_path / "test.dic"
        file_path.write_text("# 1\nword")

        with patch(
            "scripts.hunspell_writer.Path.open",
            side_effect=RuntimeError("Validation crash"),
        ):
            is_valid, errors = HunspellDictionaryWriter.validate_format(file_path)
            assert is_valid is False
            assert any("Validation error: Validation crash" in e for e in errors)
