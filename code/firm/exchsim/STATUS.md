# firm.exchsim — status (read before each chapter that needs the simulator)

Written by Book 10's agent; consumers (Books 11, 12, 13) read it. Contract: `code/firm/INTERFACES.md` §7.
Wire formats and engine rules: `PROTOCOL.md`; machine-readable layouts: `schema.json`.

| date | piece | state |
|---|---|---|
| 2026-09-25 | `code/firm/lob` (book; Python + C++20 + Rust twins on a shared fixture) | **landed** |
| 2026-09-25 | `code/firm/ordertypes` (validation, pegs, iceberg slices, self-trade prevention, stops) | **landed** (used by the engine) |
| 2026-09-25 | Python engine `firm_exchsim_engine.py` (all order types, FIFO / pro rata / configurable, auctions, bands, throttle with weights, self-trade prevention, cancel on disconnect, mass cancel, mass quote, stops, pegs, icebergs, snapshots) | **landed** |
| 2026-09-25 | Python simulator `firm_exchsim.py` (configs, `Simulator`, agents and `ctx`, `TapeBackground`, latency with counter-based jitter, speed bump (symmetric and asymmetric), `batch_interval_ns`, phases and auctions with indicatives and cut-off, faults: pause, halt, drop_session/refuse_login as logout-login, scripted orders and raw messages, efficient-price jumps; `Result`: feed packets (MoldUDP64), lines A/B with loss, Gilbert–Elliott bursts, dup, jitter, outages; recorded files; retransmission; snapshot channel; `tape()`; `reports()`; `drop_copy()`; `truth`; journal) | **landed** |
| 2026-09-25 | `TapeAgentAdapter`, `ReplayStrategyAdapter` | **landed** |
| 2026-09-25 | presets `us_equity_lit`, `pro_rata_futures`, `midpoint_dark_pool`, `speed_bumped`, `periodic_batch`, `auction_venue`, `crypto_venue` | **landed** (crypto: 24 h session, fees in bp, request-weight throttle) |
| 2026-09-25 | `PROTOCOL.md`, `schema.json`, fixtures in `data/` (`fixture_config.json`, `fixture_journal.bin` 17,059 records, `fixture_out.bin` + SHA-256, `golden/*.csv|bin`, `fixture_mold.bin`, `fixture_soup.bin/.csv`) | **landed** |
| 2026-09-25 | C++20 `cpp/exchsim_codec.hpp` (all four protocols, allocation-free decode, MoldUDP64, SoupBinTCP frames, journal, CRC-32), `cpp/exchsim_json.hpp`, `cpp/exchsim_engine.hpp` | **landed**: byte-identical to Python on all 17,059 fixture records (`cpp/exchsim_engine_test.cpp`) |
| 2026-09-25 | C++20 live server `cpp/exchsim_server.hpp` + `exchsim_server.cpp` (build: `code/firm/exchsim/cpp/build.sh` → `cpp/bin/exchsim_server --config cfg.json [--seconds N]`): MoldUDP64 feed on lines A/B by **loopback multicast** (works under WSL2; `"multicast": false` sends unicast to `dest_host`), snapshot channel, TCP retransmission (20-byte MoldUDP64 request, u16-prefixed answers), SoupBinTCP 4.0 order entry with credentials and sequenced replay on re-login, heartbeats (drop after 15 s silence), drop-copy sessions, cancel on disconnect, background journal replayed in real time (sessions renumbered +10,000), faults (drop_session, refuse_login, pause, halt; times in ms from start), input journal (`journal_out`) | **landed**; `cpp/exchsim_client.hpp` is a minimal blocking Soup client and UDP receiver for tests; `exchsim_server_test.cpp` trades two firms on loopback |
| — | Rust crate `rust/` (`codec`, `engine`) | after the C++ server |
| 2026-09-25 | Rust crate `rust/` (`codec`, `engine`, `json`) | **landed**: byte-identical to Python on all 17,059 fixture records; golden messages round-trip |
| 2026-09-25 | `python -m firm_exchsim serve --config cfg.json` (from `code/firm/exchsim`; slow live reference, same config and protocols as the C++ server; no background or faults) | **landed** (`tests/test_serve.py`) |
| 2026-09-25 | `make_recorded_day.py` (streams to `data/generated/`, git-ignored: lines A and B, snapshots, journal; default one busy hour, two instruments) | **landed**, tested on a 72-second day; the full-size day generated once on 2026-09-26 under `nice -n 19`: 812,723 feed messages, 807,160 journal records, 806,408 / 805,010 packets on lines A / B, ~140 MB, 34 s, 346 MB peak RSS; SHA-256 of each file in `day_summary.json` |
| 2026-09-25 | `data/server_example.json` (every server option; its `background` must be a journal made with a matching instrument list, e.g. `data/generated/day_journal.bin` with `day_config.json`'s engine) | **landed** |
| 2026-09-25 | consolidated feed: `Simulator(venues, sip=SipConfig(default_ns, venue_ns={venue: ns}, process_ns, agent_ns, round_lot))`; each venue's top of book reaches the SIP after its delay, the NBBO (Book 1's `firm_nbbo`, round lots only) is published `process_ns` later and delivered `agent_ns` after that: `Agent.on_nbbo(ctx, locate, nbbo)`, `ctx.nbbo(locate)` (last received), `ctx.direct_nbbo(locate)` (from the agent's own direct feeds), `Result.sip(locate)` (published series); `inter_venue_ns` is accepted and unused; `TapeBackground(v_path=...)` imposes an efficient path so that several venues' backgrounds share one price | **landed** (Book 10 ch. 8; `tests/test_firm_exchsim.py::test_consolidated_feed_delays_and_direct_view`) |
| 2026-09-25 | dark venues: control **N** (reference quote for midpoint pegs, 11 bytes: locate, bid, ask) in the Python, C++20 and Rust engines and codecs; `ExchangeConfig(reference=lit venue, reference_ns)` makes the simulator send N after each change of the lit top; `midpoint_dark_pool(reference="SIMX", reference_ns=50_000)`. Fixtures regenerated with three N messages (17,059 records; C++ and Rust byte-identical again) | **landed** (Book 10 ch. 9; `tests/test_firm_exchsim.py::test_dark_venue_prices_midpoint_pegs_off_the_lit_venue`) |
| 2026-09-26 | `Simulator.schedule_call(t_ns, fn, *args)` (venue-side processes among the controls) and `code/firm/halts` (`LULD` dynamic bands with limit state, pause and reopening call, `MarketWide`, `Velocity`, `Combined`, loaded as `ExchangeConfig(halts=...)`; they act only through controls R and P); `firm.agentmkt` `PopulationConfig.curve` (intraday activity); `firm.placement.SliceExecutor` per-slice limit | **landed** (chapters 16, 19, 25) |
| 2026-09-26 | `firm.agentmkt` completed (Book 10 ch. 27): chartists (`chart`, `chart_window`, off by default), `MarketMaker` (inventory skew), `facts`/`FACTS`, `distance`, `msm`; the population runs as an Agent (not a background), default population unchanged | **landed** (chapter 27) |

## How to use it now (Python, in process)

```python
import sys; sys.path.insert(0, "code/firm/exchsim"); sys.path.insert(0, "code/firm/tape")
from firm_exchsim import (Simulator, ExchangeConfig, TapeBackground, Agent, Order, SessionSpec, LatencyModel)
from firm_tape import TapeConfig

class Quoter(Agent):
    name = "quoter"
    def on_book(self, ctx, locate, top):          # top = (bid, bid_qty, ask, ask_qty), prices in 1/10,000
        if top[0] is not None and not ctx.working():
            ctx.send(Order(locate, "B", 100, top[0]))

sim = Simulator(ExchangeConfig(), seed=1)
sim.add_background(TapeBackground(TapeConfig(seconds=3600.0, seed=7)))     # one hour from 09:30
sim.add_agent(Quoter(), SessionSpec(firm="HF1", latency=LatencyModel(20_000, 20_000, 20_000)))
res = sim.run()
res.agents["quoter"].fills          # (ts, venue, locate, sign, price, qty, liquidity, fee)
res.tape()                          # firm_tape.Tape: Book 7's lobreplay / lobfeat / tradeflow / markout run on it
res.truth["trades"]                 # aggressor class (noise / informed / agent name / cross) per execution
res.recorded(line="A")              # recorded file of line A (send_ns u64 | len u32 | MoldUDP64 packet)
```

Measured on the laptop (Intel Core Ultra 7 155H, WSL2): one simulated hour of default `firm_tape` flow
(about 31,500 messages) with one quoting agent runs in about 3.3 s, of which 1.3 s is `firm_tape` itself.

## Known limits (Python reference)

- Implied-in calendar-spread instruments (a stretch goal) are not implemented.
- In process, `refuse_login` behaves as `drop_session` (the session is logged out for the window); the live
  server refuses Soup logins in the window.
- `TapeBackground` replays the tape's orders; it does not react to prices (use `firm.agentmkt` for a reactive
  population, chapter 27).
