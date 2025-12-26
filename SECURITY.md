# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email the maintainer directly at: [inquiry@syafiqhadzir.dev](mailto:inquiry@syafiqhadzir.dev)
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium/Low: Within 30 days

### Security Measures in Place

This project implements the following security practices:

- **Dependency Scanning**: Automated via `pip-audit` in CI
- **Static Analysis**: CodeQL scanning on every push
- **Secret Detection**: Pre-commit hooks prevent accidental commits
- **Non-root Docker**: Container runs as unprivileged user
- **Rate Limiting**: Polite crawler respects server resources

### Scope

The following are in scope for security reports:

- Code vulnerabilities in the scraper
- Dependency vulnerabilities
- Configuration security issues
- Docker security concerns

The following are **out of scope**:

- Denial of service attacks
- Social engineering
- Physical security

## Security Best Practices for Users

1. **Keep dependencies updated**: Run `pip install --upgrade -r requirements.txt` regularly
2. **Use virtual environments**: Isolate project dependencies
3. **Review audit reports**: Check generated reports before publishing
4. **Verify dictionary sources**: Ensure data integrity after scraping

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities (unless they prefer to remain anonymous).

Thank you for helping keep this project secure!
