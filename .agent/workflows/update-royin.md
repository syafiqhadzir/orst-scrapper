---
description: Update th_TH-royin.dic from ORST Dictionary
---

# Update Royal Institute Dictionary Workflow

This workflow updates `th_TH-royin.dic` by scraping the official Thai Royal Institute Dictionary (ORST) at https://dictionary.orst.go.th/

## Prerequisites

1. Navigate to the scraper directory and install Python dependencies (see [docs/DEVELOPMENT.md](../../docs/DEVELOPMENT.md) for detailed setup):
```powershell
cd orst-scraper
pip install -r requirements.txt
```

## Workflow Steps

### 1. Dry Run (Recommended First)

Test the scraper and generate reports without modifying the dictionary:

```powershell
cd orst-scraper
python update_royin_dictionary.py --dry-run --verbose
```

This will:
- Scrape the ORST dictionary
- Generate an audit report at `reports/audit_report.md`
- Show what would change without modifying files

### 2. Review Audit Report

```powershell
# Open the audit report (from project root)
code reports/audit_report.md
```

Review:
- Added words (new words from ORST)
- Ghost words (words in old dict but not in ORST)
- Total word count changes

### 3. Run Full Update

Once you've reviewed the audit report and are satisfied:

```powershell
cd orst-scraper
python update_royin_dictionary.py
```

This will:
- Create a timestamped backup of the current dictionary
- Update `th_TH-royin.dic` with new words
- Generate final audit reports

### 4. Verify the Updated Dictionary

```powershell
# From project root
# Check word count
python -c "with open('th_TH-royin.dic', encoding='utf-8') as f: print(f'Word count:', f.readline().strip())"

# Validate format (from orst-scraper directory)
cd orst-scraper
python -c "from scripts.hunspell_writer import HunspellDictionaryWriter; from pathlib import Path; print(HunspellDictionaryWriter.validate_format(Path('../th_TH-royin.dic')))"
cd ..
```

## Advanced Options

### Custom Delay Between Requests

To be more polite to the server (slower):

```powershell
cd orst-scraper
python update_royin_dictionary.py --delay 500
```

### Resume Interrupted Scrape

If scraping is interrupted, it will automatically resume from where it stopped:

```powershell
cd orst-scraper
python update_royin_dictionary.py
```

To start fresh (clear progress):

```powershell
# From project root
Remove-Item data/scraper_progress.json -ErrorAction SilentlyContinue
cd orst-scraper
python update_royin_dictionary.py
```

### Clear Cache

To re-fetch all data from the server:

```powershell
# From project root
Remove-Item data/cache/*.json -ErrorAction SilentlyContinue
cd orst-scraper
python update_royin_dictionary.py
```

## Troubleshooting

### Error: "Module not found"

See [docs/USAGE.md#troubleshooting](../../docs/USAGE.md#troubleshooting) for common issues.

```powershell
# Ensure you're in the orst-scraper directory
cd orst-scraper

# Install dependencies
pip install -r requirements.txt
```

### Error: "Connection timeout"

Increase the delay between requests:

```powershell
cd orst-scraper
python update_royin_dictionary.py --delay 1000
```

### Ghost Words Concerns

If you see ghost words in the audit report:
1. Review `reports/ghost_words.txt` (from project root)
2. Verify these words should be removed
3. Consider preserving them in a separate supplementary dict if needed

## Testing

Run the unit tests:

```powershell
cd orst-scraper
pytest tests/ -v
```

Run with coverage:

```powershell
cd orst-scraper
pytest tests/ --cov=scripts --cov-report=html
```
