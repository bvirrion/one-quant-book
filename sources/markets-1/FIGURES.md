# Book 1 — per-figure inspection log

Each figure is rendered on its own page (~100–130 dpi) and read for overlaps
and for correctness in the field. `clean` = re-rendered page has no defect.

| ch | figure | defects found | status |
|---|---|---|---|
| 1 | break-even profit line | label sat on the −20 gridline → moved | clean |
| 1 | map of one trade (TikZ) | "buy order"/"ask quote" labels touched boxes → shortened, nodes spread | clean |
| 1 | who-earned-what bars | none | clean |
| 1 | daily net histogram | `ybar interval` drew bins shifted by two bins (peak at 5–10 instead of 15–20) → switched to `ybar` on bin centres | clean |
| 2 | markets division (TikZ) | Sales→Structuring arrow crossed Sales-trading→Trading → removed | clean |
| 2 | discount vs block size | legend sat on the σ=3% curve → legend moved below the axis | clean |
| 2 | division revenue bars | none | clean |
| 2 | risk-bid P&L histogram | none (5% of mass left of the dashed zero line, as it should be) | clean |
| 3 | saver-to-market chain (TikZ) | 6 pt overfull; "mandate"/"orders" labels touched boxes → figure narrowed, labels raised above box height | clean |
| 3 | years to establish skill (log axis) | none | clean |
| 3 | fee vs volatility | none | clean |
| 3 | gross / net / high-water mark | none (mark steps up only at new net highs: years 1, 4, 7) | clean |
| 4 | ICE exchanges-segment bars | x tick labels ran together ("1,0001,2001,400") → explicit ticks every 500 | clean |
| 4 | four access models (TikZ) | row titles sat on the client boxes → row pitch 1.4 → 1.7 cm | clean |
| 4 | access cost, log-log | none (crossovers at 2.5, 33 and 313 million visible where computed) | clean |
| 4 | new-venue profit vs share | none | clean |
| 5 | trade-to-settlement timeline (TikZ) | none | clean |
| 5 | bilateral web vs CCP hub (TikZ) | none (15 edges left, 6 right, as counted in the proposition) | clean |
| 5 | margin vs volatility | none | clean |
| 5 | waterfall stacked areas | stray plot markers on the x axis → `no markers`; layer order matches the definition | clean |
| 5 | netting efficiency (log x) | none | clean |
| 6 | return on equity vs asset return | caption arithmetic was wrong (said 12.9%, truth 9%: financing is owed too) → corrected and asserted in test_solutions | clean |
| 6 | two legs of a repo (TikZ) | none | clean |
| 6 | short-sale flows (TikZ) | "sale proceeds held" label touched both boxes → shortened | clean |
| 6 | deleveraging spiral | none | clean |
| 7 | realised / unrealised / total through the day | none (realised steps only at the two sales; total ends at 31.0) | clean |
| 7 | three P&L numbers | CSV labels contained commas and would have broken column parsing → semicolons | clean |
| 7 | explain bars | value labels of the negative bars sat on the axis line → xmin −2 → −4 | clean |
| 7 | keeper data flow (TikZ) | none | clean |
| 8 | dividend dates timeline (TikZ) | none | clean |
| 8 | raw vs back-adjusted through a split (log axis) | none (adjusted pre-split level = raw/10, continuous at day 150) | clean |
| 8 | three weighting rules bars | caption called B "second largest" while the plotted float-adjusted weights rank it third → reworded; legend glyphs → `area legend` | clean |
| 8 | index level with / without divisor adjustment | thousands separator was a comma, inconsistent with the book → thin space | clean |
| 9 | tape vs direct feeds (TikZ) | build error: node names with decimal points (`v1.8`) parsed as anchors → letter names | clean |
| 9 | staleness vs tape delay | x tick labels ran together → ticks every 500 | clean |
| 9 | all-in cost by fee model | 12 pt overfull and a value label on a gridline → narrower axis, explicit ticks | clean |
| 9 | where shares traded in 2025 | 4 pt overfull → narrower axis | clean |
| 10 | path of a retail order (TikZ) | "market order" touched a box; sloped "hedges, overflow" ran into the Exchanges box → shortened / removed (caption carries it) | clean |
| 10 | where the half-spread goes | duplicated x tick labels (0.1 0.1 0.2 0.2) → explicit ticks; bars sum to 1.00 as asserted in the script | clean |
| 10 | realised spread vs horizon (log x) | none (exchange flow decays to ~0, retail to 0.65, as in the text) | clean |
| 10 | maximum payment vs informed share | label crossed two gridlines → white background; zero crossing at 23% matches the caption | clean |
| 11 | venue taxonomy (TikZ) | caption said shares trade on "the blue categories" though the blue OTF box says "not for shares" → caption names the categories | clean |
| 11 | effective number of venues | none | clean |
| 11 | on-exchange mechanisms, July 2026 | none (four bars sum to 98.4: the source's remainder is 'other') | clean |
| 11 | volume-cap breach and suspension | none (breach in month 28, dark at zero for months 29–31, periodic share jumps to ~12%) | clean |
| 12 | days locked vs revaluation size | none (steps at 10%, 21%, 33.1%… for the 10% limit, as the proposition gives) | clean |
| 12 | returns with / without a 10% limit (log y) | **content defect**: values exactly at ±10% fell on bin edges, so the spikes appeared at −9.5 and +10.5 → bins re-centred on whole percentages; also a build-stopping comma in a CSV label in the tax chart | clean |
| 12 | northbound Stock Connect order (TikZ) | none | clean |
| 12 | round-trip transaction taxes | none (20 / 20 / 5 bp match the dated boxes) | clean |
| 13 | demand and supply steps | first draft had quantity on x with a y-filter and an unreadable step direction → redrawn with price on x; step levels checked against the example's table (1800/1200/800/300; 200/600/1100/1800) | clean |
| 13 | closing ten minutes (TikZ) | **content defect**: brace said "only offsetting interest may join" for the whole window, true for NYSE only → relabelled, caption made exchange-specific | clean |
| 13 | close move vs imbalance | x and y labels collided at the corner → shortened, plot taller | clean |
| 13 | indicative price and paired volume (two axes) | none | clean |
| 14 | two markets of an ETF (TikZ) | arrow labels ran over both boxes, sloped label collided with the AP box → labels shortened to "trade"/"quote", basket arrow rerouted orthogonally with a two-line label | clean |
| 14 | simulated premium and band | 300 steps unreadably dense → first 120 steps shown; band at ±7 matches the example | clean |
| 14 | stale NAV sell-off | none (max discount 4.0% on day 29 matches caption) | clean |
| 14 | rebalance trade by leverage factor | none (12/6/2/0/2/6 = β(β−1)) | clean |
| 14 | leveraged paths, one year | three-times path clipped at ymax 1.7 (peak 1.696 touching frame) → range 0.4–1.8; end values −5.8% / −17.4% / −41.8% asserted in test_solutions | clean |
| 15 | June 2026 reconstitution timeline (TikZ) | "further updates" label ran into the 29 May and 26 June date labels → raised above them; awkward tick label reworded; dates match ledger F1 | clean |
| 15 | buffer band scatter | legend entries ragged → left-aligned; outcomes checked (12 kept in 201–220, 12 blocked in 181–200, additions all ≤180) | clean |
| 15 | additions per review vs buffer | first point label touched the top frame → ymax 24; "halves" checked (16.95 → 8.82) | clean |
| 15 | stylised event path | y label longer than the axis → shortened, "cumulative" moved to the caption; day-0 heights 7.4 / 0.3 match ledger F6 | clean |
| 16 | lending chain (TikZ) | none; direction of red arrows (collateral and fee to the lender) checked | clean |
| 16 | illustrative fee curve | none | clean |
| 16 | carry of a short going special | **clipped**: net P&L fell to −1,355k, below ymin −700 → range −1500..1100, and the adverse excursion added to the example and asserted in test_solutions; entry forced to exactly $40 | clean |
| 16 | covering cascade | none; kinks at shocks 10% and 20%, end values 60/80/100 checked against the proposition | clean |
| 17 | equity swap cash flows (TikZ) | both arrow labels were longer than the gap and ran over the Client and Dealer boxes → narrower boxes, wider spacing, two-line labels | clean |
| 17 | conversion band of a receipt | centre label sat on the zero gridline and between the curves → moved below with an arrow; "cancel receipts" shifted left | clean |
| 17 | stacked cost by wrapper | tick label baselines uneven ("swap") → strut; totals 140/93/68/56/296 asserted | clean |
| 17 | annualised cost vs horizon | none; crossings at 1.6 and 2.7 years visible and asserted | clean |
| 18 | reading a futures symbol (TikZ) | the three labels under ES / Z / 6 overlapped → letters spaced out, labels centred under each, month strip shifted right | clean |
| 18 | tick in bp of value | bar labels inconsistently formatted (1.4 vs 1.43) → zero-filled to two decimals | clean |
| 18 | stylised roll of open interest | none | clean |
| 18 | hedge residual sawtooth | none; peaks checked against the half-contract bound | clean |
| 19 | three allocation rules, one book | none; bar labels match alloc.csv (10/90/0/0, 2/40/8/50, 10/51/13/26) | clean |
| 19 | fill against shown size (pro rata) | first version sampled every 5 lots and put the threshold at 25 → resampled every lot, threshold 21 asserted, caption corrected | clean |
| 19 | expected fill by queue position | none; crossing at 170 asserted | clean |
| 19 | implied-in diagram (TikZ) | none; all six numbers asserted in test_solutions | clean |
| 20 | sixteen scenario losses | "scan risk" label ran into the top frame → ymax 140, label moved inside | clean |
| 20 | what the scan sees (profile and scenario dots) | x tick labels ran together (−1,000−800) → five ticks; dots lie on the two curves as they must | clean |
| 20 | offsets: legs vs portfolio | top bar label touched the frame → ymax 135 | clean |
| 20 | procyclicality of three margin models | none; 109 / 203 / 94% and calm means asserted | clean |
| 21 | fair basis sawtooth | none; start 42.6, three upward jumps on dividend dates asserted | clean |
| 21 | mispricing inside the arbitrage band | **content defect**: the simulation clamped symmetrically at ±6.47 while the lower band is −10.27 → simulation given both bounds; caption's unsupported claim ("on average slightly rich") removed | clean |
| 21 | rolled position in contango / backwardation | none; end values 0.751 / 1.273 asserted | clean |
| 21 | expiry timeline with special opening quotation (TikZ) | build broke on a comma inside a \foreach item → braced; layout clean | clean |
| 22 | contracts traded by region, 2025 | the 75.6 label was crossed by the gridline at 80 → white label background; the five bars sum to the published 119.29 (asserted) | clean |
| 22 | the global relay in UTC | none; bar ends checked against the session data (FESX 00:10–20:00, HSI three sessions, ES break 21–22) | clean |
| 22 | illustrative dividend strip | 168.0 label sat on the 170 gridline → white label background; truncated axis declared in the caption | clean |
| 23 | payoff panels (groupplot) | put payoff at 40 (8.1) touched the top frame → y range ±9; `groupplots` library was missing from the style → added | clean |
| 23 | exercise and assignment flow (TikZ) | none | clean |
| 23 | net shares at expiry against the close | y label longer than the axis, first label ran into the frame, last label cut at the right edge and then crossed by the step → label shortened (meaning moved to the caption), range widened, labels repositioned; step values asserted | clean |
| 24 | allocation under three rules | none; all 18 bar labels asserted in test_solutions | clean |
| 24 | auction timeline (TikZ) | the two lower labels ran into each other and a response arrow crossed the "t0 + 100 ms" label → two-line labels, arrows moved left | clean |
| 24 | initiator's share against improvement probability | none; end points 65.5% and 12.7% asserted | clean |
| 24 | OPRA projected messages a day | y label longer than the axis and two bar labels on the 300 gridline → label shortened, white label background; values match the notice's table, not the search engine's garbled summary | clean |
| 25 | price against volatility, with the two inversions | none; guide lines end at (20.08, 4.06) and (23.82, 1.12), matching chain.csv | clean |
| 25 | recovered smile | first point label collided with the top frame → ymax 33 | clean |
| 25 | strip weights 1/K² | none; 60 vs 140 ratio 5.4 asserted | clean |
| 25 | two stylised volatility-futures curves | none; declared illustrative in the caption | clean |
| 26 | same-day straddle payoff | premium label crossed both arms of the V → moved under the vertex, axis extended | clean |
| 26 | at-the-money gamma against minutes to expiry (log) | added after the gate showed only three figures and an unused CSV; none | clean |
| 26 | gamma profile at three horizons | two solid lines hard to tell apart in the legend → the one-month line dotted | clean |
| 26 | hedging feedback and realised volatility | y label longer than the axis → "volatility ratio", definition moved to the caption | clean |
| 27 | three rankings of four invented markets | x tick labels ran into one another → two-line centred labels, legend lowered, y label shortened; shares asserted | clean |
| 27 | contracts by region, 2024 (derived) and 2025 | none; derived total reproduces the published −42.2% (asserted) | clean |
| 27 | structure of a settlement-manipulation case (TikZ) | none | clean |
| 28 | one book at three levels (TikZ) | none; level 2 and level 1 rows consistent with the level 3 orders (asserted through the build in test_solutions) | clean |
| 28 | fifteen trade reports, kept and removed | none | clean |
| 28 | messages out of order against jitter | y label slightly longer than the axis → shortened | clean |
| 28 | level 1 and tape rebuilt from the sample | **content defect**: trades printed away from the best quotes because the sample generator executed random resting orders → generator now executes the oldest order at the best price; sample, expected summary, message counts, file size and the reorder percentages regenerated and re-asserted in Python, C++ and Rust; caption corrected (hidden-order trades print inside the spread); y range widened | clean |
| 29 | executing and clearing brokers (TikZ) | "settles with" label touched the clearing-broker box, "positions, cash" touched the firm box → moved above / along the arrow | clean |
| 29 | monthly rebates with tier cliffs | y label longer than the axis → shortened; cliff of $155,400 at 24m asserted | clean |
| 29 | all-in cost on three venue types | none; six labels asserted | clean |
| 30 | access to a futures exchange (TikZ) | "margin calls, more" label ran over the FCM and firm boxes → boxes spaced out, label shortened to "its own calls" | clean |
| 30 | cost of one side by status (stacked) | none; totals 1.45 / 0.57 / 0.45 asserted | clean |
| 30 | monthly cost under three routes | none; crossings at 1.7k and 20.8k sides visible and asserted | clean |
| 30 | round trip as % of a tick | y label longer than the axis → shortened | clean |
| 31 | toy model: three price paths | none; troughs 2.2 / 9.8 / 7.0 asserted; first version of the model discarded (step-dependent), see ledger EXCLUDED | clean |
| 31 | LULD halts, 24 Aug 2015 (bars) | legend touched the x tick labels → moved down | clean |
| 31 | depth needed against tolerated fall | y label longer than the axis → shortened | clean |
