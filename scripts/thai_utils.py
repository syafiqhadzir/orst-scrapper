"""Thai language utilities for Unicode handling and sorting.

This module provides utilities for:
- Unicode normalization (NFC) for Thai text
- Thai character validation
- Royal Institute dictionary order sorting
- Compound word handling
"""

import locale
import unicodedata
from collections.abc import Callable, Iterable

from scripts.config import (
    THAI_ALPHABET,
    THAI_CONSONANTS_RANGE,
    THAI_SPECIAL_CHARS_RANGE,
    THAI_TONE_MARKS_RANGE,
    THAI_VOWELS_RANGE,
)


def is_thai_character(char: str) -> bool:
    """Check if a character is a valid Thai script character.

    Args:
        char: Single character to check

    Returns:
        True if the character is in Thai Unicode range
    """
    if len(char) != 1:
        return False

    code_point = ord(char)

    return any(
        [
            THAI_CONSONANTS_RANGE[0] <= code_point <= THAI_CONSONANTS_RANGE[1],
            THAI_VOWELS_RANGE[0] <= code_point <= THAI_VOWELS_RANGE[1],
            THAI_TONE_MARKS_RANGE[0] <= code_point <= THAI_TONE_MARKS_RANGE[1],
            THAI_SPECIAL_CHARS_RANGE[0] <= code_point <= THAI_SPECIAL_CHARS_RANGE[1],
        ]
    )


def is_valid_thai_word(word: str, allow_spaces: bool = True) -> bool:
    """Validate that a word contains only Thai characters (and optionally spaces).

    Args:
        word: Word to validate
        allow_spaces: Whether to allow space characters

    Returns:
        True if all characters are valid Thai or allowed whitespace
    """
    if not word:
        return False

    for char in word:
        if char.isspace():
            if not allow_spaces:
                return False
        elif not is_thai_character(char):
            return False

    return True


def normalize_thai_unicode(text: str) -> str:
    """Normalize Thai text using Unicode NFC (Canonical Composition).

    This ensures consistent representation of composed characters like
    Sara Am (ำ) which can be represented as either:
    - U+0E33 (single character)
    - U+0E4D U+0E32 (Nikhahit + Sara Aa)

    Args:
        text: Thai text to normalize

    Returns:
        Normalized text in NFC form
    """
    return unicodedata.normalize("NFC", text)


def is_compound_word(word: str) -> bool:
    """Check if a word is a compound word (contains spaces or hyphens).

    Args:
        word: Word to check

    Returns:
        True if word contains spaces or hyphens
    """
    return " " in word or "-" in word or "–" in word  # noqa: RUF001


def create_thai_sort_key() -> Callable[[str], tuple[tuple[int, int], ...]]:
    """Create a sort key function for Royal Institute Thai dictionary order.

    This creates a collation key based on the official Thai alphabet order
    defined by the Royal Institute, not standard UTF-8 binary sort.

    Returns:
        A function that can be used as key parameter in sorted()
    """
    from functools import lru_cache

    # Create a mapping of Thai characters to their sort order
    thai_order = {char: idx for idx, char in enumerate(THAI_ALPHABET)}

    @lru_cache(maxsize=100_000)
    def sort_key(word: str) -> tuple[tuple[int, int], ...]:
        """Generate sort key for a Thai word.

        Args:
            word: Thai word to generate key for

        Returns:
            Tuple of integers representing sort order
        """
        result = []
        for char in word:
            if char in thai_order:
                # Primary consonant gets official order
                result.append((thai_order[char], 0))
            elif is_thai_character(char):
                # Vowels, tone marks, etc. sort after consonant
                result.append((1000, ord(char)))
            else:
                # Non-Thai characters (spaces, hyphens) sort last
                result.append((2000, ord(char)))
        return tuple(result)

    return sort_key


def sort_thai_words(words: Iterable[str]) -> list[str]:
    """Sort words according to Royal Institute Thai dictionary order.

    Args:
        words: Iterable of Thai words to sort

    Returns:
        Sorted list of words in Royal Institute order
    """
    sort_key = create_thai_sort_key()
    return sorted(words, key=sort_key)


def setup_thai_locale() -> bool:
    """Attempt to set Thai locale for system-level sorting support.

    Returns:
        True if locale was successfully set, False otherwise
    """
    thai_locales = ["th_TH.UTF-8", "th_TH", "Thai_Thailand.874"]

    for loc in thai_locales:
        try:
            locale.setlocale(locale.LC_COLLATE, loc)
            return True
        except locale.Error:
            continue

    return False


def filter_invalid_words(
    words: Iterable[str], allow_compounds: bool = True, strict_thai_only: bool = True
) -> list[str]:
    """Filter out invalid words from a word list.

    Args:
        words: Iterable of words to filter
        allow_compounds: Whether to allow compound words (with spaces)
        strict_thai_only: Whether to reject words with non-Thai characters

    Returns:
        List of valid words
    """
    valid_words = []

    for word in words:
        # Skip empty words
        if not word or not word.strip():
            continue

        # Check for compound words
        if not allow_compounds and is_compound_word(word):
            continue

        # Validate Thai characters
        if strict_thai_only and not is_valid_thai_word(
            word, allow_spaces=allow_compounds
        ):
            continue

        valid_words.append(word)

    return valid_words


def deduplicate_preserving_order(words: list[str]) -> list[str]:
    """Remove duplicates while preserving original order.

    Args:
        words: List of words (may contain duplicates)

    Returns:
        List with duplicates removed, preserving first occurrence order
    """
    seen = set()
    result = []

    for word in words:
        if word not in seen:
            seen.add(word)
            result.append(word)

    return result
