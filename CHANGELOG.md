# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-12-29

### Added

- Python 3.13 support with full CI testing
- SonarCloud integration with quality gate badges and code analysis
- PyPI publishing workflow for automated package releases
- Scheduled dictionary update workflow (runs weekly, creates PRs)
- Rich CLI with styled progress bars, panels, and colored output
- Integration tests with HTTP mocking using `responses` library
- `--no-color` CLI flag for disabling colored output
- End-to-end workflow tests for scraper pipeline
- Additional pre-commit hooks: codespell, check-jsonschema, check-toml
- Enhanced Ruff lint rules: pydocstyle, pylint, perflint, refurb, logging

### Changed

- **BREAKING**: Bumped minimum Ruff version to 0.14.0
- **BREAKING**: Bumped minimum mypy version to 1.14.0
- Upgraded all dependencies to bleeding-edge versions:
  - `ruff` 0.8.0 → 0.14.10
  - `mypy` 1.7.0 → 1.14.1
  - `pytest` 8.0.0 → 9.0.0
  - `rich` 13.0.0 → 14.0.0
  - `requests` 2.31.0 → 2.32.5
  - `tqdm` 4.66.0 → 4.67.1
  - `unicodedata2` 15.1.0 → 17.0.0
  - `pre-commit` 3.5.0 → 4.0.0
  - `setuptools` 61.0 → 75.0
- Upgraded Docker base image to Python 3.13-slim
- Upgraded pre-commit ruff hook to v0.14.10
- Refactored CI workflow into separate lint/security/test jobs
- Updated pyproject.toml target-version to py313
- Enhanced mypy configuration with strict mode
- Project status upgraded from Beta to Production/Stable

### Fixed

- Type annotations for `create_thai_sort_key()` function for mypy strict mode
- pytest-bdd compatibility with pytest 9.x

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

[1.1.0]: https://github.com/SyafiqHadzir/orst-scrapper/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/SyafiqHadzir/orst-scrapper/releases/tag/v1.0.0
