# Security Policy

## Supported Versions

This project is currently in active development. We provide security updates for the latest version only.

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report vulnerabilities via email to:
- **Email:** mathieu.p@northeastern.edu
- **Subject Line:** [SECURITY] Access Project Vulnerability Report

### What to Include

Please include the following information in your report:

1. **Type of vulnerability** (e.g., SQL injection, cross-site scripting, etc.)
2. **Full paths of source file(s)** related to the vulnerability
3. **Location of the affected source code** (tag/branch/commit or direct URL)
4. **Step-by-step instructions** to reproduce the issue
5. **Proof-of-concept or exploit code** (if possible)
6. **Impact of the issue**, including how an attacker might exploit it

### Response Timeline

- **Initial Response:** Within 48 hours of receiving your report
- **Status Update:** Within 7 days with an assessment and expected timeline
- **Resolution:** We aim to release a fix within 30 days for high-severity issues

### What to Expect

1. We will acknowledge receipt of your vulnerability report
2. We will investigate and confirm the vulnerability
3. We will develop and test a fix
4. We will release a security update
5. We will publicly acknowledge your responsible disclosure (unless you prefer to remain anonymous)

## Security Measures

### Automated Security Scanning

This project uses the following automated security measures:

1. **Dependabot**: Automated dependency updates to address known vulnerabilities
2. **pip-audit**: Regular scanning of Python dependencies for security vulnerabilities
3. **Bandit**: Static code analysis for common security issues in Python code
4. **GitHub Security Advisories**: Monitoring for known vulnerabilities in dependencies

### Security Best Practices

We follow these security best practices:

- Regular dependency updates
- Principle of least privilege for file access
- Input validation for external data sources
- Secure handling of API keys and credentials (via environment variables)
- Regular security scans in CI/CD pipeline

## Vulnerability Disclosure Policy

When we receive a security vulnerability report:

1. We will work with the reporter to understand and verify the issue
2. We will develop a fix and test it thoroughly
3. We will release a security update
4. We will publish a security advisory with:
   - Description of the vulnerability
   - Affected versions
   - Fixed version
   - Workarounds (if any)
   - Credit to the reporter (if desired)

## Security Updates

Security updates will be:

1. Released as soon as possible after verification and fix development
2. Clearly marked in release notes with [SECURITY] tag
3. Announced via GitHub Security Advisories
4. Documented with CVE numbers when applicable

## Dependencies Security

### Python Version

- We require Python 3.10+ which receives security updates
- We will upgrade to newer Python versions as they become stable

### Dependency Management

- All dependencies are tracked in `pyproject.toml`
- We use version pinning for critical dependencies
- Regular dependency audits are performed via automated scanning
- Dependabot provides automated pull requests for security updates

### API Keys and Credentials

- **Never commit API keys, passwords, or credentials** to the repository
- Use `.env` files for local development (excluded via `.gitignore`)
- Use environment variables for production deployments
- Rotate credentials regularly

## Contact

For security concerns, please contact:
- **Project Lead:** Philip Mathieu (mathieu.p@northeastern.edu)

For general questions about this security policy, please open a GitHub issue with the `security` label.

---

**Last Updated:** 2025-11-15
