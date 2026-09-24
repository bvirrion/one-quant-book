# 29. Getting Access: Equity Markets — brief and source ledger

## Brief

- **Hook.** A new firm has a strategy, ten million dollars and no way to send an order.
- **Sections.** Member or client?; Clearing arrangements; Fee schedules and tiers; Liquidity-provider programmes; Data licences; The negotiation.
- **Defines.** clearing broker, executing broker, volume tier, designated market maker, supplemental liquidity provider, non-display fee, give-up (equities).
- **Tutorial.** Net cost per share across three venues under tiered fees.
- **Build.** Fee-schedule engine.
- **Weekend problem.** Reaching the tier — named result: the volume at which the better tier pays for itself.
- **Facts to verify.** NYSE/Nasdaq/Cboe fee schedule structure; NYSE DMM/SLP programme rules; non-display fee policies; FINRA/SEC broker-dealer registration, net capital 15c3-1.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Cboe BZX Equities fee schedule effective 1 Sept 2026, securities at or above $1.00: adding liquidity ($0.0016), removing $0.0030; Add Volume Tier 1 ADAV >= 0.06% of TCV ($0.0020); Tier 2 >= 0.20% ($0.0023); Tier 3 >= 0.25% ($0.0028); Tier 7 >= 1.00% ($0.0031); non-displayed adds from free to ($0.0008); definitions of ADAV, ADV, TCV | Cboe BZX fee schedule | https://www.cboe.com/us/equities/membership/fee_schedule/bzx/ | 2026-09-18 | quoted rates and tier conditions | dat:m1:getting-access-equities:bzx; figs; build tests; all exercises |
| F2 | Net capital: $250,000 carrying; $100,000 dealer (more than ten transactions a year for its own investment account); $50,000 introducing; $5,000 not holding customer funds; market makers $2,500 per security ($1,000 if priced $5 or less) up to $1,000,000; aggregate indebtedness not over 1500% of net capital | 17 CFR 240.15c3-1 (LII) | https://www.law.cornell.edu/cfr/text/17/240.15c3-1 | 2026-09-18 | quoted | dat:m1:getting-access-equities:netcap; exo 4 |
| F3 | NYSE SLPs must maintain a bid or offer at the NBBO in each assigned security at least 10 percent of the trading day (Rule 107B); SLP-Prop and SLMM of the same member organisation not aggregated | NYSE fee filings with the SEC (search excerpt of SR-NYSE filings) | https://www.sec.gov/files/rules/sro/nyse/2023/34-99206.pdf | 2026-09-18 | "at least 10 percent of the trading day" | dat:m1:getting-access-equities:slp; exo 5 |
| F4 | Rule 15c3-5: market-access risk controls under the broker-dealer's direct and exclusive control | chapter 4 ledger F3 | https://www.sec.gov/newsroom/press-releases/2010-210 | 2026-09-18 | see there | section Member or client? |

## EXCLUDED

- The fetched page also listed "retail" rates of ($0.0320)/$0.0300, which look like a parsing artefact of the small fetch model (ten times any plausible rate); not used.
- Inverted-venue and flat-fee rates, clearing at 2 cents and regulatory fees at 1 cent per 100 shares, the $25,000 monthly cost of membership and the 80% pass-through: illustrative, declared so in the captions and the problem.
- How NYSE measures the SLP 10% (average of bid and offer time, by security, monthly): not fetched; exercise 5 presents both readings and tells the reader to read the rule.
- DMM obligations and privileges: defined generically; the NYSE DMM fact sheet was not fetched.
- Non-display fee amounts and categories (Nasdaq, NYSE policies): definition only.
- Total consolidated volume of 12 billion shares a day: an assumption stated in the figure caption and the problem.
