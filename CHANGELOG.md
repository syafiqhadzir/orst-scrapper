# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive unit tests for `dictionary_diff`, `hunspell_writer`, `progress_tracker`, and `config` modules
- Dependabot configuration for automated dependency updates
- Makefile with common development commands
- VS Code workspace settings and recommended extensions
- CHANGELOG.md following Keep a Changelog format
- SECURITY.md with vulnerability reporting guidelines
- CI badges in README.md
- Docker HEALTHCHECK instruction
- OCI-compliant Docker labels
- Python 3.12 support in CI matrix

### Changed

- Updated pre-commit hooks to latest versions
- Fixed invalid `trail-separator-lines` hook to `trailing-whitespace`
- Expanded Ruff lint rules with security, naming, and pathlib checks
- Enhanced CI workflow with coverage thresholds and format checking
- Added `[project]` metadata to pyproject.toml for PEP 621 compliance
- Removed redundant `black` dependency (Ruff handles formatting)

### Fixed

- Pre-commit configuration using non-existent hook ID

## [1.0.0] - 2024-12-26

### Initial Release

- Initial release of ORST Dictionary Scraper
- API client with retry logic and rate limiting
- Thai Unicode normalization and validation utilities
- Royal Institute dictionary order sorting
- Progress tracking with resumable operations
- Audit report generation for dictionary diffs
- Hunspell dictionary file writer
- Comprehensive documentation (USAGE.md, ARCHITECTURE.md, DEVELOPMENT.md)
- CI/CD pipeline with GitHub Actions
- CodeQL security scanning
- Docker support with multi-stage build
- Type hints throughout the codebase
- Unit test coverage

[Unreleased]: https://github.com/SyafiqHadzir/orst-scrapper/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/SyafiqHadzir/orst-scrapper/releases/tag/v1.0.0
