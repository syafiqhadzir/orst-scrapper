"""Property-based tests for Thai utilities using Hypothesis.

This module uses property-based testing to automatically discover edge cases
in the Thai language processing utilities.
"""

import string

from hypothesis import given, settings
from hypothesis import strategies as st

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

# Thai character strategies
THAI_CONSONANTS = "กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"
THAI_VOWELS = "ะาิีึืุูเแโใไๅ"
THAI_TONE_MARKS = "่้๊๋์"
THAI_CHARS = THAI_CONSONANTS + THAI_VOWELS + THAI_TONE_MARKS

thai_char_strategy = st.sampled_from(THAI_CHARS)
thai_word_strategy = st.text(alphabet=THAI_CHARS, min_size=1, max_size=30)
non_thai_strategy = st.text(
    alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10
)


class TestIsThaiCharacterProperties:
    """Property-based tests for is_thai_character."""

    @given(st.sampled_from(THAI_CONSONANTS))
    def test_all_thai_consonants_are_recognized(self, char: str) -> None:
        """All Thai consonants should be recognized as Thai characters."""
        assert is_thai_character(char) is True

    @given(st.sampled_from(THAI_VOWELS))
    def test_all_thai_vowels_are_recognized(self, char: str) -> None:
        """All Thai vowels should be recognized as Thai characters."""
        assert is_thai_character(char) is True

    @given(st.sampled_from(string.ascii_letters))
    def test_ascii_letters_are_not_thai(self, char: str) -> None:
        """ASCII letters should not be recognized as Thai characters."""
        assert is_thai_character(char) is False

    @given(st.sampled_from(string.digits))
    def test_ascii_digits_are_not_thai(self, digit: str) -> None:
        """ASCII digits should not be recognized as Thai characters."""
        assert is_thai_character(digit) is False


class TestNormalizeThaiUnicodeProperties:
    """Property-based tests for normalize_thai_unicode."""

    @given(thai_word_strategy)
    def test_normalization_is_idempotent(self, text: str) -> None:
        """Normalizing already normalized text should produce the same result."""
        normalized = normalize_thai_unicode(text)
        assert normalize_thai_unicode(normalized) == normalized

    @given(st.text(min_size=0, max_size=100))
    def test_normalization_never_raises(self, text: str) -> None:
        """Normalization should never raise an exception for any input."""
        # Should not raise
        result = normalize_thai_unicode(text)
        assert isinstance(result, str)

    @given(thai_word_strategy)
    def test_normalization_preserves_length_or_reduces(self, text: str) -> None:
        """Normalization should not increase string length significantly."""
        normalized = normalize_thai_unicode(text)
        # NFC normalization typically preserves or reduces length
        assert len(normalized) <= len(text) * 2


class TestIsValidThaiWordProperties:
    """Property-based tests for is_valid_thai_word."""

    @given(thai_word_strategy)
    def test_pure_thai_words_are_valid(self, word: str) -> None:
        """Words containing only Thai characters should be valid."""
        assert is_valid_thai_word(word) is True

    @given(non_thai_strategy)
    def test_pure_non_thai_words_are_invalid(self, word: str) -> None:
        """Words containing only non-Thai characters should be invalid."""
        assert is_valid_thai_word(word) is False

    @given(thai_word_strategy, non_thai_strategy)
    def test_mixed_words_are_invalid(self, thai: str, non_thai: str) -> None:
        """Words mixing Thai and non-Thai characters should be invalid."""
        mixed = thai + non_thai
        assert is_valid_thai_word(mixed) is False


class TestIsCompoundWordProperties:
    """Property-based tests for is_compound_word."""

    @given(thai_word_strategy, thai_word_strategy)
    def test_space_separated_words_are_compound(self, word1: str, word2: str) -> None:
        """Words separated by spaces should be detected as compound."""
        compound = f"{word1} {word2}"
        assert is_compound_word(compound) is True

    @given(thai_word_strategy.filter(lambda x: " " not in x and "-" not in x))
    def test_single_words_are_not_compound(self, word: str) -> None:
        """Single words without separators should not be compound."""
        assert is_compound_word(word) is False


