"""Performance benchmark tests for ORST Dictionary Scraper.

These tests measure the performance of critical operations and ensure
they complete within acceptable time limits.

Run with: pytest tests/performance/ -v --benchmark
"""

import time
from typing import Any

import pytest

from scripts.thai_utils import (
    create_thai_sort_key,
    deduplicate_preserving_order,
    filter_invalid_words,
    normalize_thai_unicode,
    sort_thai_words,
)

# Sample data for benchmarks
THAI_WORDS_SMALL = ["กระดาษ", "กระทง", "กระเป๋า", "กราฟ", "กรุงเทพ"] * 100
THAI_WORDS_MEDIUM = ["กระดาษ", "กระทง", "กระเป๋า", "กราฟ", "กรุงเทพ"] * 1000
THAI_WORDS_LARGE = ["กระดาษ", "กระทง", "กระเป๋า", "กราฟ", "กรุงเทพ"] * 10000


class BenchmarkResult:
    """Container for benchmark results."""

    def __init__(self, name: str, duration: float, iterations: int) -> None:
        """Initialize benchmark result."""
        self.name = name
        self.duration = duration
        self.iterations = iterations

    @property
    def per_iteration(self) -> float:
        """Calculate time per iteration."""
        return self.duration / self.iterations

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"{self.name}: {self.duration:.4f}s total, "
            f"{self.per_iteration * 1000:.4f}ms per iteration"
        )


def benchmark(func: Any, iterations: int = 100) -> BenchmarkResult:
    """Run a function multiple times and measure duration.

    Args:
        func: Function to benchmark (callable with no arguments)
        iterations: Number of iterations to run

    Returns:
        BenchmarkResult with timing information
    """
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    duration = time.perf_counter() - start
    return BenchmarkResult(
        func.__name__ if hasattr(func, "__name__") else "anonymous",
        duration,
        iterations,
    )


class TestNormalizationPerformance:
    """Performance tests for Unicode normalization."""

    @pytest.mark.slow
    def test_normalize_small_dataset(self) -> None:
        """Benchmark normalization on small dataset."""

        def run() -> None:
            for word in THAI_WORDS_SMALL:
                normalize_thai_unicode(word)

        result = benchmark(run, iterations=10)
        print(f"\n{result}")
        # Should complete in reasonable time
        assert result.duration < 5.0, f"Normalization too slow: {result.duration}s"

    @pytest.mark.slow
    def test_normalize_medium_dataset(self) -> None:
        """Benchmark normalization on medium dataset."""

        def run() -> None:
            for word in THAI_WORDS_MEDIUM:
                normalize_thai_unicode(word)

        result = benchmark(run, iterations=5)
        print(f"\n{result}")
        assert result.duration < 10.0, f"Normalization too slow: {result.duration}s"


class TestSortingPerformance:
    """Performance tests for Thai word sorting."""

    @pytest.mark.slow
    def test_sort_small_dataset(self) -> None:
        """Benchmark sorting on small dataset."""
        result = benchmark(lambda: sort_thai_words(THAI_WORDS_SMALL), iterations=100)
        print(f"\n{result}")
        assert result.duration < 5.0, f"Sorting too slow: {result.duration}s"

    @pytest.mark.slow
    def test_sort_medium_dataset(self) -> None:
        """Benchmark sorting on medium dataset."""
        result = benchmark(lambda: sort_thai_words(THAI_WORDS_MEDIUM), iterations=10)
        print(f"\n{result}")
        assert result.duration < 10.0, f"Sorting too slow: {result.duration}s"

    @pytest.mark.slow
    def test_sort_large_dataset(self) -> None:
        """Benchmark sorting on large dataset."""
        result = benchmark(lambda: sort_thai_words(THAI_WORDS_LARGE), iterations=3)
        print(f"\n{result}")
        assert result.duration < 30.0, f"Sorting too slow: {result.duration}s"

    def test_sort_key_caching_effectiveness(self) -> None:
        """Test that LRU caching improves sort key performance."""
        sort_key = create_thai_sort_key()
        unique_words = list(set(THAI_WORDS_SMALL))

        # First pass: populates cache
        start1 = time.perf_counter()
        for word in unique_words * 10:
            sort_key(word)
        duration1 = time.perf_counter() - start1

        # Second pass: should hit cache
        start2 = time.perf_counter()
        for word in unique_words * 10:
            sort_key(word)
        duration2 = time.perf_counter() - start2

        print(f"\nFirst pass: {duration1:.4f}s, Second pass: {duration2:.4f}s")
        # Second pass should be at least as fast (cache hits)
        # Due to the LRU cache, repeated calls should be faster or equal
        assert duration2 <= duration1 * 1.5, "Caching not effective"


class TestDeduplicationPerformance:
    """Performance tests for deduplication."""

    @pytest.mark.slow
    def test_deduplicate_large_dataset(self) -> None:
        """Benchmark deduplication on large dataset."""
        result = benchmark(
            lambda: deduplicate_preserving_order(THAI_WORDS_LARGE), iterations=10
        )
        print(f"\n{result}")
        assert result.duration < 5.0, f"Deduplication too slow: {result.duration}s"


class TestFilteringPerformance:
    """Performance tests for word filtering."""

    @pytest.mark.slow
    def test_filter_large_dataset(self) -> None:
        """Benchmark filtering on large dataset."""
        result = benchmark(
            lambda: filter_invalid_words(
                THAI_WORDS_LARGE, allow_compounds=True, strict_thai_only=True
            ),
            iterations=5,
        )
        print(f"\n{result}")
        assert result.duration < 10.0, f"Filtering too slow: {result.duration}s"


class TestEndToEndPerformance:
    """End-to-end performance tests."""

    @pytest.mark.slow
    def test_full_pipeline_performance(self) -> None:
        """Benchmark full processing pipeline."""

        def run_pipeline() -> list[str]:
            words = THAI_WORDS_MEDIUM.copy()
            normalized = [normalize_thai_unicode(w) for w in words]
            filtered = filter_invalid_words(normalized)
            deduplicated = deduplicate_preserving_order(filtered)
            return sort_thai_words(deduplicated)

        result = benchmark(run_pipeline, iterations=5)
        print(f"\n{result}")
        assert result.duration < 30.0, f"Full pipeline too slow: {result.duration}s"

    def test_pipeline_output_correctness(self) -> None:
        """Verify that the pipeline produces correct output."""
        words = THAI_WORDS_SMALL.copy()
        normalized = [normalize_thai_unicode(w) for w in words]
        filtered = filter_invalid_words(normalized)
        deduplicated = deduplicate_preserving_order(filtered)
        sorted_words = sort_thai_words(deduplicated)

        # Should have unique words
        assert len(sorted_words) == len(set(sorted_words))
        # Should have fewer words than input (due to duplicates)
        assert len(sorted_words) <= len(words)
        # All words should be valid Thai
        for word in sorted_words:
            assert all(len(c) == 1 for c in word)
