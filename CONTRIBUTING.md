# Contributing to ORST Dictionary Scraper

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

### Our Standards

- **Be respectful**: Treat all contributors with respect and courtesy
- **Be collaborative**: Work together to improve the project
- **Be constructive**: Provide helpful feedback and suggestions
- **Be inclusive**: Welcome contributors of all skill levels

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Personal attacks
- Publishing private information

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:

1. **Check existing issues**: Search [GitHub Issues](https://github.com/SyafiqHadzir/orst-scrapper/issues) to avoid duplicates
2. **Verify the bug**: Ensure it's reproducible
3. **Collect information**: Gather error messages, logs, and environment details

**Bug Report Template**:

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Run command X
2. Observe error Y

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: Windows 11 / Ubuntu 22.04 / macOS 13
- Python version: 3.10.5
- Script version: 1.0.0

**Logs**
```
Paste relevant error logs here
```

**Additional Context**
Any other relevant information
```

### Suggesting Features

Feature requests are welcome! Please:

1. **Check existing feature requests**: Avoid duplicates
2. **Provide clear use case**: Explain why this feature is needed
3. **Consider scope**: Ensure it aligns with project goals

**Feature Request Template**:

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why is this feature needed?

**Proposed Implementation**
How could this be implemented? (optional)

**Alternatives Considered**
Other approaches you've considered
```

### Improving Documentation

Documentation improvements are highly valued:

- Fix typos or unclear explanations
- Add examples or use cases
- Improve code comments
- Translate documentation (if applicable)

## Development Process

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/orst-scrapper.git
cd orst-scrapper
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov mypy ruff
```

### 3. Create Feature Branch

```bash
# Create branch from main
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/bug-description
```

### 4. Make Changes

- Write clean, well-documented code
- Add type hints to all functions
- Follow existing code style
- Add tests for new functionality

### 5. Run Tests and Quality Checks

```bash
# Run all tests
pytest tests/ -v

# Check test coverage (should be >90%)
pytest tests/ --cov=scripts --cov-report=term

# Type checking
mypy scripts/

# Linting
ruff check scripts/

# Format code
ruff format scripts/
```

### 6. Commit Changes

See [Commit Guidelines](#commit-guidelines) below.

### 7. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create PR on GitHub
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (not 79)
- **String quotes**: Double quotes preferred
- **Indentation**: 4 spaces (no tabs)

### Type Hints

All functions must have type hints:

```python
def process_word(word: str, normalize: bool = True) -> str:
    """Process a Thai word.
    
    Args:
        word: Thai word to process
        normalize: Whether to apply Unicode normalization
        
    Returns:
        Processed word
    """
    # Implementation
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief one-line description.
    
    Longer description if needed. Explain what the function does,
    not how it does it (that's what code comments are for).
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative
        
    Example:
        >>> function_name("test", 42)
        True
    """
```

### Error Handling

- Use specific exceptions, not bare `except:`
- Provide meaningful error messages
- Log errors appropriately

```python
# Good
try:
    result = api_call()
except requests.RequestException as e:
    logger.error(f"API call failed: {e}")
    raise

# Bad
try:
    result = api_call()
except:
    pass
```

### Logging

Use the `logging` module:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed diagnostic information")
logger.info("General progress information")
logger.warning("Potential issue detected")
logger.error("Error occurred but continuing")
logger.critical("Severe error, cannot continue")
```

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Scope

Module or component affected:
- `api`: API client
- `thai`: Thai utilities
- `scraper`: Main scraper
- `writer`: Dictionary writer
- `diff`: Diff analyzer
- `config`: Configuration
- `tests`: Test suite
- `docs`: Documentation

### Subject

- Use imperative mood: "Add feature" not "Added feature"
- No period at the end
- Maximum 50 characters

### Examples

```
feat(api): add retry logic for timeout errors

Implements exponential backoff for API requests that timeout.
Configurable via MAX_RETRIES in config.py.

Closes #123
```

```
fix(thai): correct Royal Institute sort order for ฤ

The sort order was incorrectly placing ฤ after ฦ.
Updated THAI_SORT_ORDER constant.

Fixes #456
```

```
docs(readme): update installation instructions

Added Python 3.10+ requirement and clarified virtual environment setup.
```

## Pull Request Process

### Before Submitting

1. **Update documentation**: Update README, docstrings, or docs/ as needed
2. **Add tests**: Ensure test coverage for new code
3. **Run quality checks**: Pass all linters, type checks, and tests
4. **Update CHANGELOG**: If applicable
5. **Rebase on main**: Ensure your branch is up to date

```bash
git fetch upstream
git rebase upstream/main
```

### PR Title

Use the same format as commit messages:

```
feat(api): add caching support for API responses
```

### PR Description Template

```markdown
## Description
Clear description of changes

## Motivation
Why is this change needed?

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] All tests passing
- [ ] Type checks passing
- [ ] No linting errors

## Related Issues
Closes #123
```

### Review Process

1. **Automated checks**: CI/CD pipeline must pass
2. **Code review**: At least one maintainer approval required
3. **Discussion**: Address feedback and make requested changes
4. **Approval**: Once approved, maintainer will merge

### After Merge

1. Delete your feature branch
2. Pull latest main
3. Update your fork

```bash
git checkout main
git pull upstream main
git push origin main
```

## Testing Requirements

### Unit Tests

- Write tests for all new functions
- Use descriptive test names
- Test both success and failure cases
- Use `pytest` fixtures for common setup

```python
def test_normalize_thai_text_with_combining_marks():
    """Test normalization of Thai text with combining marks."""
    input_text = "ก\u0E31"  # ก + combining vowel
    expected = "กั"
    assert normalize_thai_text(input_text) == expected

def test_normalize_thai_text_with_invalid_input():
    """Test normalization with invalid input."""
    with pytest.raises(TypeError):
        normalize_thai_text(None)
```

### Integration Tests

For changes affecting the scraping workflow:

```bash
# Run dry-run test
python update_royin_dictionary.py --dry-run --verbose
```

### Test Coverage

Minimum coverage requirements:
- **Overall**: 90%
- **New code**: 100%
- **Critical modules**: 95%

```bash
# Generate coverage report
pytest tests/ --cov=scripts --cov-report=html
```

## Code Review Checklist

Reviewers should verify:

- [ ] Code follows style guidelines
- [ ] Type hints are present and correct
- [ ] Docstrings are complete and accurate
- [ ] Tests are comprehensive
- [ ] No unnecessary complexity
- [ ] Error handling is appropriate
- [ ] Logging is appropriate
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed

## Getting Help

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Browse [GitHub Issues](https://github.com/SyafiqHadzir/orst-scrapper/issues)
- **Contact**: inquiry@syafiqhadzir.dev

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- CHANGELOG for significant contributions
- Special thanks in release notes

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 License.

Thank you for contributing! 🎉
