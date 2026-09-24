# 30. Getting Access: Futures and Listed Options — brief and source ledger

## Brief

- **Hook.** The same contract costs one firm 1.38 dollars a side and another 0.35.
- **Sections.** The clearing broker; Membership: buy, lease or stay outside; Incentive and market-maker programmes; Options market-maker appointments; Data licences.
- **Defines.** futures commission merchant, clearing member, exchange membership, member rate, incentive programme, give-up, market-maker appointment.
- **Tutorial.** Break-even volume for leasing a membership.
- **Build.** Futures fee engine.
- **Weekend problem.** Lease or pay? — named result: break-even contracts per month.
- **Facts to verify.** CME fee schedule structure and membership types; CME membership lease/seat prices (public); Eurex MM programmes; Cboe MM appointment costs; CFTC FCM list.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | E-mini S&P 500 exchange fee per side: non-member $1.18, member lease $0.47, member owner $0.35; micro E-mini $0.20 / $0.07 / $0.04; non-members pay $0.02 NFA fee; leasing is a two-step process with a $2,000 application fee for individual CME membership | Optimus Futures, "CME Membership Seat Lease" (a broker's published comparison; SECONDARY) | https://optimusfutures.com/CME-Lease.php | 2026-09-18 | "$1.18 per side, per contract"; "Member lease: $0.47"; "Member owner: $0.35" | hook; dat:m1:getting-access-futures-options:rates; all figures; build tests |
| F2 | FCM: "An entity that solicits or accepts orders to buy or sell futures contracts, options on futures, retail off-exchange forex contracts or swaps, and accepts money or other assets from customers to support such orders"; all registered FCMs must be NFA members | NFA, FCM registration page | https://www.nfa.futures.org/registration-membership/who-has-to-register/fcm.html | 2026-09-18 | quoted | def fcm |
| F3 | CME Group announced transaction fee schedule changes effective 1 October 2026 | CME Group clearing fees page (search excerpt; page not fetchable) | https://www.cmegroup.com/company/clearing-fees.html | 2026-09-18 | "Effective October 1, 2026, CME Group announced a series of transaction fee schedule changes" | dat rates |

## EXCLUDED

- The brief's hook ($1.38 non-member): CME's own schedule could not be fetched (JSON error pages, timeouts); the chapter uses the broker-published $1.18 / $0.47 / $0.35 and says the exchange's schedule is the reference. FLAG: check against the CME Non-Member Fee Finder before publication, particularly after the 1 October 2026 changes.
- Lease prices and seat prices by division (CME publishes them monthly): not fetchable; the $1,500 lease and the $4,000 monthly cost of capital for ownership are stated assumptions.
- Eurex and CME market-maker programme terms, Cboe market-maker permit and appointment fees: described generically.
- Member waivers of market-data fees: stated as true "on some exchanges" without naming one.
- FCMs shedding customers after 2020 and 2022: removed as unverified; replaced by a general statement about stressed periods.
- The CFTC glossary (FCM, give-up) returned 403 to every fetch method tried.
