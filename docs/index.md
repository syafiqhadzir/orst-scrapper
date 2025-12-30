# ORST Dictionary Scraper

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
[![PyPI version](https://badge.fury.io/py/orst-scrapper.svg)](https://pypi.org/project/orst-scrapper/)
[![CI](https://github.com/SyafiqHadzir/orst-scrapper/actions/workflows/ci.yml/badge.svg)](https://github.com/SyafiqHadzir/orst-scrapper/actions/workflows/ci.yml)

> Production-grade Python tool to synchronize `th_TH-royin.dic` with the official Thai Royal Institute Dictionary (ORST).

## Features

- 🔄 **Automated Scraping**: Extracts all headwords from ORST dictionary (ก to ฮ)
- 🛡️ **Polite Crawler**: Respects server resources with configurable rate limiting
- 💾 **Resumable**: Automatically saves progress and resumes on interruption
- 🔍 **Smart Validation**: Unicode normalization, Thai character validation, duplicate detection
- 📊 **Audit Reports**: Comprehensive diff analysis with added/removed word tracking
- ✅ **Royal Institute Sorting**: Proper Thai alphabetical ordering (not UTF-8 binary)
- 🧪 **Fully Tested**: Comprehensive unit test coverage with type safety
- 🎨 **Rich CLI**: Beautiful command-line interface with progress bars and colored output

## Quick Start

### Installation

**From PyPI** (recommended):

```bash
pip install orst-scrapper
```

**From source**:

```bash
git clone https://github.com/SyafiqHadzir/orst-scrapper.git
cd orst-scrapper
pip install -e .[dev]
```

### Usage

**Dry run** (recommended first time):

```bash
python update_royin_dictionary.py --dry-run
```

**Full update**:

```bash
python update_royin_dictionary.py
```

## Documentation

- [User Guide](USAGE.md) - Comprehensive usage instructions
- [Architecture](ARCHITECTURE.md) - System design and components
- [Development](DEVELOPMENT.md) - Developer setup and contribution

## API Reference

This documentation includes auto-generated API reference from docstrings:

- [Configuration](api/config.md)
- [API Client](api/api_client.md)
- [Thai Utilities](api/thai_utils.md)
- [Scraper Engine](api/orst_scraper.md)
