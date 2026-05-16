# ABS Dashboard

**Does beating the robot umpire win you games?**

A public-facing analytics dashboard tracking MLB's 2026 ABS (Automated Ball-Strike) Challenge
System — challenge success rates, Win Probability Added, and whether teams that win more
ball-strike challenges actually win more games.

Live: [abs-dashboard.pages.dev](https://abs-dashboard.pages.dev) ·
Data: updated daily during the MLB season

---

## Tech stack

| Layer | Tech |
|-------|------|
| Framework | [Astro 4.x](https://astro.build) with TypeScript strict mode |
| Styling | Tailwind CSS v3 |
| Charts | Chart.js v4 |
| Data | Static JSON in `src/data/`, committed by GitHub Actions |
| Pipeline | Python 3.12 (`pybaseball`, `pydantic`, `pandas`) |
| Hosting | Cloudflare Pages (auto-deploy on push to `main`) |
| Package manager | pnpm |

## Local development

```bash
# Clone
git clone https://github.com/leyeoyelami/abs-dashboard
cd abs-dashboard

# Install dependencies
pnpm install

# Start dev server
pnpm dev
# → http://localhost:4321
```

Other commands:

```bash
pnpm build        # production build
pnpm preview      # preview production build locally
pnpm typecheck    # TypeScript type check (no emit)
pnpm lint         # ESLint
pnpm format       # Prettier
```

## Data pipeline

The site reads from static JSON files in `src/data/`. To populate real data:

```bash
cd scripts
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

See [scripts/README.md](scripts/README.md) for full pipeline documentation.

**GitHub Actions** runs the pipeline daily at 11:00 UTC and commits any changed JSON to `main`,
triggering a Cloudflare Pages rebuild.

## Project structure

```
abs-dashboard/
├── .github/workflows/     # CI/CD + daily data refresh
├── scripts/               # Python data pipeline
│   ├── lib/               # Clients, metrics, Pydantic schemas
│   └── tests/             # Unit tests for metric math
├── src/
│   ├── components/        # Reusable Astro components
│   ├── data/              # Static JSON (committed by pipeline)
│   ├── layouts/           # BaseLayout.astro
│   ├── lib/               # TypeScript types + helpers
│   ├── pages/             # Routes (index, teams, players, methodology, about)
│   └── styles/            # global.css
└── public/                # Static assets
```

## Data sources

- **Baseball Savant** (`baseballsavant.mlb.com/abs`) — challenge counts, overturn rates
- **pybaseball / Statcast** — pitch-by-pitch data, WPA
- **MLB Stats API** (`statsapi.mlb.com`) — standings, game results

## Contributing

Bug reports and data corrections are welcome. Open an issue or PR.

For data discrepancies, please include the date, teams, and game ID so we can trace the source.

## License

MIT — see [LICENSE](LICENSE).

Data is sourced from public MLB APIs. Not affiliated with MLB or any team.
