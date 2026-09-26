# 1. Where Latency Comes From — brief and source ledger

## Brief

- **Hook.** In a study of a large exchange's own message data, the winner of a race to trade on a stale quote beat the loser by a few millionths of a second, and such races were a sizeable share of the day's volume: a microsecond is a unit of competition, not of engineering pride.
- **Sections.** The tick-to-trade path, stage by stage; Latency is a distribution: medians, tails, jitter; Budgets from wire to wire; Which strategies pay for which microseconds.
- **Defines.** latency, tick-to-trade latency, wire-to-wire latency, latency budget, hot path, tail latency, jitter.
- **Uses (defined earlier).** exchange timestamp (B1.28), receive timestamp (B1.28), latency model (B7.18), order-entry latency (B7.18), market-data latency (B7.18), direct feed (B1.9), adverse selection (B1.1), latency arbitrage (B11.9), heavy-tailed distribution (B4.15).
- **Tutorial.** Time each stage of a toy tick-to-trade path (Book 1's C++ decoder, a book update, a decision, an order encode) with a steady clock, then compose per-stage distributions in Python: the sum of the stage medians against the median of the sum, the sum of the stage 99th percentiles against the 99th percentile of the sum. End state: a stacked budget chart and a table of percentiles, measured on this laptop.
- **Build.** `firm.latbudget`: a latency budget as data (stages, targets per percentile), composition of per-stage histograms by convolution or by joint samples, a budget-against-measurement report; Python. Consumed by chapter 26.
- **Weekend problem.** The microsecond that lost the race -- named result: a firm's probability of winning a race against one competitor, from both latency distributions, and the gain from halving its 99th percentile compared with halving its median.
- **Data.** Book 1's firm.feed sample; measured stage timings on this laptop (bench script, machine named in the caption).
- **Facts to verify.** Aquilina, Budish and O'Neill 2022, Quantifying the high-frequency trading arms race (QJE): race duration and share of volume; speed of light in optical fibre (refractive index about 1.47); a published matching-engine round-trip latency of a major venue (dated); tuned-server tick-to-trade figures from a public talk (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Latency-arbitrage races on LSE FTSE 100 stocks: about one per minute per symbol; modal race lasts 5-10 millionths of a second; about 20% of volume; top six firms over 80% of wins and losses; roughly 0.5 bp tax on trading | Aquilina, Budish and O'Neill, Quantifying the high-frequency trading arms race, QJE 137(1), 2022, pp. 493-564 (abstract) | https://ideas.repec.org/a/oup/qjecon/v137y2022i1p493-564..html | 2026-09-25 | abstract: "very frequent (about one per minute per symbol for FTSE 100 stocks), extremely fast (the modal race lasts 5-10 millionths of a second)... about 20%... top six firms accounting for over 80%... roughly 0.5 basis point tax" | hook; section 4 |
| F2 | A very good minimum wire-to-wire time for a software-based trading system is around 2.5 us (talk by an engineer of a large electronic market maker, 2017) | C. Cook, When a Microsecond Is an Eternity: High Performance Trading Systems in C++, CppCon 2017, slide 14 | https://github.com/CppCon/CppCon2017/blob/master/Presentations/When%20a%20Microsecond%20Is%20an%20Eternity/When%20a%20Microsecond%20Is%20an%20Eternity%20-%20Carl%20Cook%20-%20CppCon%202017.pdf | 2026-09-25 | slide 14: "A very good minimum time (wire to wire) for a software-based trading system is around 2.5us" | dat:ll:where-latency-comes-from:published |
| F3 | STAC-T0 (tick-to-trade network I/O, UDP in, TCP out): FPGA system (Alveo UL3524 with an nxTCP-UDP core) minimum actionable latency 13.9 ns for 507-byte frames, 14.1 ns for 68-byte frames, report of 25 June 2024 | STAC news, STAC-T0 results with an Exegy/AMD FPGA solution | https://docs.stacresearch.com/news/AMD240422 | 2026-09-25 | "time from the last bit of inbound data needed to make a trading decision to the first bit of the simulated outbound order"; "13.9 nanoseconds" | dat:ll:where-latency-comes-from:published |
| F4 | Effective group index of refraction of a standard single-mode fibre: 1.4620 at 1550 nm (1.4606 at 1310 nm) | Corning SMF-28 ULL product information PI1470, issued March 2020 | https://www.fionec.com/wp-content/uploads/Corning_SMF-28-ULL_2020-03.pdf | 2026-09-25 | "Effective Group Index of Refraction (neff) 1310 nm: 1.4606, 1550 nm: 1.4620" | section 3 (4.88 ns per metre) |

## EXCLUDED

