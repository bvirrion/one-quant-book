# Book 14 — progress and working conventions (resume here)

One agent writes this book in the Books 14–16 batch (`sources/BATCH_BOOKS_14-16.md`, binding: ownership,
read-only git, build only `one_quant_book_14_networks.tex`, scoped tests, resource caps, Part IV sourced not
measured, maps computed). Budget: **10.5–12 pages all-in per chapter**, chapters of ~450–550 body lines and
~150–190 solution lines; 29 chapters → about 330–350 pages against the outline's ~384 (−9 to −14 %).

## Status

| ch | state |
|---|---|
| Phase A | done 2026-09-28: 29 briefs (`tools/briefs/book14.py`; ledgers `sources/networks/NN-*.md` with a **Data** line added after `make_briefs.py`, which does not write it), `DEFINITIONS.md` 181 terms, checked against the 2,753-definition harvest of Books 1–13 (no exact collision; near-matches listed there); every B1–13 `uses` owner checked (term and chapter). Skeleton 0/0/0 (43 pp). Sync done 2026-09-28 (vendor lock-in removed from ch. 27, public cloud added to ch. 16). |
| 1 | done 2026-09-28: firm.netsim (7 tests + C++20 egress twin on a fixture), nw_wire (6 tests, 1 reference); 4 figures (2 schematics, OPRA published peaks, fan-in simulation), 1 table, 3 listings, 2 dated boxes, 15 ledger rows; body 524 + solutions 119 lines = 12 + 2.5 pp. Searches so far: 9. |
| 2 | done 2026-09-28: firm.cagenet (3 tests), nw_cage (5 tests); 4 figures (timing schematic, device curve, cage schematic, multiplexer contention simulation), 1 table, 2 listings, 1 dated box, 4 ledger rows; body 427 + solutions 117 lines. Searches so far: 12. |
| 3 | done 2026-09-28: firm.nicring (Python + C++20 + Rust on one fixture, 3+1+2 tests), nw_nic model + laptop bench (bench_rx.py -> measured_rx*.csv + .meta; nw_rx_test.cpp small run); 4 figures, 1 table, 3 listings, 10 ledger rows; body 429 + solutions 109. Measured on a loaded laptop: re-measure on a quiet machine in Phase C. |
| 4 | done 2026-09-28: firm.clocksync (Python + C++20 servo twin, 4 tests), nw_clock (4 tests, 1 reference); 4 figures, 2 listings, 1 dated box, 8 ledger rows; body ~400 + solutions 112. Searches so far: 14. |
| 5 | done 2026-09-28: firm.wirecap (pcap/pcapng, trailer, parsing, matching; Python + C++20 reader, 4 tests; fixture read by tcpdump too), firm.wirepath (extends Book 13's path to the wire with firm.latbudget, 3 tests); nw_capture (5 tests, 2 reference); 4 figures, 3 listings, 1 dated box, 5 ledger rows; body 359 + solutions 111. Pages after ch. 5: 100 (about 12.7 per written chapter). Searches so far: 16. |
| 6 | done 2026-09-28: firm.hdlkit (skid, field extractor, CRC-32, comparator; Verilator + Icarus testbenches printing identical event lines; 5 tests incl. random back-pressure), nw_fpga (3 tests); 3 figures, 1 table, 2 SV listings, 6 ledger rows. |
| 7 | done 2026-09-28: firm.hwtrade (hwt_trigger.sv: decode, risk with token bucket and kill, order template; Verilator == Icarus == Python cycle model == C++20 cycle model on a 992-packet simulator fixture; 4 tests + C++ test), nw_hwtrade (4 tests); 3 figures, 1 table, 3 listings, 1 dated box, 3 ledger rows. Pages after ch. 7: 120. Searches so far: 22. |
| 8 | done 2026-09-28: firm.serverspec (candidates as ledger rows, latency-vs-clock model, cabinet fit, firmware audit into firm.tuneaudit Findings; 3 tests), nw_servers (3 tests); 2 figures, 1 table, 1 listing, 2 dated boxes, 9 ledger rows. Pages after ch. 8 (end of Part II): 131. Searches so far: 27. |
| 9 | done 2026-09-28: firm.colobill (fee schedules as dated ledger rows: Nasdaq NY11-4, MIAX Pearl; bill, staleness, break-even, equalisation coil; 2 tests), nw_colo (2 tests); 2 figures, 1 dated box, 2 listings, 7 ledger rows; hook rewritten around RTS 10's cable-length rule and Nasdaq's Equalization Project (sync decision 8). |
| 10 | done 2026-09-28: firm.geomap (Vincenty on WGS-84, Python + C++20 twin on 249 geodesics of Karney's CC0 test set, floors, route factors, projection; 3 tests), data/networks/sites.csv (7 sites, each with ledger rows; Markham flagged approximate), nw_map (6 tests); 4 figures (2 maps from computed coordinates, routes vs floors, route-factor schematic), 2 tables, 3 listings, 1 dated box, 18 ledger rows; body 452 + solutions 138. Pages after ch. 10: 152. Searches so far: 30 (plus direct fetches of known URLs). |
| 11 | done 2026-09-28: firm.venuesites (venue-to-site registry by MIC with dated rows, migration history, nearest-venue queries, join with Book 1's firm.venues; 3 tests); 7 European sites (3 street-level, flagged); nw_europe (5 tests); 4 figures (map, PoP schematic, migration bars, floors from LD4), 2 tables, 3 listings, 1 dated box, 16 ledger rows; body 426 + solutions 136. Pages after ch. 11: 164. Searches so far: about 42. |
| 12 | done 2026-09-28: firm.dissem (two-level sequential unicast after SEBI's 2019 order, multicast, fairness, rank stability, race odds; labelled simulation; 3 tests), 5 Asia-Pacific sites (precision in the name: two city-level, buildings undisclosed); nw_asia (5 tests, 2 reference); 4 figures (map, architecture schematic, rank curve, sorted delays), 2 tables, 2 listings, 2 dated boxes, 12 ledger rows; body 416 + solutions 132. Pages after ch. 12: 176. |
| 13 | done 2026-09-28: firm.fibreroute (spans, latency by component, inversion of a published latency, hollow-core index, dark-against-lit costs; 3 tests), nw_fibre (5 tests); 4 figures (span schematic, sensitivity, costs, component bars), 1 table, 2 listings, 6 ledger rows (equipment times and prices are labelled assumptions); body 395 + solutions 128. Pages after ch. 13: 187. |
| 14 | done 2026-09-28: firm.radiolink (hop geometry, link budget, ITU-R P.838-3 rain coefficients as data, critical rain, great-circle chain, storm crossing with failover to fibre, availability; 3 tests), nw_wireless (5 tests); 4 figures (hop schematic, specific attenuation, critical rain, storm timeline), 2 tables, 2 listings, 1 dated box, 7 ledger rows; body 426 + solutions 118. Pages after ch. 14: 198. |
| 15 | done 2026-09-28: firm.slamodel (circuit catalogue of published prices, published credit tiers, steady-state and simulated availability with common-mode events, monthly credits; 3 tests), nw_buy (5 tests, 2 reference); 4 figures (purchase stack, designs schematic, cost vs downtime, simulated-year percentiles), 2 tables, 2 listings, 2 dated boxes, 4 ledger rows; body ~410 + solutions 119. Pages after ch. 15 (end of Part III): 210. |
| 16 | done 2026-09-28: firm.cloudplan (zone-name resolver on describe-availability-zones fixtures in the documented shape with synthetic values, 1/n naming probability, lognormal-plus-spikes round trips fitted to Hilyard et al.'s published AWS percentiles, dated instance catalogue, monthly cost with cross-zone transfer; 3 tests), nw_cloud (5 tests, 2 reference); 4 figures, 1 table, 2 listings, 2 dated boxes, 9 ledger rows; public cloud defined (sync decision). Pages after ch. 16: 220. |
| 17 | done 2026-09-28: firm.venuefind (longest-prefix matcher on an ip-ranges fixture with documentation addresses, light-time bound and round-trip triangulation, instance lottery with optimal launches, CUSUM move detector wrapping Book 7's firm.decay; 3 tests), nw_find (5 tests, 1 reference); 4 figures, 1 table, 3 listings, 1 dated box, 8 ledger rows. Pages after ch. 17: 232. |
| 18 | done 2026-09-28: firm.privlink (documented paths as dated data, round trips on firm.cloudplan's bodies plus stated hop assumptions, zone-alignment check, endpoint and cross-zone costs; 3 tests), nw_private (4 tests, 2 reference); 4 figures, 1 table, 2 listings, 2 dated boxes, 7 ledger rows. Pages after ch. 18: 243. |
| 19 | done 2026-09-28: firm.routerace (correlated lognormal routes via a Gaussian copula with common random numbers, first arrival, percentile gain, break-even price, duplicate rules, path inflation; 3 tests), 7 AWS hub sites (city-level; N. Virginia placed at Ashburn), nw_race (4 tests, 2 reference); 4 figures, 1 table, 1 listing, 1 dated box, 6 ledger rows. Pages after ch. 19: 252. |
| 20 | done 2026-09-28: firm.cryptofeed (dated venue limits, shard planner, recovery under Book 3's firm.ratelimit governor, water-filling allocator, minimum-delay venue-clock estimator; Book 3's firm.wsbook used for the gap; 3 tests), nw_api (4 tests); 4 figures, 1 table, 3 listings, 1 dated box, 6 ledger rows. Pages after ch. 20 (end of the crypto sources' run): 262. |
| 21 | done 2026-09-28: firm.chainnet (peer graph on geomap cities, gossip as shortest paths with flooding and square-root fan-out, dated Jito engine regions, nearest-engine chooser and deadline check; 3 tests), nw_chain (5 tests, 3 reference); 4 figures (1 schematic), 2 listings, 2 dated boxes, 7 ledger rows. Pages after ch. 21: 271. |
| 22 | done 2026-09-28: firm.portplan (OPRA capacity rows and quoting-port fees as dated data, netsim framing, a busy-minute burst model with two parameters fitted to two published peak ratios and checked against a third, line packing per planning percentile, handler cores, synchronous-port arithmetic; 4 tests), nw_options (5 tests, 2 reference); 4 figures (1 schematic), 1 table, 4 listings, 3 dated boxes, 8 ledger rows. Pages after ch. 22: 282. |
| 23 | done 2026-09-28: firm.gwmodel (parallel against segment gateway races with queues and cable ties, bystander latency, dated Eurex session fees and a cheapest-mix planner, A/B joint loss, per-session drop-copy reconciliation wrapping Book 13's firm.ordergw; 5 tests), nw_futures (3 tests, 1 reference, about 45 s); 2 figures, 3 listings, 2 dated boxes, 8 ledger rows. Trap: a micro sign in a listed Python file stops pdfTeX (Invalid UTF-8 in listings); write us in code. Pages after ch. 23: 294. |
| 24 | done 2026-09-28: firm.fxlinks (dated FX venue sites, three new sites.csv rows ty3 ny6 sg1, staleness and the hold that closes an information-path gap, jittered catch rates, aggregator stale windows, order path; 4 tests), nw_fx (4 tests); 3 figures (1 schematic), 1 table, 2 listings, 2 dated boxes, 5 ledger rows. The brief's hook (EBS engines in London, New York and Tokyo) was out of date: EBS now matches in NY5 and LD4.2 only, Tokyo is a gateway; the hook and problem were rewritten around that and the GFXC's ruling that added last-look delay is contrary to Principle 17. Pages after ch. 24: 303. |
| 25 | done 2026-09-28: firm.rfqlink (lognormal pipelines with a manual share, quote timer, three client rules on Book 11's firm.rfqmm bid model drawn identically and checked equal to firm.rfqmm.simulate, lost-to-speed, value of speed against price; 3 tests), nw_rfq (3 tests, 1 reference); 2 figures, 1 table, 2 listings, 2 dated boxes, 4 ledger rows. Pages after ch. 25: 312. |
| 26 | done 2026-09-28: firm.powerlink (first-come capacity race, gate-closure clock, dated Betfair request weights, polling arithmetic, charged transactions; 2 tests), nw_power (3 tests); 2 figures (1 schematic), 2 listings, 2 dated boxes, 5 ledger rows. Defined term renamed at writing: *data-request charge* became *transaction charge* (DEFINITIONS.md and the brief updated), because the exchange's documentation shows no data request charge any more, only a transaction charge above 5,000 an hour; to report at reconciliation. Pages after ch. 26: 321. |
| 27 | done 2026-09-28: firm.vendormap (dated vendor inventory with ledger sources, stack graph, component and vendor cuts, HHI of spend, bill of materials; 3 tests), nw_vendors (3 tests); 2 figures (1 schematic), 1 listing, 1 dated box, 5 ledger rows; vendor lock-in used with a pointer to Book 16 ch. 20, not defined. Five vendor names added to tools/firm_names.txt under Book 14. Pages after ch. 27: 330. |
| 28 | done 2026-09-28: firm.drplan (sites via geomap, hazard radius, lognormal runbooks, recovery point by replication mode, synchronous-replication penalty, 12-month test check, dated test calendar; 3 tests), nw_dr (3 tests); 1 figure, 1 table, 2 listings, 3 dated boxes, 7 ledger rows; the nine resilience terms defined in four definition blocks. Pages after ch. 28: 341. |
| 29 | done 2026-09-28: firm.connplan, the capstone (dated price rows with sources, latency by access kind from cagenet+wirepath, fibreroute, a published radio figure and privlink, bill of materials, budget with recovery share, source and staleness checks, cheapest fix for a missed cloud target, availability via slamodel, exported cost table for Book 16's techtier with a README; 4 tests), nw_plan (4 tests); 2 figures, 2 tables, 3 listings, 1 dated box, 5 ledger rows. The plan: NYSE Mahwah colocation, CME by radio data and a fibre wavelength, Binance in AWS Tokyo; USD 1,017,289 a year; one unsourced row (the wavelength) flagged by its own check. Pages after ch. 29: 349. |

## Commands (this book only)

```sh
nice -n 19 systemd-run --user --scope -q -p MemoryHigh=2G -p MemoryMax=4G latexmk one_quant_book_14_networks.tex
tools/gates.sh log networks
tools/gates.sh chapter networks/NN-slug ; tools/gates.sh sources networks/NN-slug ; tools/gates.sh firms networks/NN-slug
make test-code CH=networks/NN-slug          # and CH=firm/<component> for my components
tools/figdata.sh networks
OQB_BOOK=14 .venv/bin/python tools/figcrop.py "Figure N.M." <scratchpad>/networks/fig.png   # check the running header
```
Crops: `/tmp/claude-1000/-home-bvirrion-repositories-one-course/ae14faac-4918-4550-a552-734d3b2515f8/scratchpad/networks/`.
Harvest for the defined-once check: `scratchpad/networks/harvest.tsv` / `owners.tsv`; checker `check.py`
(defines against the harvest, `uses` owners, in-book forward references).

## Conventions decided in Phase A

- Teaching modules `code/networks/NN-…/python/nw_*.py`; C++ `nw_*.cpp/.hpp`; HDL modules and files `nw_*`
  in chapters and `hdk_*` (firm.hdlkit) / `hwt_*` (firm.hwtrade) in components, so Verilator's generated
  class names (`Vnw_…`) are unique.
- HDL: SystemVerilog accepted by **both** Verilator 4.038 and Icarus 11 (`iverilog -g2012`): no interfaces
  or classes, no `unique case`, packed structs only where both accept them, `always_ff`/`always_comb`
  checked in both; Verilator driven by `verilator --cc --exe --build -j 1` from pytest into a
  `tmp_path`; Icarus by `iverilog -g2012 -o … && vvp …`. Tests **fail** if a tool is missing
  (`shutil.which` → `pytest.fail`). Golden models in Python; a C++20 cycle model beside the HDL in ch. 7.
- Listings of `.sv`: `\om@lstlang` in `onequant.sty` maps unknown extensions to C++. Plan (append-only, after
  the sync): define a `SystemVerilog` listings language and wrap the dispatch with
  `\let\om@lstlang@base\om@lstlang` + a `\renewcommand` that tests `.sv`/`.v` first and falls back to the
  base — no existing line changed.
- Maps: coordinates only from ledger rows (`data/networks/sites.csv`, each row with its ledger id);
  `firm.geomap` computes WGS-84 geodesics (Vincenty, tested against GeographicLib values), latency floors
  and projections into `figdata/networks/…`; TikZ reads coordinates from CSV (no typed numbers).
- Part IV: no measurement; every simulation is captioned "simulation" with its parameters' sources.
- Laptop measurements (ch. 3, 8 only): `bench_*.py` → `measured_*.csv` + `.meta`, caption names the machine
  (Intel Core Ultra 7 155H, WSL2, no isolated cores), tests assert only machine-independent properties.
- Every chapter directory: fast set < 20 s; full-size reproductions `@pytest.mark.reference`;
  `test_small_runs` unmarked.
- Dated boxes: venue locations, providers, product terms, prices, limits. Named vendors/venues only with a
  ledger row per attribution (firm-name gate).

## Notation proposed for the sync (beyond CONTRIBUTING.md)

| symbol | meaning |
|---|---|
| $c_0$ | speed of light in vacuum, 299 792 458 m/s ($c$ stays the coupon rate) |
| $n_g$ | group index of a medium (fibre about 1.47, air about 1.0003) |
| $d_{\mathrm{geo}}$, $L_{\mathrm{path}}$ | geodesic distance; physical path length |
| $\xi = L_{\mathrm{path}}/d_{\mathrm{geo}}$ | route factor (*local* to Part III) |
| $t_{\mathrm{floor}} = d_{\mathrm{geo}}/c_0$ | one-way latency floor |
| $R_{\mathrm L}$ | line rate in bit/s; $t_{\mathrm{ser}} = 8\,\ell_{\mathrm f}/R_{\mathrm L}$ serialisation delay of a frame of $\ell_{\mathrm f}$ bytes (*local*) |
| $t_1,\dots,t_4$; $\vartheta$; $y_{\mathrm f}$; $\sigma_y(\tau)$ | PTP timestamps; clock offset; fractional frequency offset; Allan deviation (*local* to ch. 4) |
| $f_{\mathrm{clk}}$, $T_{\mathrm{clk}}$ | clock frequency and period of a hardware design (ch. 6–7) |
| $\gamma_{\mathrm{rain}} = k_{\mathrm{ITU}} R_{\mathrm{rain}}^{\alpha_{\mathrm{ITU}}}$ | specific rain attenuation, dB/km (ITU-R P.838; *local* to ch. 14); $r_F$ first Fresnel radius; $k_e$ effective-earth-radius factor |
| $\mathcal A$, MTBF, MTTR, RTO, RPO | availability; upright abbreviations (ch. 15, 28) |
| units | `\qty{}{\giga\bit\per\second}`, `\qty{}{\nano\second}`, `\qty{}{\kilo\meter}`, `\qty{}{\decibel}`, `\qty{}{\kilo\watt}`, `\qty{}{\mega\hertz}`; ppm written with `\num{}` and ``ppm'' (no new unit unless needed) |

## Running project (all new; checked against the 378 existing `code/firm/` directories on 2026-09-28)

| ch | component | languages | builds on |
|---|---|---|---|
| 1 | netsim | Python + C++20 queue kernel | exchsim (recorded feed) |
| 2 | cagenet | Python | netsim |
| 3 | nicring | C++20, Rust, Python model | ring (layout ideas only), arena |
| 4 | clocksync | Python + C++20 servo | netsim |
| 5 | wirecap | Python + C++20 reader | exchsim, wirecodec (encapsulation) |
| 5 | wirepath | Python | ticktotrade (measured CSV, read-only), latbudget, cagenet, netsim |
| 6 | hdlkit | SystemVerilog, C++20 testbench, Python | — |
| 7 | hwtrade | SystemVerilog, C++20 cycle model, Python golden | hdlkit, exchsim fixtures, wirecodec/feed layouts, latbudget (race model) |
| 8 | serverspec | Python | tuneaudit (wrapped), ubench |
| 9 | colobill | Python | feesched (pattern only) |
| 10 | geomap | Python + C++20 geodesic | — |
| 11 | venuesites | Python | geomap, venues (wrapped by MIC) |
| 12 | dissem | Python | geomap |
| 13 | fibreroute | Python | geomap |
| 14 | radiolink | Python | geomap, fibreroute |
| 15 | slamodel | Python | — |
| 16 | cloudplan | Python | — |
| 17 | venuefind | Python | geomap, cloudplan, decay (CUSUM, wrapped) |
| 18 | privlink | Python | cloudplan |
| 19 | routerace | Python | geomap |
| 20 | cryptofeed | Python | wsclient, wsbook, ratelimit (all wrapped) |
| 21 | chainnet | Python | geomap |
| 22 | portplan | Python | netsim |
| 23 | gwmodel | Python | ordergw (drop-copy reconciler, wrapped) |
| 24 | fxlinks | Python | geomap |
| 25 | rfqlink | Python | rfqmm (wrapped), latbudget |
| 26 | powerlink | Python | — |
| 27 | vendormap | Python | — |
| 28 | drplan | Python | geomap, slamodel |
| 29 | connplan | Python | all of the above |

## Source plan and leads (from Phase A's six checking searches; not yet ledger rows)

- Euronext core data centre Basildon → Aruba Bergamo, completed 6 June 2022, press release 15 June 2022:
  euronext.com/en/about/media/euronext-press-releases/successful-completion-migration-euronexts-core-data-centre
  (and the PDF PR_DataCentre_migration_to_Bergamo.pdf). Ch. 11 hook.
- NSE colocation: SAT January 2023 (disgorgement set aside, Rs 100 crore deposit); SEBI accepted NSE's
  settlement (~Rs 1,492 crore, July 2026); Supreme Court allowed it 18 September 2026 (Business Standard,
  BusinessToday). Find SEBI's own orders/press releases for the ledger. Ch. 12 hook.
- Jito block-engine regional endpoints: docs.jito.wtf (lowlatencytxnsend) and jito-labs.gitbook.io
  "Mainnet Addresses". Ch. 21.
- Crypto venues in AWS Tokyo: AWS blog "Ultra-low-latency cross-Region crypto trading with Avelacom and
  AWS"; CoinDesk 2026-03-30 (Glassnode on Hyperliquid validators in ap-northeast-1); BitMEX Dublin → Tokyo
  (2025) needs a primary source. Secondary blogs (longcipher, arbitron, medium) are NOT sources. Ch. 17.
- CSRC Securities Programme Trading Rules, effective 9 Oct 2024; SSE/SZSE implementation rules released
  3 Apr 2025, effective 7 Jul 2025 (law-firm alerts: Han Kun, AIMA) — fetch the CSRC/SSE text. Ch. 12.
- Equal-length cross-connects: the first search did not find an SEC text saying so; NYSE colocation
  filings (e.g., SR-NYSE-2012 34-67262, SR-NYSE-2016 34-78556, SR-NYSE-2023-27 34-97998) define cross
  connects and the meet-me room. If no primary text states equal lengths, the ch. 9 hook is rewritten
  around a sourced fairness rule (RTS 10) and "latency equalisation" is stated generically.
- Known unfetchable by script: cmegroup.com (use the CME client-systems wiki on atlassian.net), sec.gov PDFs
  need `curl -A "<name> <email>"`, regulator PDFs via WebFetch's saved binary + `pdftotext`.

Search budget: about **380** (source-heavy chapters: 9–12 and 15 venue sites and products, 16–21 cloud and
crypto documentation, 22–28 connectivity documents and rules; chapters 1–8 and 13–14 are mostly standards,
papers and datasheets, fetched directly). Prefer direct fetches of known primary URLs.

## Things to report / watch

- Book 15's figdata/platforms/25-databases-and-sql/measured_queries.csv failed test_code.sh's chart-CSV column check (5-6 fields against a 4-field header) on 2026-09-28 during Book 14's ch. 28 cycle; every per-chapter make test-code turns RED while it lasts, whatever the chapter.

- `tools/test_code.sh` chart-CSV check does not flag a `%` inside a field: pgfplots reads it as a comment and the build fails with an unbalanced-columns error (hit in ch. 13, `with DCF (20%)`).

- `tools/make_briefs.py` does not write a chapter's `data` field into its ledger (Book 13 added it by hand;
  so did this book, with a one-off script).
- CI (`.github/workflows/ci.yml`) matrix has no `networks` slug, and installs neither `verilator` nor
  `iverilog`: the ch. 6–7 and `firm/hdlkit`, `firm/hwtrade` tests fail on CI until
  `sudo apt-get install -y verilator iverilog` is added to the code job (Ubuntu 24.04 ships Verilator 5.x
  and Icarus 12: HDL is written for both versions).
- `burn-in test` (ch. 8) sits next to Book 4's `burn-in`: watch the linker in Phase C.

## Calibration log

**Checkpoint at ch. 10 (2026-09-28).** Chapters 1-10 occupy body pages 2-95 (three part pages included): 9.1 body pages per
chapter, plus about 2.5 pages of solutions, so about 11.6 pages all-in per written chapter. The PDF is 152 pages with
chapters 11-29 still placeholders (about 1.2 pages each with their solution stubs). Projection: 152 + 19 x (11.6 - 1.2) =
**about 350 pages**, against the outline's ~384: **-9%**, inside the 15% tolerance, so no depth restoration is required.
Chapters 5-9 ran short (311-360 body lines); chapter 10 is back at 452, and chapters 11-29 aim at 450-550. Web searches so
far: 30 (the budget is about 380).


**Checkpoint at ch. 20 (2026-09-28).** Chapters 1-20 occupy body pages 2-189 (four part pages included): 9.4 body pages per
chapter; solutions run about 2.6 pages each, so about 12.0 pages all-in per written chapter. The PDF is 262 pages with
chapters 21-29 still placeholders (about 1.1 pages each). Projection: 262 + 9 x (12.0 - 1.1) = **about 360 pages**
against the outline's ~384: **-6%**, inside the 15% tolerance; no depth restoration needed. Part IV chapters ran 318-383
body lines, compensated by denser figures and tables. Web searches so far: 64 (plus direct fetches of known documents
and price lists); budget about 380.

**Final (2026-09-28, end of Phase C).** 349 pages against the outline's ~384 (**-9%**), 29 chapters. Chapters 21-29 averaged
9.7 pages all-in each (262 to 349), shorter than 1-20 (12.0): Part V's chapters are documentation-heavy and model-light,
295-344 body lines. Web searches: about 95 in all (64 by ch. 20), plus some 40 direct fetches of known documents, price
lists and API endpoints.

**Phase C.** Term links: 685 (223 linkable terms; one wrong-sense link removed by rewording: *critical path* in
ch. 27's vendor sense became "trading path"). `tools/gates.sh book networks` GREEN (3,336 definitions over 16 books, none
twice; problem numbering OK; links match the config; log 0/0/0). `make test-code CH=networks`: 29 chapter directories
green (122 tests), 66 listing ranges, C++ test in ch. 3; RED only through Book 15's CSV (Things to report). 30 components
green (102 tests; 6 C++20 builds, 1 Rust crate, Verilator and Icarus builds in hdlkit and hwtrade). `tools/figdata.sh
networks` reproduced every chart CSV and connplan's cost table with no diff (hash comparison; figdata is untracked). All 96
figures cropped; ch. 21-29 checked one by one while writing, ch. 1-20 sampled. Ledger access dates 2026-09-24 to 09-28.
Ch. 3's bench re-run twice at load 0.8-0.9 on 22 threads: medians close (blocking 12.8-13.2 us against 16.2 published; busy
polling 1.2-1.3 us against 1.5), busy polling's 99th percentile 11.6 us in one run and 3.03 ms in the other: the tail is
WSL2 preemption, run to run; the published table was kept (it is one draw, and the text says why the tail is there).

**Traps met in ch. 21-29.**
- A micro sign in a listed Python file stops pdfTeX (Invalid UTF-8 in listings): write "us" in code.
- `point meta=explicit symbolic` with `meta expr={round(...)}` prints pgf's internal fixed-point ("1Y8.1e1]"): use
  `nodes near coords={\pgfmathprintnumber[fixed,fixed zerofill,precision=1]{\pgfplotspointmeta}}`.
- pgfplots draws `\draw` commands after the plots, over node labels: move labels inside the bars (anchor=north).
- Python's round of an exact .x5 float (140.55 to 140.5) differs from a hand rounding: print what the tests compute.
- Briefs age: EBS no longer matches in Tokyo (NY5 and LD4.2 only), Betfair no longer charges for data requests. Rewrite
  hooks from the sources read, not from the brief (ch. 24's hook and ch. 26's defined term changed).
- Source access: cmegroup.com times out, but CME's client wiki answers through Confluence's REST API
  (`/wiki/rest/api/content/search?cql=...`, `/content/<id>?expand=body.view`); the Federal Register serves full text at
  `/documents/full_text/text/...`; EUR-Lex refuses, legislation.gov.uk serves the same RTS articles; AWS prices by region
  come gzipped from `b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/...`.

**Figures ch. 1–20: 72 checked, 22 fixed** (each cropped at 130 dpi and read one by one, running header, overlaps, field
correctness and caption checked; 2026-09-28, after the coordinator's request):
- Content: 14.1 the earth-bulge arrow spanned the clearance above the ground; it now runs from the chord between the tower
  feet to the ground at mid-hop. 18.2 the path chained the endpoint's two interfaces; it now goes from the interface in az2
  through the load balancer to the gateways in az1 (caption says so). 14.2's text claimed two orders of magnitude between
  6 and 80 GHz in light rain; it is a factor of about 740 at 2.5 mm/h (test added).
- Overlaps: 11.1 FR2–Bergamo label sat on the Zurich dot and the Frankfurt name left the frame; 12.1 link labels sat on the
  lines and the Hong Kong and Sydney names collided or left the frame; 13.3 legend hid the lit-wavelength line; 20.3 the top
  bar was clipped by the frame.
- Log axes not labelled as such: 15.3, 15.4, 16.3, 17.2, 18.3, 20.2.
- Thousands printed with commas instead of thin spaces: 2.2, 8.1, 10.2, 10.3, 11.1, 12.1, 16.4, 17.1, 18.4, 19.2, 19.3,
  20.2, 20.3, and the map link labels of 10.2 and 12.1 (fig_map.py, fig_asia.py now write `\thinspace`).
Trap: pgfplots prints automatic tick labels with a comma thousands separator; set `/pgf/number format/1000 sep={\,}` on
every axis whose ticks can pass 999 (a PDF text scan for `^[0-9]{1,3},[0-9]{3}$` finds the ones missed).
After the fixes: log 0/0/0, `tools/gates.sh book networks` GREEN, `tools/figdata.sh networks` reproduces with no diff,
ch. 10–12 and 14 tests green.
