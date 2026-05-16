import type { APIRoute } from 'astro';
import type { LeagueSummary, TeamsData } from '@/lib/types';
import leagueData from '@/data/league.json';
import teamsData from '@/data/teams.json';
import metadata from '@/data/metadata.json';

const league = leagueData as unknown as LeagueSummary;
const { teams } = teamsData as unknown as TeamsData;

const site = 'https://challengetheump.com';

function escapeXml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export const GET: APIRoute = () => {
  const topTeams = [...teams]
    .sort((a, b) => (b.challenges.challenge_wpa ?? -Infinity) - (a.challenges.challenge_wpa ?? -Infinity))
    .slice(0, 5);

  const successPct = league.overall_success_rate
    ? Math.round(league.overall_success_rate * 100)
    : '??';

  const topTeamsSummary = topTeams
    .map((t, i) => `${i + 1}. ${t.team_name} (${t.challenges.challenge_wpa?.toFixed(2) ?? '—'})`)
    .join(', ');

  const pubDate = new Date(metadata.last_updated).toUTCString();

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Challenge The Ump — MLB ABS Challenge Analytics</title>
    <description>Daily updates on MLB ABS Challenge System performance, success rates, and team rankings.</description>
    <link>${site}</link>
    <atom:link href="${site}/feed.xml" rel="self" type="application/rss+xml" />
    <language>en-us</language>
    <lastBuildDate>${pubDate}</lastBuildDate>
    <item>
      <title>ABS Dashboard Update — ${successPct}% overturn rate through ${metadata.games_through || 'today'}</title>
      <description>${escapeXml(
        `League-wide: ${league.total_challenges} challenges, ${league.total_overturns} overturns (${successPct}% rate). ` +
        `Top teams by Net RV: ${topTeamsSummary}.`
      )}</description>
      <link>${site}</link>
      <pubDate>${pubDate}</pubDate>
      <guid isPermaLink="false">strikezone-${metadata.games_through || 'latest'}</guid>
    </item>
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
    },
  });
};
