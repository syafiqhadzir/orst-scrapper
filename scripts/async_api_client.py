"""Async API client for ORST Dictionary web service.

This module provides an asynchronous HTTP client for high-performance
scraping of the Thai Royal Institute Dictionary API.

Features:
- Concurrent requests using httpx and asyncio
- Automatic retry with exponential backoff
- Rate limiting with semaphore control
- Optional response caching
- Full type safety

Usage:
    async with AsyncORSTAPIClient(config) as client:
        words = await client.fetch_all_pages_concurrent(["ก", "ข", "ค"])
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

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
class AsyncAPIResponse:
    """Structured response from ORST API.

    Attributes:
        total_count: Total number of words for this Thai character
        words: List of headwords for the current page
        page: Page number of this response
        domain: Thai character (domain) for this response
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


class AsyncORSTAPIClient:
    """Async HTTP client for ORST Dictionary API.

    This client implements:
    - Concurrent requests with configurable concurrency limit
    - Polite crawling with rate limiting
    - Automatic retries with exponential backoff
    - Optional response caching

    Attributes:
        config: Scraper configuration
        semaphore: Asyncio semaphore for concurrency control
    """

    def __init__(
        self,
        config: ScraperConfig,
        max_concurrent: int = 5,
    ) -> None:
        """Initialize the async API client.

        Args:
            config: Scraper configuration
            max_concurrent: Maximum concurrent requests (default: 5)
        """
        self.config = config
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._client: httpx.AsyncClient | None = None
        self._last_request_time: float = 0

        # Ensure cache directory exists
        if config.cache_enabled:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=API_BASE_URL,
                headers={"User-Agent": USER_AGENT},
                timeout=httpx.Timeout(REQUEST_TIMEOUT),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncORSTAPIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    def _get_cache_path(self, domain: str, page: int) -> Path:
        """Get cache file path for a specific request."""
        cache_key = hashlib.md5(  # noqa: S324
            f"{domain}_{page}".encode()
        ).hexdigest()
        return CACHE_DIR / f"async_{cache_key}.json"

    async def _load_from_cache(self, domain: str, page: int) -> AsyncAPIResponse | None:
        """Try to load response from cache."""
        if not self.config.cache_enabled:
            return None

        cache_path = self._get_cache_path(domain, page)
        if not cache_path.exists():
            return None

        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            logger.debug("Cache hit for %s page %d", domain, page)
            return AsyncAPIResponse(
                total_count=data["total_count"],
                words=data["words"],
                page=data["page"],
                domain=data["domain"],
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Cache read error for %s page %d: %s", domain, page, e)
            return None

    async def _save_to_cache(self, response: AsyncAPIResponse) -> None:
        """Save response to cache."""
        if not self.config.cache_enabled:
            return

        cache_path = self._get_cache_path(response.domain, response.page)
        data = {
            "total_count": response.total_count,
            "words": response.words,
            "page": response.page,
            "domain": response.domain,
        }
        cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    async def _wait_for_rate_limit(self) -> None:
        """Implement polite crawler delay between requests."""
        if self.config.delay_ms > 0:
            await asyncio.sleep(self.config.delay_ms / 1000)

    async def fetch_page(self, domain: str, page: int) -> AsyncAPIResponse:
        """Fetch a single page of words for a Thai character.

        Args:
            domain: Thai character (e.g., 'ก', 'ข')
            page: Page number (1-indexed)

        Returns:
            AsyncAPIResponse containing words and metadata

        Raises:
            httpx.HTTPError: If the request fails after retries
            ValueError: If the API response is invalid
        """
        # Check cache first
        cached = await self._load_from_cache(domain, page)
        if cached:
            return cached

        # Apply rate limiting
        async with self.semaphore:
            await self._wait_for_rate_limit()

            client = await self._get_client()

            params: dict[str, str | int] = {
                "domain": domain,
                "page": page,
            }

            # Retry logic with exponential backoff
            last_error: Exception | None = None
            for attempt in range(self.config.max_retries + 1):
                try:
                    response = await client.get(API_ENDPOINT, params=params)
                    response.raise_for_status()

                    data: Any = response.json()

                    # Parse response
                    if (
                        isinstance(data, list)
                        and len(data) >= 2
                        and isinstance(data[1], list)
                    ):
                        total_count = int(data[0])
                        words = [
                            item.get("headword", item.get("word", ""))
                            for item in data[1]
                            if isinstance(item, dict)
                        ]
                    else:
                        raise ValueError(f"Unexpected API response format: {data!r}")

                    result = AsyncAPIResponse(
                        total_count=total_count,
                        words=words,
                        page=page,
                        domain=domain,
                    )

                    # Cache the result
                    await self._save_to_cache(result)

                    logger.debug(
                        "Fetched %s page %d/%d (%d words)",
                        domain,
                        page,
                        result.total_pages,
                        len(words),
                    )
                    return result

                except (httpx.HTTPError, ValueError) as e:
                    last_error = e
                    if attempt < self.config.max_retries:
                        delay = RETRY_BACKOFF_BASE ** (attempt + 1)
                        logger.warning(
                            "Request failed for %s page %d (attempt %d/%d), "
                            "retrying in %.1fs: %s",
                            domain,
                            page,
                            attempt + 1,
                            self.config.max_retries + 1,
                            delay,
                            e,
                        )
                        await asyncio.sleep(delay)

            raise RuntimeError(
                f"Failed to fetch {domain} page {page} after "
                f"{self.config.max_retries + 1} attempts"
            ) from last_error

    async def fetch_all_pages(self, domain: str) -> list[str]:
        """Fetch all pages of words for a Thai character.

        Args:
            domain: Thai character (e.g., 'ก', 'ข')

        Returns:
            Complete list of all words for this character
        """
        # Get first page to determine total pages
        first_page = await self.fetch_page(domain, 1)
        all_words = list(first_page.words)

        if first_page.total_pages <= 1:
            return all_words

        # Fetch remaining pages concurrently
        tasks = [
            self.fetch_page(domain, page)
            for page in range(2, first_page.total_pages + 1)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for resp in responses:
            if isinstance(resp, AsyncAPIResponse):
                all_words.extend(resp.words)
            elif isinstance(resp, Exception):
                logger.error("Error fetching page: %s", resp)

        return all_words

    async def fetch_all_domains_concurrent(
        self, domains: list[str]
    ) -> dict[str, list[str]]:
        """Fetch all words for multiple Thai characters concurrently.

        This is the main entry point for high-performance scraping.

        Args:
            domains: List of Thai characters to scrape

        Returns:
            Dictionary mapping each character to its word list
        """
        logger.info(
            "Starting concurrent fetch for %d domains with max %d concurrent requests",
            len(domains),
            self.max_concurrent,
        )

        async def fetch_domain(domain: str) -> tuple[str, list[str]]:
            words = await self.fetch_all_pages(domain)
            logger.info("Completed %s: %d words", domain, len(words))
            return domain, words

        tasks = [fetch_domain(d) for d in domains]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        domain_words: dict[str, list[str]] = {}
        for result in results:
            if isinstance(result, tuple):
                domain, words = result
                domain_words[domain] = words
            elif isinstance(result, Exception):
                logger.error("Domain fetch error: %s", result)

        return domain_words
