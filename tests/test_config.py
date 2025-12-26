"""Unit tests for configuration module."""

import pytest

from scripts.config import (
    API_BASE_URL,
    DEFAULT_DELAY_MS,
    DEFAULT_HUNSPELL_CONFIG,
    DEFAULT_SCRAPER_CONFIG,
    MAX_RETRIES,
    THAI_ALPHABET,
    HunspellConfig,
    ScraperConfig,
)


class TestScraperConfig:
    """Tests for ScraperConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ScraperConfig()

        assert config.delay_ms == DEFAULT_DELAY_MS
        assert config.max_retries == MAX_RETRIES
        assert config.include_compound_words is True
        assert config.normalize_unicode is True
        assert config.validate_thai_only is True
        assert config.resume_enabled is True
        assert config.cache_enabled is True

    def test_custom_values(self):
        """Test creating config with custom values."""
        config = ScraperConfig(
            delay_ms=500,
            max_retries=5,
            include_compound_words=False,
            cache_enabled=False,
        )

        assert config.delay_ms == 500
        assert config.max_retries == 5
        assert config.include_compound_words is False
        assert config.cache_enabled is False

    def test_negative_delay_raises_error(self):
        """Test that negative delay raises ValueError."""
        with pytest.raises(ValueError, match="delay_ms must be non-negative"):
            ScraperConfig(delay_ms=-1)

    def test_negative_max_retries_raises_error(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            ScraperConfig(max_retries=-1)

    def test_zero_delay_is_valid(self):
        """Test that zero delay is valid."""
        config = ScraperConfig(delay_ms=0)
        assert config.delay_ms == 0

    def test_zero_retries_is_valid(self):
        """Test that zero retries is valid."""
        config = ScraperConfig(max_retries=0)
        assert config.max_retries == 0

    def test_config_is_frozen(self):
        """Test that config is immutable (frozen)."""
        config = ScraperConfig()
        with pytest.raises(AttributeError):
            config.delay_ms = 1000  # type: ignore


class TestHunspellConfig:
    """Tests for HunspellConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = HunspellConfig()

        assert config.encoding == "utf-8"
        assert config.use_count_header is True
        assert config.one_word_per_line is True
        assert config.affix_notation is False

    def test_custom_values(self):
        """Test creating config with custom values."""
        config = HunspellConfig(
            encoding="iso-8859-11",
            use_count_header=False,
            affix_notation=True,
        )

        assert config.encoding == "iso-8859-11"
        assert config.use_count_header is False
        assert config.affix_notation is True

    def test_config_is_frozen(self):
        """Test that config is immutable (frozen)."""
        config = HunspellConfig()
        with pytest.raises(AttributeError):
            config.encoding = "ascii"  # type: ignore


class TestDefaultConfigs:
    """Tests for default configuration instances."""

    def test_default_scraper_config_exists(self):
        """Test DEFAULT_SCRAPER_CONFIG is available."""
        assert DEFAULT_SCRAPER_CONFIG is not None
        assert isinstance(DEFAULT_SCRAPER_CONFIG, ScraperConfig)

    def test_default_hunspell_config_exists(self):
        """Test DEFAULT_HUNSPELL_CONFIG is available."""
        assert DEFAULT_HUNSPELL_CONFIG is not None
        assert isinstance(DEFAULT_HUNSPELL_CONFIG, HunspellConfig)


class TestConstants:
    """Tests for configuration constants."""

    def test_api_base_url(self):
        """Test API base URL is set correctly."""
        assert API_BASE_URL == "https://dictionary.orst.go.th"

    def test_thai_alphabet_length(self):
        """Test Thai alphabet contains all consonants."""
        # Thai alphabet: 44 consonants + 2 vowel-consonants (ฤ, ฦ)
        assert len(THAI_ALPHABET) == 46

    def test_thai_alphabet_starts_with_kor_kai(self):
        """Test Thai alphabet starts with ก."""
        assert THAI_ALPHABET[0] == "ก"

    def test_thai_alphabet_ends_with_hor_nokhuk(self):
        """Test Thai alphabet ends with ฮ."""
        assert THAI_ALPHABET[-1] == "ฮ"

    def test_thai_alphabet_contains_obsolete_letters(self):
        """Test Thai alphabet includes obsolete letters."""
        assert "ฃ" in THAI_ALPHABET  # Kho Khuat (obsolete)
        assert "ฅ" in THAI_ALPHABET  # Kho Khon (obsolete)
