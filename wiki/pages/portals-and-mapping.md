---
status: current
last_updated: 2026-04-24
last_verified: 2026-04-24
sources:
  - raw/article-digest.md
  - raw/instructions.md
synthesis: Portal-to-profile mapping, search-only sources, and platform-specific notes
---

# Portals and Mapping

Six portals with stored CVs. Two search-only discovery sources.

| Portal | Stored Track | Note |
|--------|-------------|------|
| LinkedIn | B | Headhunting primary |
| Indeed | B | Widest audience; overridden per application |
| Reed | D | Rail/civils/construction agency leads |
| Totaljobs | C | Infrastructure, 21M CV database |
| CWJobs | A | IT/tech niche specialist |
| RailwayPeople | C | Rail domain only |
| Adzuna | None | API, aggregates 100+ UK boards |
| Google Jobs | None | Via SerpAPI, direct company postings |

Full config in portals.yml. Adzuna and SerpAPI require API keys in .env.

## TODO
- [ ] Add Adzuna API key setup instructions
- [ ] Add SerpAPI key setup instructions
- [ ] Document agency vs direct employer flag for Reed (different follow-up approach)
- [ ] Add rail/civils tracked companies list
