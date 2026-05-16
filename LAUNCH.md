# Pre-Launch Checklist

## Pages & Content
- [ ] All pages load without errors
- [ ] Homepage renders league stats, scatter plot, top teams/players
- [ ] Team leaderboard filters (All/AL/NL) and sorting work
- [ ] Player leaderboard tabs (Batters/Catchers) work
- [ ] Individual team pages show breakdown + player table
- [ ] Individual player pages show headshot + stats
- [ ] Methodology page renders glossary, diagram, limitations
- [ ] About page renders correctly
- [ ] 404 page renders for invalid routes (e.g., `/nonexistent`)

## Performance
- [ ] Lighthouse scores 90+ on all key pages (mobile and desktop)
- [ ] No layout shift visible on page load
- [ ] Fonts load without FOUT/FOIT issues

## SEO & Social
- [ ] Open Graph previews look good (test with opengraph.xyz)
- [ ] Twitter Card previews look good
- [ ] Sitemap accessible at `/sitemap-index.xml`
- [ ] `robots.txt` accessible and correct
- [ ] JSON-LD structured data on homepage, team, and player pages
- [ ] RSS feed at `/feed.xml` returns valid XML

## Security
- [ ] CSP headers don't break anything (check browser console)
- [ ] HSTS header present
- [ ] X-Frame-Options: DENY
- [ ] No mixed content warnings
- [ ] All external links have `rel="noopener noreferrer"` if `target="_blank"`

## Accessibility
- [ ] Skip-to-content link works
- [ ] All images have alt text
- [ ] Tables have proper headers and structure
- [ ] Color contrast meets WCAG AA
- [ ] Keyboard navigation works across all interactive elements

## Dark/Light Mode
- [ ] Dark mode renders correctly (default)
- [ ] Light mode renders correctly
- [ ] Theme persists across page navigations
- [ ] No flash of wrong theme on load

## Mobile
- [ ] Mobile experience tested on actual phone, not just devtools
- [ ] Tables scroll horizontally without breaking layout
- [ ] Navigation hamburger menu works
- [ ] Text is readable without zooming

## Data
- [ ] All data sources cited on methodology page
- [ ] Sample size warnings appear for small samples
- [ ] Data refresh pipeline runs successfully (`python scripts/run.py`)
- [ ] Daily GitHub Actions workflow triggers correctly

## Infrastructure
- [ ] Cloudflare Pages connected to GitHub repo
- [ ] Custom domain configured (apex + www redirect)
- [ ] HTTPS enforced
- [ ] Preview deployments working on PRs
- [ ] Dependabot enabled
- [ ] Branch protection on `main`

## Repository
- [ ] README has clear setup instructions
- [ ] LICENSE file present (MIT)
- [ ] SECURITY.md with disclosure contact
- [ ] No secrets or credentials in committed files
