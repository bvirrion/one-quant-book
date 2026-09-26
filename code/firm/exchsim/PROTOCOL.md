# firm.exchsim — protocols and engine rules

The exchange simulator of One Quant Book 10, chapter 26 (contract: `code/firm/INTERFACES.md` §7).
Every byte layout is generated from one table, `firm_exchsim_codec.MESSAGES`; the machine-readable copy is
`schema.json` (field names, types, offsets, lengths, enums), from which Book 13 generates its codecs. A test
checks `schema.json` against the codec. This file states the semantics.

**Conventions.** Big-endian integers. Prices are unsigned integers in **1/10,000 currency unit** (100.00 is
1,000,000); a price of 0 means *market* in order entry. Feed timestamps are **48-bit nanoseconds since
midnight**; order-entry timestamps are u64 nanoseconds since midnight. `char` is one ASCII byte; `alphaN` is
ASCII, left-justified, space-padded; `numN` is ASCII digits, right-justified, space-padded (SoupBinTCP).

## 1. Market-data feed

### Packets: MoldUDP64

```
session  alpha10   the venue's session name (ExchangeConfig.session, default the venue name)
seq      u64       sequence number of the packet's first message (messages are numbered from 1)
count    u16       number of messages; 0 = heartbeat (seq = next expected), 0xFFFF = end of session
then count times:  length u16 | message
```

Messages produced by one engine event travel together, split into packets of at most `max_packet` (1,400)
bytes. Heartbeats are sent after `heartbeat_ns` (1 s) without data. Lines **A and B** carry identical packets;
each line's impairments are drawn independently from counter-based streams: independent loss, Gilbert–Elliott
burst loss (`burst_loss = (p_good_to_bad, p_bad_to_good, loss_in_bad)`), duplication, exponential jitter
(reordering only when `reorder_window > 0`), a fixed delay per line, and outages (`(line, start_ns, end_ns)`).

### Messages

| type | length | fields after the type byte | meaning |
|---|---|---|---|
| A | 36 | locate u16, tracking u16, ts u48, ref u64, side, shares u32, stock alpha8, price u32 | add displayed order (Book 1 layout) |
| E | 31 | locate, tracking, ts, ref, shares u32, match u64 | displayed order executed at its price (Book 1) |
| X | 23 | locate, tracking, ts, ref, shares u32 | displayed order reduced (partial cancel, same priority) (Book 1) |
| D | 19 | locate, tracking, ts, ref | displayed order deleted (Book 1) |
| P | 44 | locate, tracking, ts, ref (0), side, shares, stock, price, match | trade against a non-displayed order; side = the resting order's (Book 1) |
| U | 35 | locate, tracking, ts, ref u64, new_ref u64, shares u32, price u32 | order replaced: loses priority, new reference (ITCH length) |
| C | 36 | locate, tracking, ts, ref, shares, match, printable char, price u32 | executed at a price other than its own; `N` in auctions (ITCH length) |
| Q | 40 | locate, tracking, ts, shares u64, stock, price, match, cross_type | auction cross, printable, one per cross (ITCH length) |
| I | 50 | locate, tracking, ts, paired u64, imbalance u64, direction, stock, far u32, near u32, ref_price u32, cross_type, variation | indicative price and imbalance (ITCH length); direction B/S/N, or O when no cross is possible |
| S | 12 | locate (0), tracking, ts, event | system event: O start of messages, S start of system hours, Q start of market hours, M end of market hours, E end of system hours, C end of messages |
| H | 25 | locate, tracking, ts, stock, state, reserved, reason alpha4 | trading state: T trading, H halted, P paused (reopening call), Q quotation only (a call phase), C closed |
| R | 28 | locate, tracking, ts, stock, tick u32, lot u32, matching | instrument directory, after the S O event; matching F FIFO, P pro rata, C configurable |
| G | 23 | locate, tracking, ts, seq u64, orders u32 | snapshot begin: the book reflects every incremental message up to `seq` |
| W | 23 | locate, tracking, ts, seq u64, crc u32 | snapshot end: CRC-32 (zlib) of the snapshot's A messages, encoded, concatenated |

