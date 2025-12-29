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

# Rich imports for enhanced CLI
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table
from rich.theme import Theme

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

# Custom theme for consistent styling
custom_theme = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "step": "bold blue",
    }
)

console = Console(theme=custom_theme)

# File paths
PROJECT_ROOT = Path(__file__).parent
CURRENT_DIC_FILE = PROJECT_ROOT / "th_TH-royin.dic"
NEW_DIC_FILE = PROJECT_ROOT / "th_TH-royin.new.dic"
BACKUP_DIC_FILE = PROJECT_ROOT / "th_TH-royin.backup.dic"
AUDIT_REPORT_FILE = PROJECT_ROOT / "reports" / "audit_report.md"
ADDED_WORDS_FILE = PROJECT_ROOT / "reports" / "added_words.txt"
GHOST_WORDS_FILE = PROJECT_ROOT / "reports" / "ghost_words.txt"


def print_banner() -> None:
    """Print application banner."""
    banner = """
[bold cyan]╔═══════════════════════════════════════════════════════════╗
║       ORST Dictionary Synchronization Tool                ║
║       Thai Royal Institute Dictionary Updater             ║
╚═══════════════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner)


def print_summary_table(diff: object) -> None:
    """Print a summary table of dictionary changes."""
    table = Table(
        title="Dictionary Comparison Summary",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Status", justify="center")

    table.add_row("Previous words", str(diff.old_count), "📚")
    table.add_row("New words", str(diff.new_count), "📖")
    table.add_row(
        "Added",
        str(diff.added_count),
        "[green]✓[/green]" if diff.added_count > 0 else "-",
    )
    table.add_row(
        "Removed (ghosts)",
        str(diff.removed_count),
        "[red]⚠[/red]" if diff.removed_count > 0 else "-",
    )
    table.add_row("Unchanged", str(diff.unchanged_count), "-")
    table.add_row("Net change", f"{diff.new_count - diff.old_count:+}", "📊")

    console.print(table)


def main() -> int:
    """Main workflow for updating th_TH-royin.dic.

    Returns:
        Exit code (0 for success)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Update th_TH-royin.dic from ORST Dictionary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run          Run without saving changes
  %(prog)s --delay 500        Slower requests (polite crawling)
  %(prog)s --verbose          Enable debug logging
        """,
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
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    args = parser.parse_args()

    # Disable colors if requested
    if args.no_color:
        console.no_color = True

    # Setup logging
    setup_logging(args.verbose)

    # Print banner
    print_banner()

    if args.dry_run:
        console.print(
            Panel(
                "[yellow]DRY RUN MODE[/yellow] - No changes will be saved",
                style="yellow",
            )
        )

    try:
        # Step 1: Scrape ORST dictionary
        console.print(
            "\n[step]Step 1/5[/step] Scraping ORST Dictionary...", style="step"
        )
        config = ScraperConfig(delay_ms=args.delay)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Fetching words from ORST API...", total=None
            )

            with ORSTScraper(config=config) as scraper:
                new_words = scraper.run()

            progress.update(
                task, completed=True, description="[green]Scraping complete!"
            )

        console.print(
            f"[success]✓ Scraped {len(new_words):,} words from ORST[/success]\n"
        )

        # Step 2: Load existing dictionary
        console.print(
            "[step]Step 2/5[/step] Loading existing dictionary...", style="step"
        )
        writer = HunspellDictionaryWriter()

        if CURRENT_DIC_FILE.exists():
            old_words = writer.read(CURRENT_DIC_FILE)
            console.print(
                f"[success]✓ Loaded {len(old_words):,} words from {CURRENT_DIC_FILE.name}[/success]\n"
            )
        else:
            console.print(
                f"[warning]⚠ No existing dictionary found at {CURRENT_DIC_FILE}[/warning]"
            )
            old_words = []

        # Step 3: Compare dictionaries
        console.print("[step]Step 3/5[/step] Comparing dictionaries...", style="step")
        diff = compare_dictionaries(old_words, new_words)

        console.print("[success]✓ Comparison complete[/success]\n")
        print_summary_table(diff)

        # Step 4: Generate reports
        console.print(
            "\n[step]Step 4/5[/step] Generating audit reports...", style="step"
        )

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

        console.print(
            f"[success]✓ Audit report saved to {AUDIT_REPORT_FILE}[/success]\n"
        )

        # Step 5: Update dictionary file
        if args.dry_run:
            console.print(
                "[step]Step 5/5[/step] Dry run - skipping dictionary update",
                style="step",
            )
            console.print(f"Would write {len(new_words):,} words to {CURRENT_DIC_FILE}")
            console.print(
                Panel(
                    f"[green]Dry run complete![/green]\nReview: {AUDIT_REPORT_FILE}",
                    title="Summary",
                )
            )
        else:
            console.print(
                "[step]Step 5/5[/step] Updating dictionary file...", style="step"
            )

            # Backup existing file
            if CURRENT_DIC_FILE.exists() and not args.no_backup:
                import shutil

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = (
                    CURRENT_DIC_FILE.parent / f"th_TH-royin.{timestamp}.backup.dic"
                )
                shutil.copy2(CURRENT_DIC_FILE, backup_path)
                console.print(f"[info]✓ Backup created: {backup_path}[/info]")

            # Write new dictionary
            header_comment = (
                f"Thai Royal Institute Dictionary (ORST)\n"
                f"Synchronized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Source: https://dictionary.orst.go.th/"
            )

            writer.write(new_words, CURRENT_DIC_FILE, header_comment=header_comment)

            console.print(
                f"[success]✓ Dictionary updated: {CURRENT_DIC_FILE}[/success]"
            )

            # Validate the file
            is_valid, errors = writer.validate_format(CURRENT_DIC_FILE)
            if is_valid:
                console.print(
                    "[success]✓ Dictionary file validation passed[/success]\n"
                )
            else:
                console.print("[error]✗ Dictionary file validation failed:[/error]")
                for error in errors:
                    console.print(f"  [error]- {error}[/error]")
                return 1

        # Final summary panel
        summary_text = f"""
[bold]Previous words:[/bold] {diff.old_count:,}
[bold]New words:[/bold] {diff.new_count:,}
[bold]Net change:[/bold] {diff.new_count - diff.old_count:+,}

[dim]Audit report: {AUDIT_REPORT_FILE}[/dim]
        """
        console.print(
            Panel(
                summary_text,
                title="[bold green]Synchronization Complete[/bold green]",
                border_style="green",
            )
        )

        if diff.removed_count > 0:
            console.print(
                Panel(
                    f"[yellow]{diff.removed_count} ghost words detected![/yellow]\n"
                    f"Review: {GHOST_WORDS_FILE}",
                    title="⚠ Warning",
                    border_style="yellow",
                )
            )

        return 0

    except KeyboardInterrupt:
        console.print("\n[warning]✗ Interrupted by user[/warning]")
        return 130

    except Exception as e:
        console.print(
            Panel(f"[red]Error: {e}[/red]", title="✗ Failed", border_style="red")
        )
        if args.verbose:
            console.print_exception()
        return 1


if __name__ == "__main__":
    sys.exit(main())
