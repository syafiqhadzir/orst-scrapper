"""Unit tests for Thai utilities module."""

from scripts.thai_utils import (
    create_thai_sort_key,
    deduplicate_preserving_order,
    filter_invalid_words,
    is_compound_word,
    is_thai_character,
    is_valid_thai_word,
    normalize_thai_unicode,
    sort_thai_words,
)


class TestThaiCharacterValidation:
    """Tests for Thai character validation."""

    def test_is_thai_character_consonants(self):
        """Test recognition of Thai consonants."""
        assert is_thai_character("ก")
        assert is_thai_character("ข")
        assert is_thai_character("ฮ")

    def test_is_thai_character_vowels(self):
        """Test recognition of Thai vowels."""
        assert is_thai_character("า")
        assert is_thai_character("ิ")
        assert is_thai_character("ุ")

    def test_is_thai_character_tone_marks(self):
        """Test recognition of Thai tone marks."""
        assert is_thai_character("่")
        assert is_thai_character("้")
        assert is_thai_character("๊")

    def test_is_thai_character_non_thai(self):
        """Test rejection of non-Thai characters."""
        assert not is_thai_character("a")
        assert not is_thai_character("1")
        assert not is_thai_character(" ")
        assert not is_thai_character("中")


class TestWordValidation:
    """Tests for word validation."""

    def test_valid_thai_word(self):
        """Test validation of valid Thai words."""
        assert is_valid_thai_word("กก")
        assert is_valid_thai_word("กระดาษ")
        assert is_valid_thai_word("ก่อน")

    def test_valid_thai_word_with_spaces(self):
        """Test validation of compound words with spaces."""
        assert is_valid_thai_word("ก ข ค", allow_spaces=True)
        assert not is_valid_thai_word("ก ข ค", allow_spaces=False)

    def test_invalid_thai_word(self):
        """Test rejection of invalid words."""
        assert not is_valid_thai_word("")
        assert not is_valid_thai_word("hello")
        assert not is_valid_thai_word("กกa")
        assert not is_valid_thai_word("123")


class TestUnicodeNormalization:
    """Tests for Unicode normalization."""

    def test_normalize_sara_am(self):
        """Test normalization of Sara Am (ำ)."""
        # Sara Am can be U+0E33 (composed) or U+0E4D + U+0E32 (decomposed)
        # The key is that normalization is consistent
        composed = "ำ"  # U+0E33
        decomposed = "\u0e4d\u0e32"  # Nikhahit + Sara Aa

        # Apply NFC normalization
        result_composed = normalize_thai_unicode(composed)
        result_decomposed = normalize_thai_unicode(decomposed)

        # Both should be valid Thai text after normalization
        assert is_valid_thai_word(result_composed, allow_spaces=False)
        assert is_valid_thai_word(result_decomposed, allow_spaces=False)

        # Normalization should be idempotent
        assert normalize_thai_unicode(result_composed) == result_composed
        assert normalize_thai_unicode(result_decomposed) == result_decomposed

    def test_normalize_preserves_text(self):
        """Test that normalization preserves text content."""
        text = "กระดาษ"
        assert normalize_thai_unicode(text) == text


class TestCompoundWords:
    """Tests for compound word detection."""

    def test_is_compound_word_with_space(self):
        """Test detection of compound words with spaces."""
        assert is_compound_word("ก ข")
        assert is_compound_word("ก ข ค")

    def test_is_compound_word_with_hyphen(self):
        """Test detection of compound words with hyphens."""
        assert is_compound_word("ก-ข")
        assert is_compound_word("ก–ข")  # Em dash  # noqa: RUF001

    def test_is_not_compound_word(self):
        """Test rejection of simple words."""
        assert not is_compound_word("กก")
        assert not is_compound_word("กระดาษ")


class TestSorting:
    """Tests for Thai Royal Institute sorting."""

    def test_sort_basic_order(self):
        """Test basic alphabet ordering."""
        words = ["ข", "ก", "ค"]
        expected = ["ก", "ข", "ค"]
        assert sort_thai_words(words) == expected

    def test_sort_compound_words(self):
        """Test sorting with compound words."""
        words = ["กก", "ก", "กา"]
        expected = ["ก", "กก", "กา"]
        assert sort_thai_words(words) == expected

    def test_sort_key_function(self):
        """Test sort key function."""
        sort_key = create_thai_sort_key()

        # ก should come before ข
        assert sort_key("ก") < sort_key("ข")

        # ก should come before กก
        assert sort_key("ก") < sort_key("กก")


class TestFiltering:
    """Tests for word filtering."""

    def test_filter_invalid_words(self):
        """Test filtering of invalid words."""
        words = ["ก", "hello", "กระดาษ", "", "ข123"]
        result = filter_invalid_words(words, strict_thai_only=True)
        assert result == ["ก", "กระดาษ"]

    def test_filter_compound_words(self):
        """Test filtering of compound words."""
        words = ["ก", "ก ข", "กระดาษ"]

        # With compounds allowed
        result1 = filter_invalid_words(words, allow_compounds=True)
        assert "ก ข" in result1

        # Without compounds
        result2 = filter_invalid_words(words, allow_compounds=False)
        assert "ก ข" not in result2


class TestDeduplication:
    """Tests for deduplication."""

    def test_deduplicate_preserving_order(self):
        """Test that deduplication preserves first occurrence order."""
        words = ["ก", "ข", "ก", "ค", "ข"]
        expected = ["ก", "ข", "ค"]
        assert deduplicate_preserving_order(words) == expected

    def test_deduplicate_empty_list(self):
        """Test deduplication of empty list."""
        assert deduplicate_preserving_order([]) == []

    def test_deduplicate_no_duplicates(self):
        """Test deduplication when there are no duplicates."""
        words = ["ก", "ข", "ค"]
        assert deduplicate_preserving_order(words) == words
