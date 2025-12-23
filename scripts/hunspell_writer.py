"""Hunspell dictionary file generator.

This module handles the creation of properly formatted Hunspell .dic files
from word lists, following the Hunspell specification.
"""

import logging
from pathlib import Path

from scripts.config import DEFAULT_HUNSPELL_CONFIG, HunspellConfig

logger = logging.getLogger(__name__)


class HunspellDictionaryWriter:
    """Writer for Hunspell .dic dictionary files.
    
    Hunspell dictionary format:
    - Line 1: Word count (e.g., "45000" or "# 45000")
    - Lines 2+: One word per line
    - Encoding: UTF-8 (no BOM)
    - Optional: Affix flags after each word (future feature)
    """

    def __init__(self, config: HunspellConfig = DEFAULT_HUNSPELL_CONFIG):
        """Initialize the dictionary writer.
        
        Args:
            config: Hunspell configuration
        """
        self.config = config

    def write(
        self,
        words: list[str],
        output_path: Path,
        header_comment: str | None = None
    ) -> None:
        """Write words to a Hunspell dictionary file.
        
        Args:
            words: Sorted list of dictionary words
            output_path: Path to output .dic file
            header_comment: Optional comment to add after word count
        """
        if not words:
            raise ValueError("Cannot create dictionary from empty word list")

        # Validate one word per line
        if self.config.one_word_per_line:
            for i, word in enumerate(words):
                if '\n' in word or '\r' in word:
                    raise ValueError(
                        f"Word at index {i} contains newline: {repr(word)}"
                    )

        logger.info(f"Writing {len(words)} words to {output_path}")

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, 'w', encoding=self.config.encoding, newline='\n') as f:
                # Write word count header
                if self.config.use_count_header:
                    f.write(f"# {len(words)}\n")

                    # Optional header comment
                    if header_comment:
                        for line in header_comment.split('\n'):
                            if line.strip():
                                f.write(f"# {line.strip()}\n")

                # Write each word
                for word in words:
                    f.write(f"{word}\n")

            logger.info(f"Successfully wrote dictionary to {output_path}")

            # Verify file size
            size_kb = output_path.stat().st_size / 1024
            logger.info(f"File size: {size_kb:.2f} KB")

        except OSError as e:
            logger.error(f"Failed to write dictionary file: {e}")
            raise

    def read(self, input_path: Path) -> list[str]:
        """Read words from a Hunspell dictionary file.
        
        Args:
            input_path: Path to existing .dic file
            
        Returns:
            List of words (excluding count header)
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Dictionary file not found: {input_path}")

        logger.info(f"Reading dictionary from {input_path}")

        words = []

        try:
            with open(input_path, encoding=self.config.encoding) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines
                    if not line:
                        continue

                    # Skip count header (line 1)
                    if line_num == 1 and (line.startswith('#') or line.isdigit()):
                        logger.debug(f"Skipping count header: {line}")
                        continue

                    # Skip comment lines
                    if line.startswith('#'):
                        continue

                    # Extract word (before any affix flags)
                    # Affix flags are separated by / (e.g., "word/ABC")
                    word = line.split('/')[0].strip()

                    if word:
                        words.append(word)

            logger.info(f"Read {len(words)} words from {input_path}")
            return words

        except OSError as e:
            logger.error(f"Failed to read dictionary file: {e}")
            raise

    @staticmethod
    def validate_format(file_path: Path) -> tuple[bool, list[str]]:
        """Validate that a file follows Hunspell dictionary format.
        
        Args:
            file_path: Path to dictionary file to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not file_path.exists():
            return False, [f"File does not exist: {file_path}"]

        try:
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()

            if not lines:
                errors.append("File is empty")
                return False, errors

            # Check first line is count header
            first_line = lines[0].strip()
            if not (first_line.startswith('#') or first_line.isdigit()):
                errors.append(
                    f"First line should be word count, got: {first_line[:50]}"
                )
            else:
                # Extract count and verify
                count_str = first_line.lstrip('#').strip()
                try:
                    declared_count = int(count_str)
                    actual_count = sum(
                        1 for line in lines[1:]
                        if line.strip() and not line.strip().startswith('#')
                    )
                    if declared_count != actual_count:
                        errors.append(
                            f"Count mismatch: header says {declared_count}, "
                            f"file has {actual_count} words"
                        )
                except ValueError:
                    errors.append(f"Invalid count header: {count_str}")

            # Check for non-UTF-8 characters
            for i, line in enumerate(lines, 1):
                try:
                    line.encode('utf-8')
                except UnicodeEncodeError as e:
                    errors.append(f"Line {i}: Non-UTF-8 character: {e}")

            return len(errors) == 0, errors

        except Exception as e:
            return False, [f"Validation error: {e}"]
