# Challenge The Ump

**Does beating the robot umpire win you games?**

A public analytics dashboard tracking MLB's 2026 ABS (Automated Ball-Strike) Challenge System — challenge success rates, net run value, and whether teams that challenge more actually win more.

Live: [challengetheump.com](https://challengetheump.com) | Data: updated daily during the MLB season

![Build](https://github.com/gitleye/challengetheump/actions/workflows/deploy.yml/badge.svg)
![Data Refresh](https://github.com/gitleye/challengetheump/actions/workflows/daily-data-refresh.yml/badge.svg)

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Framework | [Astro 4.x](https://astro.build) — static site generation, TypeScript strict mode |
| Styling | Tailwind CSS v3 with CSS custom properties (dark/light theme) |
| Charts | Chart.js v4 (vanilla, lazy-loaded via IntersectionObserver) |
| Fonts | Space Grotesk (display), Inter (body), JetBrains Mono (data) |
| Data | Static JSON in `src/data/`, committed by GitHub Actions |
| Pipeline | Python 3.12 (requests, pydantic, pandas, structlog) |
| Hosting | Cloudflare Pages (auto-deploy on push to `main`) |
| Package manager | pnpm |

## Local Development

```bash
# Clone
git clone https://github.com/gitleye/challengetheump
cd challengetheump

# Install dependencies
pnpm install

# Start dev server
pnpm dev
# -> http://localhost:4321
```

Other commands:

```bash
pnpm build        # production build -> dist/
pnpm preview      # preview production build locally
pnpm typecheck    # TypeScript type check (no emit)
pnpm lint         # ESLint
pnpm format       # Prettier
```

## Data Pipeline

The site reads from static JSON files in `src/data/`. To populate or refresh data:

```bash
cd scripts
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

See [scripts/README.md](scripts/README.md) for full pipeline documentation.

**GitHub Actions** runs the pipeline daily at 11:00 UTC and commits changed JSON to `main`, triggering a Cloudflare Pages rebuild. If the pipeline fails, it automatically opens a GitHub issue.

## Project Structure

```
challengetheump/
├── .github/
│   ├── dependabot.yml           # Dependency update automation
│   └── workflows/
│       ├── daily-data-refresh.yml  # Cron: fetch data, commit JSON
│       ├── data-pr-check.yml       # PR: validate pipeline without commit
│       ├── deploy.yml              # PR/push: typecheck, lint, build
│       ├── codeql.yml              # PR/weekly: security scanning
│       ├── audit.yml               # PR/weekly: npm + pip vulnerability audit
│       └── lighthouse-ci.yml       # PR: performance regression checks
├── scripts/                     # Python data pipeline
│   ├── lib/                     # Savant client, metrics, Pydantic schemas
│   └── tests/                   # Unit tests for metric math
├── src/
│   ├── components/              # Reusable Astro components (ui/, layout/, players/, charts/, hero/)
│   ├── data/                    # Static JSON (committed by pipeline)
│   ├── layouts/                 # BaseLayout.astro
│   ├── lib/                     # TypeScript types + helpers
│   ├── pages/                   # Routes (index, teams, players, methodology, about, 404)
│   └── styles/                  # global.css (design tokens, data-table, utilities)
├── public/
│   ├── _headers                 # Cloudflare Pages security headers (CSP, HSTS, etc.)
│   ├── _redirects               # www -> apex redirect
│   ├── robots.txt               # Search engine directives
│   └── favicon.svg
├── LAUNCH.md                    # Pre-launch checklist
├── SECURITY.md                  # Vulnerability disclosure policy
└── LICENSE                      # MIT
```

## Environment Variables

No environment variables are required for v1. The site is fully static.

If needed in the future, Cloudflare Pages environment variables can be configured at:
**Cloudflare Dashboard > Pages > challengetheump > Settings > Environment variables**

The pipeline uses no secrets — all data sources are public APIs.

## Data Sources

- **Baseball Savant** (`baseballsavant.mlb.com/abs`) — ABS challenge counts, overturn rates, net run value
- **MLB Stats API** (`statsapi.mlb.com`) — standings, win/loss records

## Security

- **CSP headers** via `public/_headers` — restricts script/style/image sources
- **HSTS** with preload — enforces HTTPS
- **Dependabot** — automated dependency updates for npm, pip, and GitHub Actions
- **CodeQL** — static analysis for JS/TS on every PR
- **Dependency audits** — `pnpm audit` + `pip-audit` in CI

See [SECURITY.md](SECURITY.md) for the vulnerability disclosure policy.

## Observability

- **Uptime**: Set up via UptimeRobot or BetterStack free tier (monitor `/` and `/feed.xml`)
- **Build failures**: Daily data refresh creates a GitHub issue on failure
- **Performance**: Lighthouse CI runs on every PR, fails below 90 for accessibility/best-practices/SEO
- **Error tracking**: Not needed in v1 (static site). If interactive features are added later, integrate Sentry free tier
- **Analytics**: Cloudflare Pages Web Analytics (privacy-friendly, no cookies) — enable in the Cloudflare dashboard

## Contributing

Bug reports and data corrections are welcome. Open an issue or PR.

For data discrepancies, include the date, teams, and game ID so we can trace the source.

## License

MIT — see [LICENSE](LICENSE).

Data is sourced from public MLB APIs. Not affiliated with MLB or any team.