The feed's `ref` is the **exchange order reference** returned in the Accepted report, so a participant finds its
own orders in the feed. Hidden orders, midpoint pegs, stop orders waiting for their trigger, market orders in
a call and at-the-close orders are never displayed. An iceberg shows its displayed slice; when the slice is
consumed, a new A with a **new reference** appears at the back of the queue.

### Snapshot channel, retransmission, recorded files

- **Snapshot channel**: its own MoldUDP64 session (the venue name truncated to nine characters plus `S`) and
  its own sequence. Every `snapshot_every_ns`, per instrument: G, H (current state), the displayed orders as A
  messages in priority order (bids best first, then asks; time order within a price), W.
- **Retransmission**: a request `(session, seq, count)` (a MoldUDP64 header whose count is the number of
  messages wanted) returns packets carrying messages `seq … seq+count−1`, at most `max_retransmit` (1,000)
  messages, from a window of the last `window` (100,000) messages; beyond the window, recover from a snapshot.
  In-process: `Result.retransmit(venue, seq, count)`; live: over TCP, each answer packet prefixed by u16 length.
- **Recorded file**: records `send_ns u64 | length u32 | MoldUDP64 packet`, where `send_ns` is when the packet
  reaches the recording point on that line (venue send time + line delay + jitter), in arrival order. A
  deterministic recorded day of more than a million messages is regenerated by `make_recorded_day.py` (not
  committed).

## 2. Order entry

### Session layer: SoupBinTCP 4.0

Frames are `length u16 | type char | payload` (the length counts the type byte).

