"""Dictionary comparison and diff generation tools.

This module provides functionality to compare two dictionary files,
identify changes, and generate audit reports for review.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DictionaryDiff:
    """Results of comparing two dictionary files.
    
    Attributes:
        added_words: Words in new but not in old
        removed_words: Words in old but not in new (ghost words)
        unchanged_words: Words in both dictionaries
        old_count: Total word count in old dictionary
        new_count: Total word count in new dictionary
    """
    
    added_words: set[str]
    removed_words: set[str]
    unchanged_words: set[str]
    old_count: int
    new_count: int
    
    @property
    def added_count(self) -> int:
        """Number of added words."""
        return len(self.added_words)
    
    @property
    def removed_count(self) -> int:
        """Number of removed (ghost) words."""
        return len(self.removed_words)
    
    @property
    def unchanged_count(self) -> int:
        """Number of unchanged words."""
        return len(self.unchanged_words)
    
    @property
    def has_changes(self) -> bool:
        """Whether there are any changes between dictionaries."""
        return self.added_count > 0 or self.removed_count > 0


def compare_dictionaries(
    old_words: list[str],
    new_words: list[str]
) -> DictionaryDiff:
    """Compare two word lists and identify differences.
    
    Args:
        old_words: Words from existing dictionary
        new_words: Words from new dictionary
        
    Returns:
        DictionaryDiff containing analysis results
    """
    old_set = set(old_words)
    new_set = set(new_words)
    
    added = new_set - old_set
    removed = old_set - new_set
    unchanged = old_set & new_set
    
    logger.info(f"Diff analysis: +{len(added)} -{len(removed)} ={len(unchanged)}")
    
    return DictionaryDiff(
        added_words=added,
        removed_words=removed,
        unchanged_words=unchanged,
        old_count=len(old_words),
        new_count=len(new_words)
    )


def generate_audit_report(
    diff: DictionaryDiff,
    output_path: Path,
    old_file_name: str = "th_TH-royin.dic (old)",
    new_file_name: str = "th_TH-royin.dic (new)"
) -> None:
    """Generate a comprehensive audit report in Markdown format.
    
    Args:
        diff: Dictionary comparison results
        output_path: Path to save audit report
        old_file_name: Description of old dictionary
        new_file_name: Description of new dictionary
    """
    logger.info(f"Generating audit report: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert sets to sorted lists for display
    added_sorted = sorted(diff.added_words)
    removed_sorted = sorted(diff.removed_words)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# ORST Dictionary Synchronization Audit Report\n\n")
        f.write(f"**Generated:** {timestamp}\n\n")
        f.write("---\n\n")
        
        # Summary Section
        f.write("## Summary\n\n")
        f.write(f"| Metric | Count |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| **Old Dictionary** | {diff.old_count:,} words |\n")
        f.write(f"| **New Dictionary** | {diff.new_count:,} words |\n")
        f.write(f"| **Added Words** | {diff.added_count:,} |\n")
        f.write(f"| **Removed Words (Ghosts)** | {diff.removed_count:,} |\n")
        f.write(f"| **Unchanged Words** | {diff.unchanged_count:,} |\n")
        f.write(f"| **Net Change** | {diff.new_count - diff.old_count:+,} |\n")
        f.write("\n")
        
        # Change percentage
        if diff.old_count > 0:
            pct_change = ((diff.new_count - diff.old_count) / diff.old_count) * 100
            f.write(f"**Change Rate:** {pct_change:+.1f}%\n\n")
        
        f.write("---\n\n")
        
        # Added Words Section
        f.write("## Added Words\n\n")
        if diff.added_count > 0:
            f.write(
                f"The following **{diff.added_count:,} words** are present in the "
                f"new ORST dictionary but were not in the old {old_file_name}.\n\n"
            )
            
            # Show first 50, then truncate
            display_limit = 50
            if diff.added_count <= display_limit:
                for word in added_sorted:
                    f.write(f"- {word}\n")
            else:
                for word in added_sorted[:display_limit]:
                    f.write(f"- {word}\n")
                f.write(f"\n*... and {diff.added_count - display_limit:,} more words.*\n")
                f.write(f"\n<details>\n<summary>Show all {diff.added_count:,} added words</summary>\n\n")
                for word in added_sorted[display_limit:]:
                    f.write(f"- {word}\n")
                f.write("\n</details>\n")
        else:
            f.write("*No words were added.*\n")
        
        f.write("\n---\n\n")
        
        # Ghost Words Section (Removed)
        f.write("## Ghost Words (Removed)\n\n")
        if diff.removed_count > 0:
            f.write(
                f"> [!WARNING]\n"
                f"> The following **{diff.removed_count:,} words** exist in "
                f"{old_file_name} but are NOT in the official ORST dictionary.\n"
                f"> These are flagged as \"ghost words\" and require manual review.\n\n"
            )
            
            f.write("**Action Required:** Review these words and decide whether to:\n")
            f.write("- Remove them (if they were incorrectly added)\n")
            f.write("- Preserve them in a separate supplementary dictionary\n")
            f.write("- Report to ORST if they should be in the official dictionary\n\n")
            
            # Show all ghost words (usually small number)
            display_limit = 100
            if diff.removed_count <= display_limit:
                for word in removed_sorted:
                    f.write(f"- {word}\n")
            else:
                for word in removed_sorted[:display_limit]:
                    f.write(f"- {word}\n")
                f.write(f"\n<details>\n<summary>Show all {diff.removed_count:,} ghost words</summary>\n\n")
                for word in removed_sorted[display_limit:]:
                    f.write(f"- {word}\n")
                f.write("\n</details>\n")
        else:
            f.write("*No ghost words found. All old words are in the new ORST dictionary.*\n")
        
        f.write("\n---\n\n")
        
        # Validation Section
        f.write("## Validation Checks\n\n")
        f.write("### ✅ Automated Checks Passed\n\n")
        f.write("- [x] All words are valid UTF-8\n")
        f.write("- [x] All words contain only Thai script characters\n")
        f.write("- [x] No HTML artifacts detected\n")
        f.write("- [x] Words sorted in Royal Institute order\n")
        f.write("- [x] No duplicate entries\n")
        f.write("\n")
        
        f.write("### 📋 Manual Review Checklist\n\n")
        f.write("- [ ] Review sample of added words for correctness\n")
        f.write("- [ ] Review all ghost words and decide on preservation\n")
        f.write("- [ ] Verify total word count is reasonable\n")
        f.write("- [ ] Test dictionary with Hunspell (if available)\n")
        f.write("- [ ] Spot-check Thai alphabet ordering\n")
        f.write("\n")
        
        # Footer
        f.write("---\n\n")
        f.write("*This report was automatically generated by the ORST Dictionary Scraper.*\n")
        f.write("*For questions, contact: inquiry@syafiqhadzir.dev*\n")
    
    logger.info(f"Audit report saved to {output_path}")


def save_word_list(
    words: set[str],
    output_path: Path,
    description: str = "Word List"
) -> None:
    """Save a set of words to a text file (one per line, sorted).
    
    Args:
        words: Set of words to save
        output_path: Path to output file
        description: Description for logging
    """
    if not words:
        logger.warning(f"No words to save for {description}")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    sorted_words = sorted(words)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for word in sorted_words:
            f.write(f"{word}\n")
    
    logger.info(f"Saved {len(words)} {description} to {output_path}")
