//! firm.stratengine -- the strategy engine in Rust (build of One Quant Book 13, chapter 20), the twin of the C++20
//! header: the same event loop, hashed timing wheel, parameter snapshots, venue stub and microprice quoter in integer
//! arithmetic, hence the same actions and the same hash on the shared fixture.

use firm_bookbuilder::{Event, LadderBook, ASK, BID};

#[derive(Clone, Copy, Debug)]
pub struct Params {
    pub version: u32,
    pub half_spread_ticks: i64,
    pub size: u32,
    pub skew_ticks_per_size: i64,
    pub stale_ns: u64,
    pub ack_ns: u64,
}

impl Default for Params {
    fn default() -> Self {
        Params { version: 1, half_spread_ticks: 2, size: 100, skew_ticks_per_size: 1, stale_ns: 20_000_000, ack_ns: 50_000 }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Action {
    pub t: u64,
    pub kind: u8,
    pub side: u8,
    pub price: u32,
    pub qty: u32,
    pub version: u32,
    pub id: u64,
}

/// Hashed timing wheel; timers due by a time fire in (time, id) order.
pub struct TimerWheel {
    gran: u64,
    mask: u64,
    tick: u64,
    started: bool,
    pending: usize,
    slots: Vec<Vec<(u64, u64)>>,
    due: Vec<(u64, u64)>,
}

impl TimerWheel {
    pub fn new(gran: u64, slots_pow2: usize, per_slot: usize) -> Self {
        TimerWheel {
            gran,
            mask: slots_pow2 as u64 - 1,
            tick: 0,
            started: false,
            pending: 0,
            slots: (0..slots_pow2).map(|_| Vec::with_capacity(per_slot)).collect(),
            due: Vec::with_capacity(per_slot * 4),
        }
    }
    pub fn schedule(&mut self, t: u64, id: u64) {
        if !self.started {
            self.tick = t / self.gran;
            self.started = true;
        }
        self.slots[((t / self.gran) & self.mask) as usize].push((t, id));
        self.pending += 1;
    }
    pub fn pending(&self) -> usize {
        self.pending
    }
    /// Removes and returns, in order, the timers due by `to` in the current tick; None when the wheel has reached `to`.
    fn next_batch(&mut self, to: u64) -> Option<Vec<(u64, u64)>> {
        if !self.started {
            self.tick = to / self.gran;
            self.started = true;
            return None;
        }
        let last = to / self.gran;
        while self.tick <= last {
            if self.pending == 0 {
                self.tick = last;
                return None;
            }
            let limit = to.min((self.tick + 1) * self.gran - 1);
            let s = &mut self.slots[(self.tick & self.mask) as usize];
            self.due.clear();
            let mut i = 0;
            while i < s.len() {
                if s[i].0 <= limit {
                    self.due.push(s.swap_remove(i));
                } else {
                    i += 1;
                }
            }
            if !self.due.is_empty() {
                self.due.sort();
                self.pending -= self.due.len();
                return Some(self.due.clone());
            }
            if self.tick == last {
                return None;
            }
            self.tick += 1;
        }
        None
    }
}

#[derive(Clone, Copy, Default)]
struct Quote {
    price: u32,
    qty: u32,
    live: bool,
    sent: bool,
    id: u64,
}

const ACK_BID: u64 = 1;
const ACK_ASK: u64 = 2;
const STALE: u64 = 3;

pub struct Engine {
    tick: i64,
    p: Params,
    book: LadderBook,
    wheel: TimerWheel,
    bid: Quote,
    ask: Quote,
    next_id: u64,
    last_market: u64,
    last_micro: i64,
    stale_armed: bool,
    pub actions: Vec<Action>,
    pub position: i64,
    pub cash: i64,
    pub hash: u64,
}

impl Engine {
    pub fn new(tick: u32, p: Params) -> Self {
        Engine {
            tick: tick as i64,
            p,
            book: LadderBook::new(tick, 4096, 1 << 16),
            wheel: TimerWheel::new(100_000, 1024, 64),
            bid: Quote::default(),
            ask: Quote::default(),
            next_id: 0,
            last_market: 0,
            last_micro: 0,
            stale_armed: false,
            actions: Vec::with_capacity(1 << 20),
            position: 0,
            cash: 0,
            hash: 0xCBF29CE484222325,
        }
    }

    pub fn pnl(&self) -> i64 {
        self.cash + self.position * self.last_micro
    }

    fn emit(&mut self, t: u64, kind: u8, side: u8, price: u32, qty: u32, id: u64) {
        let a = Action { t, kind, side, price, qty, version: self.p.version, id };
        self.actions.push(a);
        let mut b = Vec::with_capacity(30);
        b.extend_from_slice(&t.to_le_bytes());
        b.extend_from_slice(&[kind, side]);
        b.extend_from_slice(&price.to_le_bytes());
        b.extend_from_slice(&qty.to_le_bytes());
        b.extend_from_slice(&a.version.to_le_bytes());
        b.extend_from_slice(&id.to_le_bytes());
        for x in b {
            self.hash = (self.hash ^ x as u64).wrapping_mul(0x100000001B3);
        }
    }

    fn on_timer(&mut self, t: u64, id: u64) {
        match id % 4 {
            ACK_BID | ACK_ASK => {
                let side = if id % 4 == ACK_BID { b'B' } else { b'S' };
                let q = if side == b'B' { self.bid } else { self.ask };
                if q.sent && q.id == id / 4 {
                    if side == b'B' {
                        self.bid.live = true;
                    } else {
                        self.ask.live = true;
                    }
                    self.emit(t, b'A', side, q.price, q.qty, q.id);
                }
            }
            STALE => {
                if t >= self.last_market + self.p.stale_ns {
                    for side in *b"BS" {
                        let q = if side == b'B' { self.bid } else { self.ask };
                        if q.sent {
                            self.emit(t, b'P', side, q.price, q.qty, q.id);
                            if side == b'B' {
                                self.bid = Quote::default();
                            } else {
                                self.ask = Quote::default();
                            }
                        }
                    }
                }
                let lm = self.last_market + self.p.stale_ns;
                let next = if lm > t { lm } else { t + self.p.stale_ns };
                self.wheel.schedule(next, STALE);
            }
            _ => {}
        }
    }

    fn quote(&mut self, now: u64, side: u8, price: u32) {
        let q = if side == b'B' { self.bid } else { self.ask };
        if q.sent && q.price == price {
            return;
        }
        let kind = if q.sent { b'R' } else { b'N' };
        self.next_id += 1;
        let nq = Quote { price, qty: self.p.size, live: false, sent: true, id: self.next_id };
        if side == b'B' {
            self.bid = nq;
        } else {
            self.ask = nq;
        }
        self.emit(now, kind, side, price, nq.qty, nq.id);
        self.wheel.schedule(now + self.p.ack_ns, nq.id * 4 + if side == b'B' { ACK_BID } else { ACK_ASK });
    }

    fn fill(&mut self, now: u64, side: u8) {
        let q = if side == b'B' { self.bid } else { self.ask };
        let sgn = if side == b'B' { 1 } else { -1 };
        self.position += sgn * q.qty as i64;
        self.cash -= sgn * q.qty as i64 * q.price as i64;
        self.emit(now, b'F', side, q.price, q.qty, q.id);
        if side == b'B' {
            self.bid = Quote::default();
        } else {
            self.ask = Quote::default();
        }
    }

    fn on_market(&mut self, e: &TimedEvent) {
        let now = e.seq_ts;
        self.book.apply(&e.ev);
        self.last_market = now;
        if !self.stale_armed {
            self.stale_armed = true;
            self.wheel.schedule(now + self.p.stale_ns, STALE);
        }
        let (b, a) = (self.book.depth(BID, 1), self.book.depth(ASK, 1));
        if self.book.stale || b.is_empty() || a.is_empty() {
            return;
        }
        let ((bp, bq), (ap, aq)) = (b[0], a[0]);
        if self.bid.live && ap <= self.bid.price {
            self.fill(now, b'B');
        }
        if self.ask.live && bp >= self.ask.price {
            self.fill(now, b'S');
        }
        let micro = (bp as i64 * aq as i64 + ap as i64 * bq as i64) / (aq + bq) as i64;
        self.last_micro = micro;
        let t = self.tick;
        let skew = self.position * self.p.skew_ticks_per_size / self.p.size as i64 * t;
        let mut bpx = (micro - self.p.half_spread_ticks * t - skew) / t * t;
        let mut apx = (micro + self.p.half_spread_ticks * t - skew + t - 1) / t * t;
        bpx = bpx.min(ap as i64 - t);
        apx = apx.max(bp as i64 + t);
        self.quote(now, b'B', bpx as u32);
        self.quote(now, b'S', apx as u32);
    }

    /// Market events with their timestamps, and parameter snapshots (effective time, parameters).
    pub fn run(&mut self, market: &[TimedEvent], changes: &[(u64, Params)]) {
        let mut c = 0;
        for e in market {
            while let Some(batch) = self.wheel.next_batch(e.seq_ts) {
                for (t, id) in batch {
                    self.on_timer(t, id);
                }
            }
            while c < changes.len() && changes[c].0 <= e.seq_ts {
                self.p = changes[c].1;
                c += 1;
            }
            self.on_market(e);
        }
    }
}

/// A book event with its timestamp (the 48-byte record's ts field).
pub struct TimedEvent {
    pub ev: Event,
    pub seq_ts: u64,
}

pub fn read_events(raw: &[u8]) -> Vec<TimedEvent> {
    raw.chunks(48)
        .map(|b| TimedEvent { ev: Event::from_record(b), seq_ts: u64::from_le_bytes(b[12..20].try_into().unwrap()) })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn replays_to_the_cpp_hash() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
        let raw = std::fs::read(dir.join("bookbuilder/data/events_small.bin")).unwrap();
        let ev = read_events(&raw);
        let want = std::fs::read_to_string(dir.join("stratengine/data/expected.txt")).unwrap();
        let mut a = Engine::new(1, Params::default());
        a.run(&ev, &[]);
        let mut b = Engine::new(1, Params::default());
        b.run(&ev, &[]);
        assert_eq!(a.hash, b.hash);
        assert_eq!(format!("{:016x}", a.hash), want.trim());
        assert!(a.actions.len() > 100);
    }
}