| from | type | payload |
|---|---|---|
| client | L login request | username alpha6, password alpha10, requested session alpha10 (blank = current), requested sequence num20 (next sequenced message wanted; 0 = the next one from now) |
| client | U unsequenced data | one inbound application message |
| client | R heartbeat | — |
| client | O logout request | — |
| server | A login accepted | session alpha10, sequence num20 (the next sequenced message's number) |
| server | J login rejected | reason: A not authorized, S session not available |
| server | S sequenced data | one outbound application message |
| server | H heartbeat | — |
| server | Z end of session | — |
| server | + debug | text |

Outbound application messages are numbered per session from 1; logging in again with a requested sequence
replays every message from that number. Heartbeats are due every second; a session silent for 15 s is dropped.
Losing the TCP connection disconnects the session: with **cancel on disconnect** (the session's default in the
simulator) every live order of the session is cancelled with reason D.

### Inbound application messages

| type | length | fields |
|---|---|---|
| O Enter | 38 | cl_ord_id u64, locate u16, side B/S, qty u32, price u32 (0 = market), tif, display, post_only Y/N, display_qty u32 (iceberg slice; visible orders only), min_qty u32 (IOC orders and midpoint pegs only), stp_group u16, stp_mode, stop_price u32 (0 = none) |
| U Replace | 25 | cl_ord_id u64 (the order), new_cl_ord_id u64, qty u32 (new total remaining), price u32 |
| X Cancel | 13 | cl_ord_id u64, leave_qty u32 (0 = cancel all; otherwise reduce to this) |
| M Mass cancel | 4 | locate u16 (0 = all), side B, S or `*` |
| Q Mass quote | 27 | quote_id u64, locate u16, bid_price u32, bid_qty u32, ask_price u32, ask_qty u32; replaces the session's previous quote on the instrument; its legs are orders with cl_ord_id 2·quote_id (bid) and 2·quote_id+1 (ask); qty 0 = no leg |

`tif`: D day, G good till cancelled, I immediate or cancel, F fill or kill, O at the open (opening call only),
C at the close (kept aside until the closing cross; accepted until the cut-off). `display`: Y visible, N
hidden, M midpoint peg (hidden, priced at the mid of the reference quote of control N when one has been received, else
of the displayed best bid and ask, capped by `price` if
non-zero, inactive when a side is empty), P primary peg (visible, priced at the best displayed price of its
side among orders that are not pegged, capped by `price`). `stp_mode` (self-trade prevention between orders of
the same firm and the same non-zero group; the incoming order's mode applies): N none (they trade), O cancel
the resting order, W cancel the incoming order, B cancel both, D decrement both by the smaller size.

### Outbound application messages

| type | length | fields |
|---|---|---|
| S System event | 10 | ts u64, event (as the feed's S) |
| A Accepted | 39 | ts, cl_ord_id, ref u64, locate, side, qty, price, tif, display, state (L live, S stop waiting) |
| U Replaced | 42 | ts, cl_ord_id (old), new_cl_ord_id, ref (new if priority lost), qty, price, priority Y kept / N lost |
| C Canceled | 22 | ts, cl_ord_id, decrement u32, reason: U user, I IOC/FOK/market remainder, S self-trade prevention, D disconnect, H halt, M mass cancel, E expired |
| E Executed | 46 | ts, cl_ord_id, qty, price, match u64, liquidity (A added, R removed, C cross), fee i64 (1e-6 currency; negative = rebate), leaves u32 |
| J Rejected | 18 | ts, cl_ord_id, reason: T throttle, X price off the tick grid, Q bad quantity, H halted or closed (or wrong phase for the time in force), S unknown instrument, D duplicate cl_ord_id, O post-only would cross, B outside the price band, L too late to cancel or unknown order, C at-the-close entry after the cut-off |

**Order states on the venue.** Live → partially filled → filled | cancelled | expired; a replace yields a new
cl_ord_id (and a new reference when priority is lost); a rejection is final. Pending-new and pending-cancel are
the client's states. The cancel–fill race is real: a cancel that arrives after the last fill gets J L.

**Drop copy.** A read-only session carrying every E and C of the firm's sessions (in-process:
`Result.drop_copy(firm)`).

## 3. The engine journal and control messages

The engine is a pure function of its journal. A record is `t_ns u64 | session u16 | length u16 | message`, in
arrival order; session 0 carries **control messages** (the venue operator), other sessions inbound
application messages. The C++20 and Rust engines replay `data/fixture_journal.bin` and must reproduce
`data/fixture_out.bin` byte for byte (format in `make_fixtures.py`).

| type | length | fields | effect |
|---|---|---|---|
| L | 8 | session u16, firm u32, cod Y/N | log a session in (firm = the self-trade prevention identity) |
| D | 3 | session u16 | log it out; cancel on disconnect if cod |
| P | 8 | locate u16 (0 = all), phase, reason alpha4 | set the phase: C closed, O opening call, T continuous, K closing call, H halted, U paused (reopening call), B batch call; H on the feed |
| X | 4 | locate, cross_type | run an uncross now (frequent batch auctions) |
| I | 4 | locate, cross_type | publish the indicative price and imbalance (I on the feed) |
| R | 15 | locate, ref_price u32, band_lo u32, band_hi u32 | reference price and price band (0, 0 = none) |
| E | 4 | locate, tif | expire: D day, at-open and at-close orders; A everything |
| F | 4 | locate, freeze Y/N | freeze at-the-close entry (the cut-off) |
| S | 2 | event | system event on the feed and to every logged-in session; O also publishes the directory (R) |
| N | 11 | locate, bid u32, ask u32 | reference quote for midpoint pegs (a dark venue's view of a lit market; the simulator sends it `reference_ns` after each change of the `reference` venue's top); 0 on either side clears it; pegs are repriced at once |

## 4. Engine rules

Every record is stamped `ts = max(t_ns, busy_until) + engine_ns` (`busy_until` becomes `ts`): a burst of
messages queues behind the engine. Feed messages and reports of a record carry `ts`, in the order below.

1. **Throttle** (per session): a token bucket in integer nano-tokens; each message costs its weight
   (default 1) × 10⁹; the bucket refills `rate` × elapsed ns up to `burst` × 10⁹; empty → J T.
2. **Validation** of an Enter, in order: phase closed or halted → H; qty 0 or above 10⁹, or display_qty above
   qty → Q; unknown enum → Q; min_qty on anything but IOC or midpoint peg → Q; display_qty on anything but
   visible → Q; price or stop price off the tick grid → X; at-the-open outside the opening call → H; at-the-close
   after the cut-off → C (or outside T, K, O → H); price outside the band → B. Unknown instrument → S and a
   duplicate cl_ord_id (ever used by the session) → D are checked first. Post-only (visible or hidden, in
   continuous trading) that would execute → O.
3. **Accepted** (A), then: a stop order waits (state S) until a trade at or through its stop price, then enters
   as a market (price 0) or stop-limit order, without a second A; at-the-close orders wait for the closing cross;
   pegs are priced at the end of the record (rule 7).
4. **Call phases** (O, K, U, B): orders rest without matching (market orders apart, not displayed; IOC and FOK are
   cancelled at once, reason I).
5. **Continuous matching**: fill-or-kill and min_qty first compare the executable quantity (at marketable prices,
   within the band, excluding self-trade conflicts and resting orders whose min_qty exceeds the incoming size)
   with what is required, and cancel (I) if it falls short (a midpoint peg below its minimum rests instead).
   Then prices from best to worst while marketable and inside the band; at each price the level's orders, the
   displayed ones first then the hidden ones, each group in time order:
   - self-trade conflicts are resolved by the incoming order's mode as they are met;
   - FIFO instruments fill in that order; pro-rata and configurable instruments allocate with Book 1's
     `firm_match.configurable(level, qty, top_pct, 0, fifo_pct, min_alloc)` (top order's share, a FIFO share,
     pro rata by displayed size with allocations below `min_alloc` dropped, leftovers in time order); the *top
     order* is one that set a new best price when it arrived;
   - each fill: E (displayed) or P (hidden) on the feed, E to the resting order (liquidity A, maker fee) and to
     the incoming order (R, taker fee), in that order; an iceberg's consumed slice refreshes at the back.
6. **Remainder**: market orders, IOC and FOK are cancelled (C I); others rest (A on the feed if visible).
7. **Settle**, repeated until nothing changes: triggered stops enter (in time order); pegs are re-priced in entry
   order (a visible peg that moves is published as U with a new reference; a peg that would cross executes as an
   incoming order); a crossed book is uncrossed by taking the later of the two top orders as the aggressor
   (published D, re-entered with a new reference).
8. **Replace**: a size decrease at the same price keeps priority (X for the displayed reduction, U report with
   priority Y); anything else loses it (U on the feed with a new reference, or D then matching if the new price
   is marketable; U report with priority N). Reductions come from an iceberg's reserve first.
9. **Auctions**: leaving a call phase (O → T: opening cross O; K → C and T → C: closing cross C; U → T: H;
   B → T and X: B) runs Book 1's `firm_auction.uncross` over the book (pegs excluded), market orders in the call
   and, for the closing cross, at-the-close orders: maximum volume, minimum surplus, market pressure, closest to
   the reference price (lower on a tie). Every fill is an E report with liquidity C at the cross price; displayed
   orders get C (printable N) on the feed; one Q per cross. Leftover market orders are cancelled (I), at-the-open
   and at-the-close orders expire (E). The cross price becomes the reference and last price.
10. **Fees**: unit share: rate (1e-6 currency per share) × qty; unit bp: truncate toward zero of
    price × qty × rate / 10,000 (rate in 1e-6 of notional, i.e. hundredths of a basis point).
