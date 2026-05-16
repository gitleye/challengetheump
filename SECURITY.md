# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Email:** leye.oyelami@gmail.com

Please include:
- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact

I will acknowledge your report within 48 hours and aim to provide a fix or mitigation within 7 days for confirmed issues.

## Scope

This project is a static site with no server-side code, user authentication, or database. The primary attack surface is:

- **Supply chain** — compromised npm/pip dependencies
- **Data pipeline** — malicious data from upstream sources (Baseball Savant, MLB Stats API)
- **Client-side** — XSS via injected data rendered on the page

## Security Measures

- Content Security Policy headers via Cloudflare Pages (`public/_headers`)
- Dependabot enabled for npm, pip, and GitHub Actions
- CodeQL scanning on all PRs and weekly
- `npm audit` and `pip-audit` checks in CI
- No user input accepted (static site, no forms or APIs)
- All external data is escaped before rendering

## Supported Versions

Only the latest deployed version is supported. This project does not maintain multiple release branches.
