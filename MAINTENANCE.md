# Maintenance Guide

## Cost Projection

| Service | Monthly Cost |
|---------|-------------|
| Cloudflare Pages (hosting) | Free |
| Cloudflare Registrar (domain) | ~$10/year ($0.83/mo) |
| GitHub Actions (CI + daily refresh) | Free (2,000 min/month on free tier) |
| UptimeRobot (monitoring) | Free tier |
| **Total** | **~$1/month** |

## Maintenance Burden

Estimated: **1-2 hours/month** during the season, near-zero in the off-season.

### What could break

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Baseball Savant changes HTML structure | Medium | Data stops refreshing | Pipeline failure opens GitHub issue. Fix the regex/parser. |
| MLB Stats API endpoint changes | Low | Standings stop updating | API is versioned (v1). Monitor for deprecation notices. |
| Savant rate-limits our scraper | Low | Temporary data gap | Pipeline has retry logic + 2s delays between requests. |
| npm dependency vulnerability | Medium | CI fails audit | Dependabot opens PRs automatically. Merge or pin. |
| Astro major version release | Low | Build may break | Pin to `^4.x`. Upgrade intentionally when ready. |

### Regular tasks

- **Daily (automated)**: Data pipeline runs at 11:00 UTC via GitHub Actions
- **Weekly**: Review Dependabot PRs, merge if green
- **Monthly**: Check Lighthouse scores haven't regressed. Scan for stale data or broken links.
- **End of season**: Pipeline auto-stops when no new games are played (no data changes = no commits)

## Off-Season Plan

1. Data pipeline continues running but produces no changes (no games = no new data)
2. Add a "Season Complete" banner on the homepage when the World Series ends
3. Keep the site live with final season data as an archive
4. When spring training begins (late February), verify the pipeline picks up new data
5. Reset or archive the previous season's data before Opening Day

To add the seasonal banner, set a `season_complete` flag in `src/data/metadata.json` and conditionally render a banner in `BaseLayout.astro`.

## Multi-Season Support

The data schema already includes a `season` field in `metadata.json`. To support multiple seasons:

1. Store each season's data in `src/data/{season}/` (e.g., `src/data/2026/`)
2. Add a season selector dropdown in the header
3. Update `getStaticPaths()` in team/player pages to generate routes per season
4. Keep the current season as the default, with archived seasons accessible via URL

This is a Tier 3 feature — the schema won't block it, but the UI work is non-trivial.

## Emergency Procedures

### Pipeline failure
1. Check the GitHub Actions run log for the specific error
2. An issue is auto-created — check open issues
3. Common fix: update the Savant parser if HTML structure changed
4. Manual refresh: `python scripts/run.py` locally, then push the updated JSON

### Site down
1. Check Cloudflare Status page
2. Check UptimeRobot for alerts
3. If Cloudflare Pages is down, there's nothing to do — it auto-recovers
4. If the build is broken, revert the last commit and push
