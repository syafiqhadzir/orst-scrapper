# Usage Guide

Complete guide to using the ORST Dictionary Scraper for updating `th_TH-royin.dic`.

## Table of Contents

- [Quick Start](#quick-start)
- [Command-Line Interface](#command-line-interface)
- [Configuration](#configuration)
- [Advanced Usage](#advanced-usage)
- [Output Files](#output-files)
- [Troubleshooting](#troubleshooting)

## Quick Start

### First-Time Setup

1. **Install Dependencies**:
   ```bash
   cd orst-scraper
   pip install -r requirements.txt
   ```

2. **Run Dry Run** (recommended first time):
   ```bash
   python update_royin_dictionary.py --dry-run
   ```

3. **Review Audit Report**:
   ```bash
   # From project root
   cat reports/audit_report.md
   ```

4. **Run Full Update**:
   ```bash
   python update_royin_dictionary.py
   ```

### Expected Output

```
[12:00:00] INFO - Starting ORST dictionary scraper
[12:00:01] INFO - Loading previous progress...
[12:00:01] INFO - Starting from letter: ก
Scraping: 100%|██████████| 44/44 [02:15<00:00,  3.06s/letter]
[12:02:16] INFO - Scraped 45,231 unique words
[12:02:16] INFO - Generating audit report...
[12:02:17] INFO - Report saved to: reports/audit_report.md
[12:02:17] INFO - Update complete!
```

## Command-Line Interface

### Basic Usage

```bash
python update_royin_dictionary.py [OPTIONS]
```

### Available Options

#### `--dry-run`
Run without modifying the dictionary file. Generates audit report only.

```bash
python update_royin_dictionary.py --dry-run
```

**Use Cases**:
- Testing the scraper for the first time
- Previewing changes before applying
- Verifying API connectivity
- Generating reports for review

---

#### `--delay MILLISECONDS`
Set delay between API requests (default: 200ms).

```bash
# More polite crawling (slower)
python update_royin_dictionary.py --delay 500

# Faster crawling (use cautiously)
python update_royin_dictionary.py --delay 100
```

**Recommendations**:
- **Default (200ms)**: Balanced speed and politeness
- **500-1000ms**: Very polite, use for production updates
- **<100ms**: Not recommended, may trigger rate limiting

---

#### `--no-backup`
Skip creating backup of existing dictionary.

```bash
python update_royin_dictionary.py --no-backup
```

**⚠️ Warning**: Only use if you have external backups. Not recommended for production.

---

#### `--verbose` or `-v`
Enable detailed logging output.

```bash
python update_royin_dictionary.py --verbose
```

**Output Includes**:
- API request/response details
- Unicode normalization steps
- Validation results for each word
- Cache hit/miss statistics
- Detailed error traces

---

#### `--config FILE`
Use custom configuration file (default: `scripts/config.py`).

```bash
python update_royin_dictionary.py --config my_config.py
```

**Use Cases**:
- Testing different configurations
- Development vs. production settings
- A/B testing scraper parameters

---

### Usage Examples

#### Standard Production Update
```bash
# Polite crawling with backup
python update_royin_dictionary.py --delay 500 --verbose
```

#### Quick Development Test
```bash
# Dry run with verbose logging
python update_royin_dictionary.py --dry-run --verbose
```

#### Resume Interrupted Scrape
```bash
# No special flags needed - automatically resumes
python update_royin_dictionary.py
```

## Configuration

### Configuration File: `scripts/config.py`

#### API Settings

```python
# API endpoint configuration
ORST_API_BASE_URL = "https://dictionary.orst.go.th/api"
SEARCH_ENDPOINT = "/search"
TIMEOUT_SECONDS = 30

# Request parameters
DEFAULT_DELAY_MS = 200      # Delay between requests
MAX_RETRIES = 3             # Number of retry attempts
BACKOFF_FACTOR = 2          # Exponential backoff multiplier
```

**Customization**:
- Increase `TIMEOUT_SECONDS` for slow connections
- Adjust `MAX_RETRIES` based on network reliability
- Modify `BACKOFF_FACTOR` for retry strategy

---

#### Processing Settings

```python
# Word processing options
INCLUDE_COMPOUND_WORDS = True    # Include multi-word entries
NORMALIZE_UNICODE = True         # Apply NFC normalization
VALIDATE_THAI_ONLY = True        # Reject non-Thai characters
REMOVE_DUPLICATES = True         # Deduplicate word list
```

**Options Explained**:

| Setting | Effect | Recommendation |
|---------|--------|---------------|
| `INCLUDE_COMPOUND_WORDS` | Include phrases like "ไปมา" | `True` for completeness |
| `NORMALIZE_UNICODE` | Convert to NFC form | Always `True` |
| `VALIDATE_THAI_ONLY` | Reject non-Thai words | `True` for purity |
| `REMOVE_DUPLICATES` | Remove duplicate entries | Always `True` |

---

#### File Paths

```python
# Directory structure
DATA_DIR = Path("../data")
REPORTS_DIR = Path("../reports")
CACHE_DIR = DATA_DIR / "cache"
DICTIONARY_PATH = Path("../th_TH-royin.dic")

# Progress tracking
PROGRESS_FILE = DATA_DIR / "scraper_progress.json"
LOG_FILE = DATA_DIR / "scraper.log"
```

**Path Customization**:
```python
# Example: Use absolute paths
DATA_DIR = Path("/var/lib/orst-scraper/data")
DICTIONARY_PATH = Path("/usr/share/hunspell/th_TH-royin.dic")
```

---

#### Logging Configuration

```python
# Logging settings
LOG_LEVEL = "INFO"           # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
```

**Log Levels**:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General progress and confirmation
- **WARNING**: Potential issues that don't prevent operation
- **ERROR**: Serious problems that prevented specific operations
- **CRITICAL**: System-level failures

## Advanced Usage

### Resumable Operations

The scraper automatically saves progress after each Thai letter. If interrupted, simply run again:

```bash
python update_royin_dictionary.py
# Output: "Resuming from last checkpoint: ฐ"
```

#### View Current Progress

```bash
# From project root
cat data/scraper_progress.json
```

Example output:
```json
{
    "current_letter": "ฐ",
    "completed_letters": ["ก", "ข", "ฃ", "ค", "ฅ", "ฆ", "ง", "จ", "ฉ", "ช"],
    "words_collected": 15423,
    "last_updated": "2025-12-23T12:15:30Z",
    "version": "1.0"
}
```

#### Clear Progress (Start Fresh)

```bash
# PowerShell
Remove-Item data/scraper_progress.json -ErrorAction SilentlyContinue

# Bash
rm -f data/scraper_progress.json
```

---

### Cache Management

#### View Cache Statistics

```bash
# PowerShell
Get-ChildItem data/cache/*.json | Measure-Object -Property Length -Sum

# Bash
du -sh data/cache/
```

#### Clear Entire Cache

```bash
# PowerShell
Remove-Item data/cache/*.json

# Bash
rm -rf data/cache/*
```

#### Selective Cache Clearing

```bash
# Clear cache older than 7 days (PowerShell)
Get-ChildItem data/cache/*.json | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item

# Clear cache older than 7 days (Bash)
find data/cache/ -name "*.json" -mtime +7 -delete
```

---

### Partial Scraping

For testing or debugging, you can scrape specific letter ranges by modifying the code:

```python
# In update_royin_dictionary.py
from scripts.thai_utils import get_thai_consonants

# Scrape only first 5 letters
TEST_LETTERS = get_thai_consonants()[:5]  # ก, ข, ฃ, ค, ฅ

# Pass to scraper
scraper = ORSTScraper(api_client, progress_tracker)
words = scraper.scrape_letters(TEST_LETTERS)
```

---

### Integration with Workflows

Use the provided workflow for guided updates:

```bash
# From any directory in the repository
/update-royin
```

This runs the workflow defined in `.agent/workflows/update-royin.md`.

## Output Files

### Dictionary File: `th_TH-royin.dic`

**Location**: Project root directory  
**Format**: Hunspell dictionary format  
**Encoding**: UTF-8 with BOM

**Structure**:
```
45231
กระทรวง
กราบ
กราม
...
```

Line 1: Word count  
Lines 2+: One word per line, sorted by Thai Royal Institute order

---

### Audit Report: `reports/audit_report.md`

**Generated on**: Every scraping run  
**Purpose**: Document changes between old and new dictionary

**Sections**:
1. **Summary**: Word count statistics
2. **Added Words**: New words from ORST
3. **Ghost Words**: Words removed from dictionary
4. **Analysis**: Categorized breakdown of changes

**Example**:
```markdown
# Dictionary Update Audit Report

Generated: 2025-12-23 12:15:30

## Summary
- **Previous dictionary**: 44,360 words
- **New dictionary**: 45,231 words
- **Net change**: +871 words (+1.96%)

## Detailed Changes
- **Added words**: 1,023
- **Removed words**: 152

## Added Words Preview
กระบวนการ
กระทำ
[truncated...]

See `added_words.txt` for complete list.
```

---

### Added Words List: `reports/added_words.txt`

**Format**: One word per line  
**Sorting**: Thai Royal Institute order  
**Use Case**: Review new words before accepting update

```
กระบวนการ
กระทำ
กระบี่
กระป๋อง
...
```

---

### Ghost Words List: `reports/ghost_words.txt`

**Format**: One word per line  
**Purpose**: Track words removed from ORST  
**Action Required**: Review before accepting update

```
กระเพือม
กระแส
...
```

**Ghost Word Scenarios**:
1. **Archaic words**: Outdated terms removed from official dictionary
2. **Spelling changes**: Word updated to new spelling convention
3. **API gaps**: Temporary data issues (re-scrape to verify)
4. **Compound variations**: Variants consolidated

---

### Backup Files: `th_TH-royin.dic.backup.TIMESTAMP`

**Location**: Project root directory  
**Naming**: `th_TH-royin.dic.backup.20251223_121530`  
**Retention**: Manual cleanup (not auto-deleted)

**Restoration**:
```bash
# PowerShell
Copy-Item th_TH-royin.dic.backup.20251223_121530 th_TH-royin.dic

# Bash
cp th_TH-royin.dic.backup.20251223_121530 th_TH-royin.dic
```

---

### Log Files: `data/scraper.log`

**Format**: Timestamped log entries  
**Rotation**: Manual (not auto-rotated)

**Example entries**:
```
2025-12-23 12:15:30 - api_client - INFO - Request to /search?q=ก
2025-12-23 12:15:31 - api_client - INFO - Cache hit for query: ก
2025-12-23 12:15:31 - orst_scraper - INFO - Found 842 words for letter: ก
2025-12-23 12:15:31 - thai_utils - DEBUG - Normalized: กระทรวง -> กระทรวง
```

## Troubleshooting

### Common Issues

#### Error: "Module not found: scripts"

**Cause**: Running from wrong directory  
**Solution**:
```bash
# Ensure you're in the orst-scraper directory
cd orst-scraper
python update_royin_dictionary.py
```

---

#### Error: "Connection timeout"

**Cause**: Network issues or server overload  
**Solutions**:
1. Increase timeout:
   ```python
   # In scripts/config.py
   TIMEOUT_SECONDS = 60
   ```

2. Increase delay between requests:
   ```bash
   python update_royin_dictionary.py --delay 1000
   ```

3. Check internet connection and firewall settings

---

#### Error: "Invalid JSON response"

**Cause**: API response format changed or corrupted cache  
**Solutions**:
1. Clear cache:
   ```bash
   rm -rf data/cache/*
   ```

2. Check API status at https://dictionary.orst.go.th/

3. Enable verbose logging:
   ```bash
   python update_royin_dictionary.py --verbose
   ```

---

#### Warning: "Ghost words detected"

**Cause**: Words in old dictionary not found in ORST  
**Action**:
1. Review `reports/ghost_words.txt`
2. Verify if words should be removed
3. Check if it's an API data issue by re-scraping:
   ```bash
   rm data/scraper_progress.json
   python update_royin_dictionary.py --dry-run
   ```

---

#### Error: "Permission denied writing dictionary"

**Cause**: Insufficient file system permissions  
**Solutions**:
1. Check file permissions:
   ```bash
   # Linux/macOS
   ls -l th_TH-royin.dic
   
   # Windows PowerShell
   Get-Acl th_TH-royin.dic | Format-List
   ```

2. Run with appropriate permissions or change ownership

---

#### Performance: "Scraping is too slow"

**Causes & Solutions**:

| Issue | Solution |
|-------|----------|
| Network latency | Decrease `--delay` (cautiously) |
| API rate limiting | Increase `--delay` to 500-1000ms |
| Cache disabled | Ensure `data/cache/` directory exists |
| Debug logging enabled | Disable `--verbose` flag |

---

#### Issue: "Duplicate words in dictionary"

**Cause**: Unicode normalization disabled  
**Solution**:
```python
# In scripts/config.py
NORMALIZE_UNICODE = True  # Ensure this is True
REMOVE_DUPLICATES = True  # Ensure this is True
```

Then re-run:
```bash
python update_royin_dictionary.py
```

---

### Getting Help

1. **Check logs**: Review `data/scraper.log` for detailed error messages
2. **Enable verbose mode**: Run with `--verbose` flag
3. **Validate setup**: Run unit tests:
   ```bash
   cd orst-scraper
   pytest tests/ -v
   ```
4. **Report issues**: Create GitHub issue with:
   - Error message
   - Relevant log excerpts
   - Steps to reproduce
   - Environment details (Python version, OS)

---

### Diagnostic Commands

```bash
# Check Python version (requires 3.10+)
python --version

# Verify dependencies installed
pip list | grep -E "requests|tqdm|unicodedata2|pytest"

# Test API connectivity
python -c "import requests; print(requests.get('https://dictionary.orst.go.th/api/search?q=ก', timeout=10).status_code)"

# Validate dictionary format
python -c "from pathlib import Path; from scripts.hunspell_writer import HunspellDictionaryWriter; print(HunspellDictionaryWriter.validate_format(Path('../th_TH-royin.dic')))"

# Check file encoding
file th_TH-royin.dic  # Linux/macOS
```

## Best Practices

### Production Updates

1. **Always run dry-run first**: Preview changes before applying
2. **Review audit reports**: Verify changes make sense
3. **Use conservative delays**: 500-1000ms for production
4. **Keep backups**: Never use `--no-backup` in production
5. **Schedule appropriately**: Run during off-peak hours
6. **Monitor logs**: Check for warnings and errors
7. **Validate output**: Test dictionary in actual spell-checking

### Development Workflow

1. **Use verbose logging**: Get detailed diagnostic information
2. **Clear cache frequently**: Ensure fresh data during development
3. **Test with small samples**: Use partial scraping for quick iteration
4. **Run unit tests**: Verify changes don't break existing functionality
5. **Version control**: Commit dictionary updates with meaningful messages

### Maintenance

1. **Regular updates**: Schedule monthly/quarterly scrapes
2. **Cache cleanup**: Remove old cache files periodically
3. **Log rotation**: Archive old log files to prevent disk usage growth
4. **Backup retention**: Keep last 3-5 backups, delete older ones
5. **Dependency updates**: Keep Python packages up to date

## Quick Reference

### Essential Commands

```bash
# Standard update workflow
python update_royin_dictionary.py --dry-run --verbose
cat reports/audit_report.md
python update_royin_dictionary.py

# Maintenance
rm data/scraper_progress.json    # Clear progress
rm data/cache/*.json              # Clear cache
pytest tests/ -v                   # Run tests

# Validation
python -c "from scripts.hunspell_writer import HunspellDictionaryWriter; from pathlib import Path; print(HunspellDictionaryWriter.validate_format(Path('../th_TH-royin.dic')))"
```

### File Locations

| File | Purpose | Location |
|------|---------|----------|
| Dictionary | Output file | `th_TH-royin.dic` |
| Audit report | Change summary | `reports/audit_report.md` |
| Added words | New words list | `reports/added_words.txt` |
| Ghost words | Removed words | `reports/ghost_words.txt` |
| Progress state | Resume point | `data/scraper_progress.json` |
| Cache files | API responses | `data/cache/*.json` |
| Log file | Execution logs | `data/scraper.log` |
| Backups | Old versions | `th_TH-royin.dic.backup.*` |

For detailed technical information, see [Architecture Documentation](ARCHITECTURE.md).
