# Busy Contractors

**Live:** https://busy-contractors.vercel.app

The Minneapolis contractors with the most open jobs right now, from the city's live
building permits, with every job address and the phone and email on their state
contractor licence. One open permit is one job site making debris.

For debris haulers, dumpster companies and jobsite suppliers. The first it was built
for wrote the pitch himself: Barton Led LLC, *"Attention contractors… Debris piled up
on the jobsite? Call us today."*

## What's free, what's paid, and why

| free (on the page, no login) | paid ($5, once) |
|---|---|
| how many contractors, how many open jobs; the map of every job | **each contractor's phone, email and office** (MN DLI licence) |
| the top 10 by open jobs, with their job mix and neighbourhoods | **every open job address**, with the work, stage and start date |
| filter by kind of work | the sort by the job nearest you, by teardowns and new builds, by newest |
| | the spreadsheet |

The free part tells a hauler who is busy. What he acts on is *which jobs are near me
today and who do I call*: the job addresses and the phone, so that is the wall.

## Price

**$5, once.** Set by Aidan on 2026-10-17 as a hypothesis under test. One debris
clean-out is a few hundred dollars and one busy contractor is dozens a year, so a tenth
of one use is well above $5; $5 tests whether price stops a one-truck hauler from buying.
Revise on the funnel: `preview_open`, `checkout_open`, `paid`, `unlock`.

## Data

`DATA_MODEL.md` has the ideal model and the reality check. Sources: City of Minneapolis
building permit register (CCS_Permits, live; building, remodel, roofing and wrecking
permits still open, issued in the last 12 months, one row per job address); Minnesota
Department of Labor and Industry residential contractor licence and contractor
registration exports (public CSVs) for phone and email, joined on normalised company
name. Homeowner-pulled permits, solar and drain-tile jobs are left out. Not filled: who
hauls for them today. Minneapolis only.

## The paywall

Same as unit-turns-mpls and opening-cleans: free slice in `site/`, every row in
`private/bundle/full.json.gz` uploaded as `api/_full/`, read only by `/api/data` (401
without a password, 402 unpaid). Stripe embedded Checkout at $5 mints the password; the
webhook emails it (Mailgun). This project has no Stripe endpoint of its own (the account
is capped at 16): unit-turns-mpls relays its `checkout.session.completed` events here
(`WEBHOOK_FORWARD`), signed with that endpoint's secret. Every session also carries
`metadata.handler_url` for the shared router in `~/Desktop/stripe-router`. `python3 scripts/fulfil.py <session_id>` reprints one;
`--comp "<label>"` issues a free copy. Analytics: Vercel Web Analytics + PostHog.

## Run it

```
python3 pipeline/pull.py && python3 pipeline/build.py
python3 scripts/build_for.py && python3 -m pytest -q tests
VERCEL_TOKEN=... python3 scripts/deploy.py
```

## Licence

MIT. Minnesota public data may be reused and sold (AG op. 852, 1995).
