# 28. Getting Access: Rates and Credit — brief and source ledger

## Brief

- **Hook.** Before the first swap, the lawyers: a master agreement, a schedule, a credit support annex and an identifier, weeks of work for a trade that takes a second; and before the first cleared repo, a choice between renting a bank's membership and buying one's own.
- **Sections.** Documentation before the first trade; Dealer and client status on the platforms; Inter-dealer access for non-banks; Sponsored repo and clearing membership; Swap clearing brokers.
- **Defines.** ISDA master agreement, Global Master Repurchase Agreement, legal entity identifier, sponsored member, clearing broker (swaps).
- **Uses (defined earlier).** credit support annex, sponsored repo, futures commission merchant, inter-dealer broker, dealer-to-client platform, clearing member.
- **Tutorial.** Cost out three ways to access Treasury repo and swaps for a mid-size fund.
- **Build.** `firm.clearcost`: access-cost model.
- **Weekend problem.** Build or rent — named result: the balance-sheet size at which direct clearing membership beats a clearing broker.
- **Facts to verify.** ISDA 1992/2002 master agreements; GMRA (ICMA) 2011; LEI (GLEIF), cost; FICC sponsored membership rules; BrokerTec/ICAP non-bank access (public); CME/LCH FCM client clearing.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | The ISDA Master Agreement is the standard contract used to govern all OTC derivatives transactions between two parties, often across asset classes; 1992 and 2002 versions; on an event of default or termination event, all outstanding obligations are replaced by a single early termination amount (close-out netting); enforceability may depend on the insolvency law of the insolvent party's jurisdiction; credit departments measure exposure net where netting is enforceable, and capital may be lower | ISDA, "Legal Guidelines for Smart Derivatives Contracts: The ISDA Master Agreement", February 2019 | https://www.isda.org/a/23iME/Legal-Guidelines-for-Smart-Derivatives-Contracts-ISDA-Master-Agreement.pdf | 2026-09-24 | "The ISDA Master Agreement is the standard contract used to govern all over-the-counter (OTC) derivatives transactions entered into between the parties." | §1 |
| F2 | GMRA: standard master agreement for repo developed by ICMA with SIFMA; first published 1992, revised 1995, 2000 and 2011; ICMA publishes legal opinions for the 2011 and 2000 versions in many jurisdictions | ICMA, Global Master Repurchase Agreement page | https://www.icmagroup.org/market-practice-and-regulatory-policy/repo-and-collateral-markets/legal-documentation/global-master-repurchase-agreement-gmra/ | 2026-09-24 | "The first version of the Global Master Repurchase Agreement (GMRA) was published in 1992 and followed by substantially revised versions in 1995, 2000 and 2011." | §1 |
| F3 | LEI: unique 20-character alphanumeric code identifying a legal entity; Level 1 "who is who", Level 2 "who owns whom"; ISO 17442; G20 endorsed the LEI Charter in 2012; GLEIF (Swiss foundation) administers the system; data free to all | GLEIF, "Introducing the Legal Entity Identifier (LEI)" | https://www.gleif.org/en/about-lei/introducing-the-legal-entity-identifier-lei | 2026-09-24 | "a unique 20-character alphanumeric code that enables anyone, anywhere in the world, to access clear, unique identification data about a legal entity" | §1 |
| F4 | SEC order approving SR-FICC-2024-005 (21 Nov 2024): modifies GSD rules to facilitate access for all eligible secondary-market Treasury transactions; renames and describes the Agent Clearing Service as a "done-away" model; removes the Qualified Institutional Buyer requirement for Sponsored Members; Bank Netting Members applying to be Sponsoring Members need equity capital of at least USD 5bn, be Well-Capitalized, with a registered well-capitalized bank holding company | SEC, Release No. 34-101694 | https://www.sec.gov/files/rules/sro/ficc/2024/34-101694.pdf | 2026-09-24 | "Bank Netting Members applying to be a Sponsoring Member must (i) have equity capital of at least $5 billion" | §4 |
| F5 | FICC Sponsored Service: access to centrally cleared Treasury and agency repo; multilateral netting; average daily volume USD 2.3 trillion as of Q2 2026 | DTCC, Sponsored Service page | https://www.dtcc.com/clearing-and-settlement-services/ficc-gov/sponsored-membership | 2026-09-24 | "$2.3 Trillion" (average daily volume, Q2 2026) | §4; dat:m2:getting-access-rates-credit:access |
| F6 | SEF impartial access: a SEF must give any eligible contract participant and independent software vendor impartial access to its markets, with criteria that are impartial, transparent and applied in a fair and non-discriminatory manner, comparable fees for comparable access | 17 CFR 37.202 (eCFR) | https://www.ecfr.gov/current/title-17/chapter-I/part-37/subpart-C/section-37.202 | 2026-09-24 | "Criteria governing such access that are impartial, transparent, and applied in a fair and nondiscriminatory manner" | §2 |
| F7 | Treasury clearing mandate compliance dates: 31 Dec 2026 for eligible cash transactions and 30 Jun 2027 for eligible repo (see ch. 4 ledger F9) | SEC, as recorded in sources/markets-2/04-the-treasury-market.md F9 | https://www.sec.gov/newsroom/speeches-statements/uyeda-remarks-2026-u-s-treasury-market-conference-092226 | 2026-09-23 | see ch. 4 F9 | §4; dat:m2:getting-access-rates-credit:access |

## EXCLUDED

- Costs of LEIs, clearing memberships, sponsorship spreads and FCM fees: no public source; the chapter's cost model is illustrative and says so.
- Non-bank Netting Member capital requirements at FICC: not fetched; not stated.
- Inter-dealer platform access for non-banks (BrokerTec, Fenics): not fetched; described generically.