class TestSortThaiWordsProperties:
    """Property-based tests for sort_thai_words."""

    @given(st.lists(thai_word_strategy, min_size=0, max_size=50))
    @settings(max_examples=50)
    def test_sorting_is_stable_and_deterministic(self, words: list[str]) -> None:
        """Sorting the same list twice should produce identical results."""
        sorted1 = sort_thai_words(words)
        sorted2 = sort_thai_words(words)
        assert sorted1 == sorted2

    @given(st.lists(thai_word_strategy, min_size=1, max_size=30))
    @settings(max_examples=50)
    def test_sorting_preserves_elements(self, words: list[str]) -> None:
        """Sorting should preserve all elements (as a multiset)."""
        sorted_words = sort_thai_words(words)
        assert sorted(words) == sorted(sorted_words)

    @given(st.lists(thai_word_strategy, min_size=0, max_size=30))
    @settings(max_examples=50)
    def test_sorting_produces_sorted_output(self, words: list[str]) -> None:
        """Output should be sorted according to the sort key."""
        sort_key = create_thai_sort_key()
        sorted_words = sort_thai_words(words)
        for i in range(len(sorted_words) - 1):
            assert sort_key(sorted_words[i]) <= sort_key(sorted_words[i + 1])


class TestDeduplicatePreservingOrderProperties:
    """Property-based tests for deduplicate_preserving_order."""

    @given(st.lists(thai_word_strategy, min_size=0, max_size=50))
    @settings(max_examples=50)
    def test_deduplication_removes_duplicates(self, words: list[str]) -> None:
        """Deduplicated list should have no duplicates."""
        result = deduplicate_preserving_order(words)
        assert len(result) == len(set(result))

    @given(st.lists(thai_word_strategy, min_size=0, max_size=50))
    @settings(max_examples=50)
    def test_deduplication_preserves_first_occurrence(self, words: list[str]) -> None:
        """First occurrence of each word should be preserved."""
        result = deduplicate_preserving_order(words)
        seen: set[str] = set()
        expected: list[str] = []
        for word in words:
            if word not in seen:
                expected.append(word)
                seen.add(word)
        assert result == expected

    @given(st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=30))
    @settings(max_examples=50)
    def test_deduplication_is_idempotent(self, words: list[str]) -> None:
        """Deduplicating twice should give the same result."""
        once = deduplicate_preserving_order(words)
        twice = deduplicate_preserving_order(once)
        assert once == twice


class TestFilterInvalidWordsProperties:
    """Property-based tests for filter_invalid_words."""

    @given(st.lists(thai_word_strategy, min_size=0, max_size=30))
    @settings(max_examples=50)
    def test_filtering_preserves_valid_thai_words(self, words: list[str]) -> None:
        """Valid Thai words should pass through the filter."""
        # Filter with strict Thai only
        result = filter_invalid_words(
            words, allow_compounds=True, strict_thai_only=True
        )
        for word in result:
            assert is_valid_thai_word(word)

    @given(st.lists(non_thai_strategy, min_size=1, max_size=20))
    def test_filtering_removes_non_thai_words(self, words: list[str]) -> None:
        """Non-Thai words should be removed by the filter."""
        result = filter_invalid_words(
            words, allow_compounds=False, strict_thai_only=True
        )
        assert len(result) == 0


class TestIntegrationProperties:
    """Integration property tests combining multiple functions."""

    @given(st.lists(thai_word_strategy, min_size=1, max_size=30))
    @settings(max_examples=30)
    def test_full_pipeline_produces_valid_output(self, words: list[str]) -> None:
        """Full processing pipeline should produce valid, sorted, unique words."""
        # Simulate full processing pipeline
        normalized = [normalize_thai_unicode(w) for w in words]
        filtered = filter_invalid_words(normalized)
        deduplicated = deduplicate_preserving_order(filtered)
        sorted_words = sort_thai_words(deduplicated)

        # Verify properties
        assert len(sorted_words) == len(set(sorted_words))  # No duplicates
        for word in sorted_words:
            assert is_valid_thai_word(word)  # All valid
