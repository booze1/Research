# UK Graduate Market Research — shared brief for all research agents

Goal: collect **verifiable** UK graduate-market statistics (seeded by the ISE "Top 10 stats of 2025"
article) and shape them so they can be charted and heat-mapped across UK regions in an interactive dashboard.
Today is 2026-10-22. Prefer the most recent edition of each dataset (2025 or 2026 releases), and include
earlier years where a trend chart would help (ideally 5+ years).

## Geography: UK ITL1 regions (use these exact names)
North East, North West, Yorkshire and The Humber, East Midlands, West Midlands, East of England,
London, South East, South West, Wales, Scotland, Northern Ireland
National figures use region = "UK" (or "England" etc. when that is the true coverage; say so).

## Network constraints (important)
- WebSearch works. Use it heavily: search with the publisher's domain (e.g. allowed_domains ["hesa.ac.uk"]).
- Direct downloads (curl/WebFetch) to most sites are currently BLOCKED by the egress policy
  (ise.org.uk, hesa.ac.uk, ons.gov.uk, gov.uk, etc. return 403/DNS errors). Try a direct fetch ONCE per host;
  if it fails, don't retry that host. Work from search results instead.
- registry.npmjs.org and pypi.org ARE reachable (npm pack / pip download work).

## Verification rules (non-negotiable)
- Never fill a number from memory. Every figure needs a source URL on the publisher's own site where possible.
- `verification` column values:
  - `direct` = you read the figure from the official page or file itself
  - `search-official` = the figure appears in search results attributed to the official publisher's URL
  - `search-secondary` = only seen via a secondary source (news, a university blog); give that URL
- If sources disagree, record both rows and explain in notes.
- If a stat can't be found, list it under "Gaps" in findings.md. Don't approximate it.

## Output (write ONLY inside your own folder: /home/user/Research/data/<theme>/)
1. `stats.csv` with this exact header:
   stat_id,theme,metric,value,unit,region,period,breakdown_dim,breakdown_value,source_title,publisher,source_url,verification,notes
   - One row per number. `value` is numeric only (no £ or %); `unit` e.g. GBP, percent, count, ratio, pct_change.
   - `breakdown_dim`/`breakdown_value` for non-region splits (sector, subject, sex, year…), else leave empty.
   - Quote any field containing commas.
2. `findings.md`: key takeaways (5–10 bullets with numbers), which stats are mappable by region,
   suggested visualisations (e.g. choropleth of X, slope chart of Y), gaps, and caveats
   (sample sizes, coverage like "England only", ISE = large employers only).
Do not commit to git; the coordinator will.
