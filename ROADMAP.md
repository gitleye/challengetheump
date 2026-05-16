# Roadmap

Ideas for future development, roughly prioritized by impact vs. effort.

## Tier 1 — High Impact, Low Effort

- **Newsletter signup** — Weekly digest of challenge trends via Buttondown or self-hosted. Embed signup on homepage.
- **Game-by-game challenge log** — Each challenge event with date, inning, count, outcome, and link to MLB Gameday replay.
- **"Challenge of the Day" highlight** — Auto-select the highest-leverage challenge from the previous day's games. Feature on homepage.
- **Season recap mode** — When the season ends, freeze the data pipeline and display a "2026 Season Final" banner. Auto-resume when the next season starts.

## Tier 2 — High Impact, More Effort

- **Historical comparison** — Simulate what 2025 win rates would have looked like with ABS challenges. Compare umpire accuracy year-over-year.
- **Predictive model** — Given a team's remaining schedule and current challenge tendencies, project end-of-season challenge value.
- **Public API** — Expose the JSON data as a documented REST API for other developers to build on. Cloudflare Workers would keep it at the edge.
- **Per-page OG images** — Dynamically generated social images showing each team/player's key stat. Use Satori or pre-render at build time.

## Tier 3 — Ambitious

- **Live in-game updates** — Move from static site to edge functions (Cloudflare Workers). Poll for live challenge events during games. Push updates via WebSocket or SSE.
- **Per-pitch strike zone visualization** — Render the actual pitch location on a strike zone diagram for every challenged pitch.
- **Mobile app** — Native iOS/Android wrapper (or PWA) with push notifications for challenges involving your favorite team.
- **Multi-season archive** — Support browsing historical seasons. Schema already supports `season` field — UI and routing need season selectors.

## Not Planned

- User accounts or personalization (keep it simple, no auth overhead)
- Gambling predictions or betting odds (legal and ethical minefield)
- Ads or monetization (this is a portfolio piece, not a business)
