# ATS company inventories

Slug inventories adapted from [kalil0321/ats-scrapers](https://github.com/kalil0321/ats-scrapers) (`ats-companies/`, MIT).

Used by `tools/harvest_boards.py` and `tools/discover_company_ats.py` to expand
`job_scraper/boards.json` beyond the curated live set. Always probe before merge
(`tools/probe_boards.py`) — inventories include stale/empty boards.

Do not treat inventory presence as proof a company is hiring or sponsors visas.
