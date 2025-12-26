#!/usr/bin/env python3
"""Update th_TH-royin.dic from ORST Dictionary.

This is the main entry point script that orchestrates the complete workflow:
1. Scrape ORST dictionary
2. Process and validate words
3. Compare with existing dictionary
4. Generate audit report
5. Update dictionary file
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.config import ScraperConfig
from scripts.dictionary_diff import (
    compare_dictionaries,
    generate_audit_report,
    save_word_list,
)
from scripts.hunspell_writer import HunspellDictionaryWriter
from scripts.orst_scraper import ORSTScraper, setup_logging

logger = logging.getLogger(__name__)

# File paths
PROJECT_ROOT = Path(__file__).parent
CURRENT_DIC_FILE = PROJECT_ROOT / "th_TH-royin.dic"
NEW_DIC_FILE = PROJECT_ROOT / "th_TH-royin.new.dic"
BACKUP_DIC_FILE = PROJECT_ROOT / "th_TH-royin.backup.dic"
AUDIT_REPORT_FILE = PROJECT_ROOT / "reports" / "audit_report.md"
ADDED_WORDS_FILE = PROJECT_ROOT / "reports" / "added_words.txt"
GHOST_WORDS_FILE = PROJECT_ROOT / "reports" / "ghost_words.txt"


def main() -> int:
    """Main workflow for updating th_TH-royin.dic.

    Returns:
        Exit code (0 for success)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Update th_TH-royin.dic from ORST Dictionary"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate reports but do not update dictionary file",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backup of existing dictionary",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=200,
        help="Delay in milliseconds between API requests (default: 200)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose debug logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    logger.info("=" * 60)
    logger.info("ORST Dictionary Synchronization Tool")
    logger.info("=" * 60)

    try:
        # Step 1: Scrape ORST dictionary
        logger.info("\n[Step 1/5] Scraping ORST Dictionary...")
        config = ScraperConfig(delay_ms=args.delay)

        with ORSTScraper(config=config) as scraper:
            new_words = scraper.run()

        logger.info(f"✓ Scraped {len(new_words)} words from ORST\n")

        # Step 2: Load existing dictionary
        logger.info("[Step 2/5] Loading existing dictionary...")
        writer = HunspellDictionaryWriter()

        if CURRENT_DIC_FILE.exists():
            old_words = writer.read(CURRENT_DIC_FILE)
            logger.info(
                f"✓ Loaded {len(old_words)} words from {CURRENT_DIC_FILE.name}\n"
            )
        else:
            logger.warning(f"No existing dictionary found at {CURRENT_DIC_FILE}")
            old_words = []

        # Step 3: Compare dictionaries
        logger.info("[Step 3/5] Comparing dictionaries...")
        diff = compare_dictionaries(old_words, new_words)

        logger.info("✓ Comparison complete:")
        logger.info(f"  Added: {diff.added_count}")
        logger.info(f"  Removed (ghosts): {diff.removed_count}")
        logger.info(f"  Unchanged: {diff.unchanged_count}\n")

        # Step 4: Generate reports
        logger.info("[Step 4/5] Generating audit reports...")

        generate_audit_report(
            diff,
            AUDIT_REPORT_FILE,
            old_file_name=CURRENT_DIC_FILE.name,
            new_file_name="ORST Dictionary (scraped)",
        )

        if diff.added_count > 0:
            save_word_list(diff.added_words, ADDED_WORDS_FILE, "added words")

        if diff.removed_count > 0:
            save_word_list(diff.removed_words, GHOST_WORDS_FILE, "ghost words")

        logger.info(f"✓ Audit report saved to {AUDIT_REPORT_FILE}\n")

        # Step 5: Update dictionary file
        if args.dry_run:
            logger.info("[Step 5/5] Dry run - skipping dictionary update")
            logger.info(f"Would write {len(new_words)} words to {CURRENT_DIC_FILE}")
            logger.info(f"\n✓ Dry run complete. Review {AUDIT_REPORT_FILE}")
        else:
            logger.info("[Step 5/5] Updating dictionary file...")

            # Backup existing file
            if CURRENT_DIC_FILE.exists() and not args.no_backup:
                import shutil

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = (
                    CURRENT_DIC_FILE.parent / f"th_TH-royin.{timestamp}.backup.dic"
                )
                shutil.copy2(CURRENT_DIC_FILE, backup_path)
                logger.info(f"✓ Backup created: {backup_path}")

            # Write new dictionary
            header_comment = (
                f"Thai Royal Institute Dictionary (ORST)\n"
                f"Synchronized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Source: https://dictionary.orst.go.th/"
            )

            writer.write(new_words, CURRENT_DIC_FILE, header_comment=header_comment)

            logger.info(f"✓ Dictionary updated: {CURRENT_DIC_FILE}")

            # Validate the file
            is_valid, errors = writer.validate_format(CURRENT_DIC_FILE)
            if is_valid:
                logger.info("✓ Dictionary file validation passed\n")
            else:
                logger.error("✗ Dictionary file validation failed:")
                for error in errors:
                    logger.error(f"  - {error}")
                return 1

        # Final summary
        logger.info("=" * 60)
        logger.info("Summary")
        logger.info("=" * 60)
        logger.info(f"Old word count: {diff.old_count}")
        logger.info(f"New word count: {diff.new_count}")
        logger.info(f"Net change: {diff.new_count - diff.old_count:+}")
        logger.info(f"\nAudit report: {AUDIT_REPORT_FILE}")

        if diff.removed_count > 0:
            logger.warning(
                f"\n⚠ WARNING: {diff.removed_count} ghost words detected!\n"
                f"Review {GHOST_WORDS_FILE} for manual inspection."
            )

        logger.info("\n✓ Synchronization complete!\n")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n✗ Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"\n✗ Failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
