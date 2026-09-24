# 27. Getting Access: FX — brief and source ledger

## Brief

- **Hook.** After the Swiss franc shock of January 2015, banks' FX prime brokers kept their largest clients and shed smaller hedge funds; a new fund that wants to trade a billion dollars a day must first find someone who will stand behind its trades, and learn the limits that will stop them.
- **Sections.** Prime-broker credit and give-up lines; Limits: net open position and settlement; Becoming a liquidity provider on venues and single-dealer platforms; Brokerage, disclosures and reviews.
- **Defines.** give-up line, net open position limit, settlement limit, prime-of-prime, designation notice, liquidity-provider review.
- **Uses (defined earlier).** FX prime brokerage, give-up, last look, reject rate, settlement risk.
- **Tutorial.** Implement a pre-trade check that enforces NOP and settlement limits per prime broker.
- **Build.** `firm.pblimits`: pre-trade credit-limit gate (C++20, Rust; Python reader).
- **Weekend problem.** Three prime brokers — named result: the allocation of flow that keeps every limit and minimises cost.
- **Facts to verify.** FX PB market structure after 2015 SNB (public); PB fee ranges (EXCLUDED unless public); venue LP onboarding requirements (EBS/LSEG rulebooks); GFXC disclosure cover sheets.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Master FX Give-Up Agreement (FXC with BBA, Canadian FX Committee, Japanese Bankers Association; published 2005): a Prime Broker authorises Designated Parties, by a Notice, to trade FX with a Dealer on its behalf, limited to types, maximum tenors, currencies and offices in the Notice; the authority is limited to a Net Daily Settlement Amount not exceeding the Settlement Limit and a Net Open Position not exceeding the NOP Limit in the Notice; PB not liable for a trade that causes a limit to be exceeded or further exceeded without its consent; NOP = aggregate of net dollar values by currency (methodology in the Schedule); Net Daily Settlement Amount = sum of dollar values of currencies with a net amount owed to the PB for a settlement date | Foreign Exchange Committee, Master FX Give-Up Agreement (FMLG documentation page) | https://www.newyorkfed.org/medialibrary/microsites/fxc/files/masterfxgiveupagreement.pdf | 2026-09-24 | "expressly limited to a Net Daily Settlement Amount not to exceed the Settlement Limit and a Net Open Position not to exceed the Net Open Position Limit, as set forth in the applicable Notice" | §1; §2; build; tutorial |
| F2 | FMLG/FXC description: in give-up relationships a party designated by a prime broker executes FX with a dealer, and the trade is given up to the prime broker | FMLG, FX give-up documentation page | https://www.newyorkfed.org/fmlg/documentation/giveup.html | 2026-09-24 | "a party designated by a prime broker executes transactions with a dealer that are 'given up' to the prime broker" | §1 |
| F3 | FXC/FMLG market practice (8 May 2013): standard Form of Prime Broker Notice to Executing Dealer under the ISDA Derivatives/FX PB Business Conduct Allocation Protocol; intermediated FX PB arrangements (29 July 2014) with certifications from FX intermediaries | FXC and FMLG memos | https://www.newyorkfed.org/medialibrary/microsites/FMLG/files/docs/PB%20Notice%20to%20ED%20Market%20Practice.pdf | 2026-09-24 | "recommend the attached Form of Prime Broker Notice to Executing Dealer as a market practice" | §1 |
| F4 | BIS (Moore, Schrimpf, Sushko, Dec 2016): FX turnover via prime brokers fell 22% from 2013 (close to 30% in spot); after the January 2015 Swiss franc shock prime brokers focused on large-volume clients (large PTFs) and shed retail aggregators, smaller hedge funds and some HFT firms; raised capital requirements, tightened admission, raised fees; prime-of-prime: prime-brokered by a non-dealer bank which is itself prime-brokered by an FX dealing bank | BIS Quarterly Review, December 2016, "Downsized FX markets: causes and implications" | https://www.bis.org/publ/qtrpdf/r_qt1612e.htm | 2026-09-24 | "whereby they are prime-brokered by a non-dealer bank, which is itself prime-brokered by an FX dealing bank" | hook; §1 |
| F5 | GFXC (18 Aug 2021) released a last-look guidance paper and standardised Disclosure Cover Sheets for liquidity providers and for FX e-trading platforms; FX Global Code last updated December 2024 with a December 2024 LP cover sheet | GFXC press release; GFXC Disclosure Cover Sheets page | https://www.globalfxc.org/press/p210818.htm | 2026-09-24 | "Liquidity providers adhering to these principles and providing transparency about their practices should help to give their clients greater clarity about the process." | §4; dat:m2:getting-access-fx:disclosure |
| F6 | A completed LP Disclosure Cover Sheet (BofA) covers: capacity (Principle 8), sharing of client interaction data, pre-hedging (Principle 11), last look (Principle 17: whether used, symmetry, window length, trading during the window), and an index of disclosures on aggregation, discretion, time-stamping, stop-loss orders, partial fills, reference prices, mark-up, and internal sharing of confidential information (Principle 19) | BofA, FX Global Code Liquidity Provider Disclosure Cover Sheet | https://business.bofa.com/content/dam/flagship/pdf/FX_Global_Code_liquidity_provider_disclosure_cover_sheet.pdf | 2026-09-24 | "Liquidity Provider's Last Look window maximum and minimum length (in m/s)" | §4 |

## EXCLUDED

- FX prime brokerage fees and typical limit sizes: no public source; the chapter's fees and limits are illustrative.
- Venue liquidity-provider onboarding requirements (EBS, LSEG FX rulebooks): not fetched; described generically as a review, without venue-specific rules.
- NOP methodology: the Agreement leaves it to the Schedule; the chapter uses half the sum of absolute net dollar positions (the sum of the longs) and says so.

