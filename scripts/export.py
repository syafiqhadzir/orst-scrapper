"""Export utilities for dictionary data.

This module provides functions to export scraped dictionary data
to various formats including JSON, CSV, and SQLite.

Usage:
    from scripts.export import export_to_json, export_to_csv, export_to_sqlite

    words = ["กระดาษ", "กรุงเทพ", "กล้วย"]
    export_to_json(words, Path("output.json"))
    export_to_csv(words, Path("output.csv"))
    export_to_sqlite(words, Path("dictionary.db"))
"""

import csv
import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.thai_utils import normalize_thai_unicode, sort_thai_words

logger = logging.getLogger(__name__)


@dataclass
class ExportMetadata:
    """Metadata for exported dictionary files.

    Attributes:
        total_words: Total number of words exported
        export_date: ISO format date of export
        source: Source of the dictionary data
        version: Version of the exporter
    """

    total_words: int
    export_date: str
    source: str = "ORST Dictionary (dictionary.orst.go.th)"
    version: str = "1.2.0"

    @classmethod
    def create(cls, word_count: int) -> "ExportMetadata":
        """Create metadata with current timestamp.

        Args:
            word_count: Number of words being exported

        Returns:
            ExportMetadata instance
        """
        return cls(
            total_words=word_count,
            export_date=datetime.now(UTC).isoformat(),
        )


def export_to_json(
    words: list[str],
    output_path: Path,
    *,
    sort_words: bool = True,
    include_metadata: bool = True,
    indent: int = 2,
) -> None:
    """Export words to JSON format.

    Args:
        words: List of words to export
        output_path: Path to output JSON file
        sort_words: Whether to sort words in Thai order (default: True)
        include_metadata: Whether to include export metadata (default: True)
        indent: JSON indentation level (default: 2)

    Raises:
        OSError: If file cannot be written
    """
    # Normalize and optionally sort
    processed = [normalize_thai_unicode(w) for w in words]
    if sort_words:
        processed = sort_thai_words(processed)

    # Build output data
    data: dict[str, Any]
    if include_metadata:
        metadata = ExportMetadata.create(len(processed))
        data = {
            "metadata": asdict(metadata),
            "words": processed,
        }
    else:
        data = {"words": processed}

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )

    logger.info("Exported %d words to %s", len(processed), output_path)


def export_to_csv(
    words: list[str],
    output_path: Path,
    *,
    sort_words: bool = True,
    include_index: bool = True,
) -> None:
    """Export words to CSV format.

    Args:
        words: List of words to export
        output_path: Path to output CSV file
        sort_words: Whether to sort words in Thai order (default: True)
        include_index: Whether to include row index (default: True)

    Raises:
        OSError: If file cannot be written
    """
    # Normalize and optionally sort
    processed = [normalize_thai_unicode(w) for w in words]
    if sort_words:
        processed = sort_thai_words(processed)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        # Header
        if include_index:
            writer.writerow(["index", "word"])
        else:
            writer.writerow(["word"])

        # Data rows
        for i, word in enumerate(processed, 1):
            if include_index:
                writer.writerow([i, word])
            else:
                writer.writerow([word])

    logger.info("Exported %d words to %s", len(processed), output_path)


def export_to_sqlite(
    words: list[str],
    output_path: Path,
    *,
    sort_words: bool = True,
    table_name: str = "words",
) -> None:
    """Export words to SQLite database.

    Creates a SQLite database with a words table containing:
    - id: Auto-incrementing primary key
    - word: The Thai word
    - normalized: Unicode NFC normalized form
    - length: Character length of the word

    Args:
        words: List of words to export
        output_path: Path to output SQLite file
        sort_words: Whether to sort words in Thai order (default: True)
        table_name: Name of the table to create (default: "words")

    Raises:
        OSError: If file cannot be written
        sqlite3.Error: If database operation fails
    """
    # Normalize and optionally sort
    processed = [normalize_thai_unicode(w) for w in words]
    if sort_words:
        processed = sort_thai_words(processed)

    # Validate table_name to prevent SQL injection (internal parameter only)
    if not table_name.isidentifier():
        raise ValueError(f"Invalid table name: {table_name}")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database
    if output_path.exists():
        output_path.unlink()

    # Create and populate database
    conn = sqlite3.connect(str(output_path))
    try:
        cursor = conn.cursor()

        # Create words table (table_name is validated above)
        cursor.execute(
            f"CREATE TABLE {table_name} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "word TEXT NOT NULL UNIQUE, "
            "normalized TEXT NOT NULL, "
            "length INTEGER NOT NULL)"
        )

        # Create metadata table
        cursor.execute("""
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Insert metadata
        metadata = ExportMetadata.create(len(processed))
        cursor.executemany(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            [
                ("total_words", str(metadata.total_words)),
                ("export_date", metadata.export_date),
                ("source", metadata.source),
                ("version", metadata.version),
            ],
        )

        # Insert words (table_name is validated above)
        cursor.executemany(
            f"INSERT INTO {table_name} (word, normalized, length) "  # noqa: S608
            "VALUES (?, ?, ?)",
            [(w, normalize_thai_unicode(w), len(w)) for w in processed],
        )

        # Create index for fast lookups (table_name is validated above)
        cursor.execute(f"CREATE INDEX idx_{table_name}_word ON {table_name}(word)")

        conn.commit()
        logger.info(
            "Exported %d words to SQLite database %s", len(processed), output_path
        )

    finally:
        conn.close()


def export_to_hunspell_dic(
    words: list[str],
    output_path: Path,
    *,
    sort_words: bool = True,
) -> None:
    """Export words to Hunspell .dic format.

    The Hunspell format is:
    - First line: word count
    - Subsequent lines: one word per line

    Args:
        words: List of words to export
        output_path: Path to output .dic file
        sort_words: Whether to sort words in Thai order (default: True)

    Raises:
        OSError: If file cannot be written
    """
    # Normalize and optionally sort
    processed = [normalize_thai_unicode(w) for w in words]
    if sort_words:
        processed = sort_thai_words(processed)

    # Remove duplicates
    unique_words = list(dict.fromkeys(processed))

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write Hunspell format
    lines = [str(len(unique_words)), *unique_words]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    logger.info("Exported %d words to %s", len(unique_words), output_path)
