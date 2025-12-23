"""Progress tracker for resumable scraping operations.

This module provides functionality to save and restore scraper progress,
allowing interruption and resumption of long-running scrape operations.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from scripts.config import PROGRESS_FILE

logger = logging.getLogger(__name__)


@dataclass
class ProgressState:
    """State information for resumable scraping.
    
    Attributes:
        current_char_index: Index in THAI_ALPHABET of current character
        completed_chars: Set of completed Thai characters
        total_words_scraped: Total word count scraped so far
        last_update_time: ISO timestamp of last update
        partial_results: Dict mapping Thai char to list of words
    """
    
    current_char_index: int = 0
    completed_chars: set[str] = field(default_factory=set)
    total_words_scraped: int = 0
    last_update_time: str = ""
    partial_results: dict[str, list[str]] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        pass
    
    def mark_completed(self, char: str, words: list[str]) -> None:
        """Mark a character as completed and store its words.
        
        Args:
            char: Thai character that was completed
            words: List of words extracted for this character
        """
        self.completed_chars.add(char)
        self.partial_results[char] = words
        self.total_words_scraped += len(words)
        
        from datetime import datetime
        self.last_update_time = datetime.now().isoformat()
    
    def is_completed(self, char: str) -> bool:
        """Check if a character has already been completed.
        
        Args:
            char: Thai character to check
            
        Returns:
            True if this character was already scraped
        """
        return char in self.completed_chars
    
    def get_all_words(self) -> list[str]:
        """Get all words from partial results.
        
        Returns:
            Flat list of all scraped words
        """
        all_words = []
        for words in self.partial_results.values():
            all_words.extend(words)
        return all_words


class ProgressTracker:
    """Manages progress state persistence for resumable operations."""
    
    def __init__(self, progress_file: Path = PROGRESS_FILE):
        """Initialize the progress tracker.
        
        Args:
            progress_file: Path to progress state file
        """
        self.progress_file = progress_file
        self.state = ProgressState()
    
    def load(self) -> bool:
        """Load progress state from file.
        
        Returns:
            True if state was loaded successfully, False otherwise
        """
        if not self.progress_file.exists():
            logger.info("No existing progress file found, starting fresh")
            return False
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.state = ProgressState(
                current_char_index=data.get('current_char_index', 0),
                completed_chars=set(data.get('completed_chars', [])),
                total_words_scraped=data.get('total_words_scraped', 0),
                last_update_time=data.get('last_update_time', ''),
                partial_results=data.get('partial_results', {})
            )

            logger.info(
                f"Loaded progress: {len(self.state.completed_chars)} chars "
                f"completed, {self.state.total_words_scraped} words scraped"
            )
            return True

        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning(f"Failed to load progress file: {e}")
            return False
    
    def save(self) -> None:
        """Save current progress state to file."""
        # Ensure parent directory exists
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'current_char_index': self.state.current_char_index,
                    'completed_chars': list(self.state.completed_chars),
                    'total_words_scraped': self.state.total_words_scraped,
                    'last_update_time': self.state.last_update_time,
                    'partial_results': self.state.partial_results,
                }, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Progress saved to {self.progress_file}")
            
        except IOError as e:
            logger.error(f"Failed to save progress: {e}")
    
    def clear(self) -> None:
        """Clear progress state and delete progress file."""
        self.state = ProgressState()
        
        if self.progress_file.exists():
            try:
                self.progress_file.unlink()
                logger.info("Progress file cleared")
            except IOError as e:
                logger.warning(f"Failed to delete progress file: {e}")
    
    def update_char_index(self, index: int) -> None:
        """Update current character index and save.
        
        Args:
            index: New character index
        """
        self.state.current_char_index = index
        self.save()
    
    def mark_char_completed(self, char: str, words: list[str]) -> None:
        """Mark a character as completed and save progress.
        
        Args:
            char: Thai character
            words: Scraped words for this character
        """
        self.state.mark_completed(char, words)
        self.save()
        
        logger.info(
            f"Progress: {len(self.state.completed_chars)} chars completed, "
            f"{self.state.total_words_scraped} total words"
        )
