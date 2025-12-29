from typing import Any
from unittest.mock import MagicMock

import pytest

from scripts.config import ScraperConfig


@pytest.fixture
def mock_config() -> ScraperConfig:
    """Create a mock scraper configuration."""
    return ScraperConfig(
        delay_ms=0,
        include_compound_words=True,
        cache_enabled=False,
        resume_enabled=False,
        normalize_unicode=True,
        validate_thai_only=True,
    )


@pytest.fixture
def mock_response_data() -> list[Any]:
    """Sample API response data."""
    return [
        10,  # Total count
        ["word1", "word2", "word3"],  # Words
    ]


@pytest.fixture
def mock_session() -> MagicMock:
    """Mock requests session."""
    session = MagicMock()
    return session
