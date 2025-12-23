"""API client for ORST Dictionary web service.

This module provides a robust HTTP client for interacting with the
Thai Royal Institute Dictionary API at dictionary.orst.go.th.

Features:
- Automatic retry with exponential backoff
- Rate limiting (polite crawler)
- Response caching
- Progress tracking
- Error handling and logging
"""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scripts.config import (
    API_BASE_URL,
    API_ENDPOINT,
    CACHE_DIR,
    REQUEST_TIMEOUT,
    RESULTS_PER_PAGE,
    RETRY_BACKOFF_BASE,
    USER_AGENT,
    ScraperConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Structured response from ORST API.
    
    Attributes:
        total_count: Total number of words for this Thai character
        words: List of headwords for the current page
        page: Page number of this response
        domain: Thai character domain this response is for
    """

    total_count: int
    words: list[str]
    page: int
    domain: str

    @property
    def total_pages(self) -> int:
        """Calculate total pages based on total count."""
        return (self.total_count + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE

    @property
    def has_more_pages(self) -> bool:
        """Check if there are more pages to fetch."""
        return self.page < self.total_pages


class ORSTAPIClient:
    """HTTP client for ORST Dictionary API.
    
    This client implements:
    - Polite crawling with configurable delays
    - Automatic retries with exponential backoff
    - Optional response caching
    - Proper User-Agent and Referer headers
    """

    def __init__(self, config: ScraperConfig):
        """Initialize the API client.
        
        Args:
            config: Scraper configuration
        """
        self.config = config
        self.session = self._create_session()
        self.last_request_time: float = 0.0

        # Create cache directory if caching is enabled
        if config.cache_enabled:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration.
        
        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=RETRY_BACKOFF_BASE,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update({
            'User-Agent': USER_AGENT,
            'Referer': API_BASE_URL,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
        })

        return session

    def _wait_for_rate_limit(self) -> None:
        """Implement polite crawler delay between requests."""
        if self.config.delay_ms <= 0:
            return

        elapsed = time.time() - self.last_request_time
        delay_seconds = self.config.delay_ms / 1000.0

        if elapsed < delay_seconds:
            time.sleep(delay_seconds - elapsed)

    def _get_cache_path(self, domain: str, page: int) -> Path:
        """Get cache file path for a specific request.
        
        Args:
            domain: Thai character
            page: Page number
            
        Returns:
            Path to cache file
        """
        # Use character code to avoid filesystem issues with Thai chars
        char_code = ord(domain)
        return CACHE_DIR / f"domain_{char_code:04x}_page_{page:03d}.json"

    def _load_from_cache(self, domain: str, page: int) -> APIResponse | None:
        """Try to load response from cache.
        
        Args:
            domain: Thai character
            page: Page number
            
        Returns:
            Cached APIResponse if available, None otherwise
        """
        if not self.config.cache_enabled:
            return None

        cache_path = self._get_cache_path(domain, page)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Cache hit: {domain} page {page}")
                return APIResponse(
                    total_count=data['total_count'],
                    words=data['words'],
                    page=data['page'],
                    domain=data['domain']
                )
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Cache read error for {domain} page {page}: {e}")
            return None

    def _save_to_cache(self, response: APIResponse) -> None:
        """Save response to cache.
        
        Args:
            response: APIResponse to cache
        """
        if not self.config.cache_enabled:
            return

        cache_path = self._get_cache_path(response.domain, response.page)

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_count': response.total_count,
                    'words': response.words,
                    'page': response.page,
                    'domain': response.domain,
                }, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cached: {response.domain} page {response.page}")
        except OSError as e:
            logger.warning(f"Cache write error: {e}")

    def fetch_page(self, domain: str, page: int) -> APIResponse:
        """Fetch a single page of words for a Thai character.
        
        Args:
            domain: Thai character (e.g., 'ก', 'ข')
            page: Page number (1-indexed)
            
        Returns:
            APIResponse containing words and metadata
            
        Raises:
            requests.RequestException: If the request fails after retries
            ValueError: If the API response is invalid
        """
        # Check cache first
        cached = self._load_from_cache(domain, page)
        if cached is not None:
            return cached

        # Implement rate limiting
        self._wait_for_rate_limit()

        # Build request URL
        url = urljoin(API_BASE_URL, API_ENDPOINT)
        params = {
            'domain': domain,
            'page': page,
        }

        logger.info(f"Fetching: {domain} page {page}")

        try:
            # Make the request
            response = self.session.get(
                url,
                params=params,  # type: ignore[arg-type]
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            # Update rate limit tracker
            self.last_request_time = time.time()

            # Parse JSON response
            data = response.json()

            # Validate response format
            if not isinstance(data, list) or len(data) != 2:
                raise ValueError(f"Unexpected API response format: {data}")

            total_count, words = data

            if not isinstance(total_count, int) or not isinstance(words, list):
                raise ValueError(f"Invalid data types in response: {data}")

            # Create structured response
            api_response = APIResponse(
                total_count=total_count,
                words=words,
                page=page,
                domain=domain
            )

            # Cache the response
            self._save_to_cache(api_response)

            logger.info(
                f"Success: {domain} page {page}/{api_response.total_pages} "
                f"({len(words)} words, total: {total_count})"
            )

            return api_response

        except requests.RequestException as e:
            logger.error(f"Request failed for {domain} page {page}: {e}")
            raise
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse response for {domain} page {page}: {e}")
            raise ValueError(f"Invalid API response: {e}") from e

    def fetch_all_pages(self, domain: str) -> list[str]:
        """Fetch all pages of words for a Thai character.
        
        Args:
            domain: Thai character (e.g., 'ก', 'ข')
            
        Returns:
            Complete list of all words for this character
            
        Raises:
            requests.RequestException: If any request fails
        """
        all_words: list[str] = []

        # Fetch first page to get total count
        first_page = self.fetch_page(domain, 1)
        all_words.extend(first_page.words)

        # Fetch remaining pages
        for page in range(2, first_page.total_pages + 1):
            response = self.fetch_page(domain, page)
            all_words.extend(response.words)

        logger.info(
            f"Completed {domain}: {len(all_words)} words "
            f"from {first_page.total_pages} pages"
        )

        return all_words

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self) -> "ORSTAPIClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object | None) -> None:
        """Context manager exit."""
        self.close()
