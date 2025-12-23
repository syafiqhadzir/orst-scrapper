"""Main ORST Dictionary Scraper.

This is the primary entry point for scraping the Thai Royal Institute Dictionary.
It orchestrates the entire scraping process, data processing, and output generation.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from scripts.api_client import ORSTAPIClient
from scripts.config import (
    DEFAULT_SCRAPER_CONFIG,
    THAI_ALPHABET,
    ScraperConfig,
)
from scripts.progress_tracker import ProgressTracker
from scripts.thai_utils import (
    deduplicate_preserving_order,
    filter_invalid_words,
    normalize_thai_unicode,
    sort_thai_words,
)

logger = logging.getLogger(__name__)


class ORSTScraper:
    """Main scraper orchestrator for ORST Dictionary.
    
    This class manages the complete scraping workflow:
    1. Iterate through Thai alphabet
    2. Fetch all words for each character
    3. Process and validate words
    4. Track progress for resumability
    5. Generate output files
    """
    
    def __init__(
        self,
        config: ScraperConfig = DEFAULT_SCRAPER_CONFIG,
        resume: bool = True
    ):
        """Initialize the scraper.
        
        Args:
            config: Scraper configuration
            resume: Whether to resume from saved progress
        """
        self.config = config
        self.client = ORSTAPIClient(config)
        self.progress = ProgressTracker()
        self.all_words: list[str] = []
        
        # Load progress if resuming
        if resume and config.resume_enabled:
            if self.progress.load():
                self.all_words = self.progress.state.get_all_words()
                logger.info(
                    f"Resuming from character index "
                    f"{self.progress.state.current_char_index}"
                )
    
    def scrape_character(self, char: str) -> list[str]:
        """Scrape all words for a single Thai character.
        
        Args:
            char: Thai character to scrape
            
        Returns:
            List of words for this character
        """
        # Check if already completed
        if self.progress.state.is_completed(char):
            logger.info(f"Skipping {char} (already completed)")
            return self.progress.state.partial_results[char]
        
        # Fetch all pages for this character
        words = self.client.fetch_all_pages(char)
        
        # Apply Unicode normalization if enabled
        if self.config.normalize_unicode:
            words = [normalize_thai_unicode(w) for w in words]
        
        # Mark as completed in progress tracker
        self.progress.mark_char_completed(char, words)
        
        return words
    
    def scrape_all(self) -> list[str]:
        """Scrape all characters in the Thai alphabet.
        
        Returns:
            Complete list of all scraped words (unsorted, may have duplicates)
        """
        start_index = self.progress.state.current_char_index
        
        logger.info(
            f"Starting scrape from character {start_index + 1}/"
            f"{len(THAI_ALPHABET)}"
        )
        
        # Create progress bar
        with tqdm(
            total=len(THAI_ALPHABET),
            initial=start_index,
            desc="Scraping ORST",
            unit="char"
        ) as pbar:
            
            for index in range(start_index, len(THAI_ALPHABET)):
                char = THAI_ALPHABET[index]
                
                try:
                    # Scrape this character
                    words = self.scrape_character(char)
                    self.all_words.extend(words)
                    
                    # Update progress
                    self.progress.update_char_index(index + 1)
                    pbar.update(1)
                    pbar.set_postfix({
                        'char': char,
                        'words': len(words),
                        'total': len(self.all_words)
                    })
                    
                except Exception as e:
                    logger.error(
                        f"Failed to scrape character {char} at index {index}: {e}"
                    )
                    logger.info("Progress has been saved. You can resume later.")
                    raise
        
        logger.info(f"Scraping complete! Total words: {len(self.all_words)}")
        return self.all_words
    
    def process_words(self, words: list[str]) -> list[str]:
        """Process and clean the word list.
        
        This applies:
        1. Filtering (invalid characters, compound words)
        2. Deduplication
        3. Thai Royal Institute sorting
        
        Args:
            words: Raw word list
            
        Returns:
            Processed, sorted, deduplicated word list
        """
        logger.info(f"Processing {len(words)} words...")
        
        # Filter invalid words
        valid_words = filter_invalid_words(
            words,
            allow_compounds=self.config.include_compound_words,
            strict_thai_only=self.config.validate_thai_only
        )
        logger.info(f"After filtering: {len(valid_words)} valid words")
        
        # Deduplicate
        unique_words = deduplicate_preserving_order(valid_words)
        duplicates_removed = len(valid_words) - len(unique_words)
        logger.info(
            f"After deduplication: {len(unique_words)} unique words "
            f"({duplicates_removed} duplicates removed)"
        )
        
        # Sort using Thai Royal Institute order
        sorted_words = sort_thai_words(unique_words)
        logger.info("Words sorted in Royal Institute order")
        
        return sorted_words
    
    def run(self) -> list[str]:
        """Run the complete scraping and processing pipeline.
        
        Returns:
            Final processed word list
        """
        logger.info("=== ORST Dictionary Scraper Starting ===")
        logger.info(f"Configuration: {self.config}")
        
        try:
            # Scrape all words
            raw_words = self.scrape_all()
            
            # Process words
            processed_words = self.process_words(raw_words)
            
            # Clear progress (successful completion)
            self.progress.clear()
            
            logger.info("=== Scraping Complete ===")
            logger.info(f"Final word count: {len(processed_words)}")
            
            return processed_words
            
        except KeyboardInterrupt:
            logger.warning("Scraping interrupted by user")
            logger.info("Progress has been saved. Run again to resume.")
            raise
        
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
        
        finally:
            self.client.close()
    
    def __enter__(self) -> "ORSTScraper":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]) -> None:
        """Context manager exit."""
        self.client.close()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the scraper.
    
    Args:
        verbose: If True, set to DEBUG level, otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/scraper.log', encoding='utf-8')
        ]
    )


def main() -> int:
    """Main entry point for the scraper CLI.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape the Thai Royal Institute Dictionary (ORST)'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Start fresh instead of resuming from saved progress'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable API response caching'
    )
    parser.add_argument(
        '--no-compounds',
        action='store_true',
        help='Exclude compound words (entries with spaces)'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=200,
        help='Delay in milliseconds between requests (default: 200)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (if not specified, returns word list only)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Create configuration
    config = ScraperConfig(
        delay_ms=args.delay,
        include_compound_words=not args.no_compounds,
        cache_enabled=not args.no_cache,
        resume_enabled=not args.no_resume,
    )
    
    try:
        # Run scraper
        with ORSTScraper(config=config, resume=not args.no_resume) as scraper:
            words = scraper.run()
        
        # Output results
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                for word in words:
                    f.write(f"{word}\n")
            logger.info(f"Words saved to {args.output}")
        else:
            logger.info(f"Scraped {len(words)} words successfully")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
