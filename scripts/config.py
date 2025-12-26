"""Configuration and constants for ORST Dictionary Scraper.

This module defines all configuration parameters, Thai alphabet ordering,
and constants used throughout the scraper system.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Final

# API Configuration
API_BASE_URL: Final[str] = "https://dictionary.orst.go.th"
API_ENDPOINT: Final[str] = "Lookup/lookupDomain.php"
RESULTS_PER_PAGE: Final[int] = 10

# Crawler Configuration
DEFAULT_DELAY_MS: Final[int] = 200
MAX_RETRIES: Final[int] = 3
RETRY_BACKOFF_BASE: Final[float] = 2.0
REQUEST_TIMEOUT: Final[int] = 30
USER_AGENT: Final[str] = (
    "ORST-Dictionary-Scraper/1.0 "
    "(https://github.com/SyafiqHadzir/Hunspell-TH; "
    "inquiry@syafiqhadzir.dev)"
)

# Thai Alphabet in Royal Institute Dictionary Order
# This is the official ordering used by the Thai Royal Institute
THAI_ALPHABET: Final[tuple[str, ...]] = (
    "ก",
    "ข",
    "ฃ",
    "ค",
    "ฅ",
    "ฆ",
    "ง",
    "จ",
    "ฉ",
    "ช",
    "ซ",
    "ฌ",
    "ญ",
    "ฎ",
    "ฏ",
    "ฐ",
    "ฑ",
    "ฒ",
    "ณ",
    "ด",
    "ต",
    "ถ",
    "ท",
    "ธ",
    "น",
    "บ",
    "ป",
    "ผ",
    "ฝ",
    "พ",
    "ฟ",
    "ภ",
    "ม",
    "ย",
    "ร",
    "ฤ",
    "ล",
    "ฦ",
    "ว",
    "ศ",
    "ษ",
    "ส",
    "ห",
    "ฬ",
    "อ",
    "ฮ",
)

# Unicode Character Ranges for Thai Script
THAI_CONSONANTS_RANGE: Final[tuple[int, int]] = (0x0E01, 0x0E2E)
THAI_VOWELS_RANGE: Final[tuple[int, int]] = (0x0E30, 0x0E3A)
THAI_TONE_MARKS_RANGE: Final[tuple[int, int]] = (0x0E48, 0x0E4B)
THAI_SPECIAL_CHARS_RANGE: Final[tuple[int, int]] = (0x0E4C, 0x0E4F)

# File Paths
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "reports"
CACHE_DIR: Final[Path] = DATA_DIR / "cache"
PROGRESS_FILE: Final[Path] = DATA_DIR / "scraper_progress.json"


@dataclass(frozen=True)
class ScraperConfig:
    """Configuration for the ORST dictionary scraper.

    Attributes:
        delay_ms: Delay in milliseconds between API requests
        max_retries: Maximum number of retry attempts for failed requests
        include_compound_words: Whether to include multi-word entries
        normalize_unicode: Whether to apply Unicode NFC normalization
        validate_thai_only: Whether to reject non-Thai characters
        resume_enabled: Whether to resume from saved progress
        cache_enabled: Whether to cache API responses
    """

    delay_ms: int = DEFAULT_DELAY_MS
    max_retries: int = MAX_RETRIES
    include_compound_words: bool = True
    normalize_unicode: bool = True
    validate_thai_only: bool = True
    resume_enabled: bool = True
    cache_enabled: bool = True

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.delay_ms < 0:
            raise ValueError("delay_ms must be non-negative")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")


@dataclass(frozen=True)
class HunspellConfig:
    """Configuration for Hunspell dictionary format.

    Attributes:
        encoding: Character encoding for the dictionary file
        use_count_header: Whether to include word count on first line
        one_word_per_line: Enforce one word per line (Hunspell requirement)
        affix_notation: Whether to include affix rules (future feature)
    """

    encoding: str = "utf-8"
    use_count_header: bool = True
    one_word_per_line: bool = True
    affix_notation: bool = False


# Default configurations
DEFAULT_SCRAPER_CONFIG = ScraperConfig()
DEFAULT_HUNSPELL_CONFIG = HunspellConfig()
