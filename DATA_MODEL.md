# Data model — written before looking at the data (BUSINESS.md rule 5)

**The buyer:** a debris hauler or jobsite supplier who sells to contractors (Barton Led
LLC: *"Attention contractors… Debris piled up on the jobsite? Call us today"*).
**The question:** which contractors have the most jobs running right now, where are
those jobs, and how do I reach the contractor?

## Ideal model

**Contractor**
| field | answers |
|---|---|
| company name | who to ask for |
| phone, email, office address | how to reach them |
| open jobs (count) | how much debris they generate now (rank) |
| job mix (teardown, new build, remodel, roof/siding/windows) | what kind of debris |
| current hauler / dumpster vendor | who I'd be displacing |

**Job**
| field | answers |
|---|---|
| address, lat/lon | where the pile is; distance from me |
| type of work, description | how much and what kind of debris |
| started (permit issued), stage | is it mid-job (debris) or finishing (final sweep) |
| size | how many loads |

## Reality check (2026-10-17)

| field | source | filled? |
|---|---|---|
| company, open jobs, every job's address, type, description, issued date, stage | Minneapolis building permits (CCS_Permits, live; status Issued) | yes; company names only, homeowners left out |
| phone, email, office address | MN Department of Labor and Industry licence + registration exports (public CSVs), joined on company name; the permit's own applicant address otherwise | yes where the name matches |
| size | permit fee (the city publishes no job value) | proxy only |
| current hauler | no public record | **no** |

**Call:** build. Minneapolis only; St. Paul stopped publishing permits on 2025-06-30.
