//! The matching engine, a port of `firm_exchsim_engine.py` (and of `cpp/exchsim_engine.hpp`): the same journal in,
//! byte-identical feed and reports out. Orders live in an arena (`Vec<Order>`) and are referred to by index.
#![allow(clippy::needless_range_loop)]

use crate::codec::{crc32, Ctl, Feed, In, Out};
use crate::json::Value;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet, VecDeque};

const NANO: i64 = 1_000_000_000;
const MAX_QTY: i64 = 1_000_000_000;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Where {
    None,
    Book,
    Stop,
    Mkt,
    Close,
    Peg,
}

#[derive(Debug, Clone)]
struct Order {
    reference: u64,
    side: i32,
    price: i64,
    qty: i64,
    visible: bool,
    seq: u64,
    session: u16,
    cl: u64,
    firm: u32,
    locate: u16,
    tif: u8,
    display: u8,
    post_only: bool,
    display_qty: i64,
    reserve: i64,
    min_qty: i64,
    stp_group: u16,
    stp_mode: u8,
    stop_price: i64,
    limit: i64,
    place: Where,
    top: bool,
}

impl Order {
    fn remaining(&self) -> i64 {
        self.qty + self.reserve
    }
}

#[derive(Default)]
struct Level {
    vis: VecDeque<usize>,
    hid: VecDeque<usize>,
}

#[derive(Default)]
struct Book {
    bids: BTreeMap<i64, Level>,
    asks: BTreeMap<i64, Level>,
    orders: HashMap<u64, usize>,
}

impl Book {
    fn side_map(&mut self, side: i32) -> &mut BTreeMap<i64, Level> {
        if side == 1 {
            &mut self.bids
        } else {
            &mut self.asks
        }
    }
    fn side_ref(&self, side: i32) -> &BTreeMap<i64, Level> {
        if side == 1 {
            &self.bids
        } else {
            &self.asks
        }
    }
    fn best(&self, side: i32) -> Option<i64> {
        let m = self.side_ref(side);
        if side == 1 {
            m.keys().next_back().copied()
        } else {
            m.keys().next().copied()
        }
    }
    fn prices(&self, side: i32) -> Vec<i64> {
        let m = self.side_ref(side);
        if side == 1 {
            m.keys().rev().copied().collect()
        } else {
            m.keys().copied().collect()
        }
    }
    fn level_orders(&self, side: i32, p: i64) -> Vec<usize> {
        match self.side_ref(side).get(&p) {
            None => Vec::new(),
            Some(l) => l.vis.iter().chain(l.hid.iter()).copied().collect(),
        }
    }
    fn best_visible(&self, side: i32) -> Option<i64> {
        let m = self.side_ref(side);
        if side == 1 {
            m.iter().rev().find(|(_, l)| !l.vis.is_empty()).map(|(p, _)| *p)
        } else {
            m.iter().find(|(_, l)| !l.vis.is_empty()).map(|(p, _)| *p)
        }
    }
}

struct Inst {
    symbol: [u8; 8],
    tick: i64,
    lot: i64,
    matching: u8,
    top_pct: i64,
    fifo_pct: i64,
    min_alloc: i64,
    book: Book,
    phase: u8,
    ref_price: i64,
    band_lo: i64,
    band_hi: i64,
    last: i64,
    frozen: bool,
    stops: Vec<usize>,
    mkt: Vec<usize>,
    close: Vec<usize>,
    pegs: Vec<usize>,
    pegged: HashSet<u64>,
    ref_quote: Option<(i64, i64)>, // control N: reference quote for midpoint pegs
}

struct Sess {
    firm: u32,
    cod: bool,
    logged: bool,
    tokens: i64,
    last_t: Option<u64>,
    used: HashSet<u64>,
    live: HashMap<u64, usize>,
    quotes: BTreeMap<u16, Vec<u64>>,
}

/// An execution: (match, locate, price, qty, resting session, aggressor session, side, liquidity).
#[derive(Debug, Clone, Copy)]
pub struct Trade {
    pub matched: u64,
    pub locate: u16,
    pub price: i64,
    pub qty: i64,
}

fn marketable(side: i32, limit: i64, price: i64) -> bool {
    if limit == 0 {
        return true;
    }
    if side == 1 {
        price <= limit
    } else {
        price >= limit
    }
}

fn stp_actions(mode: u8) -> (bool, bool, bool) {
    match mode {
        b'O' => (true, false, false),
        b'W' => (false, true, false),
        b'B' => (true, true, false),
        b'D' => (false, false, true),
        _ => (false, false, false),
    }
}

fn is_call(phase: u8) -> bool {
    matches!(phase, b'O' | b'K' | b'U' | b'B')
}

fn state_of(phase: u8) -> u8 {
    match phase {
        b'T' => b'T',
        b'H' => b'H',
        b'U' => b'P',
        b'C' => b'C',
        _ => b'Q',
    }
}

fn symbol8(s: &str) -> [u8; 8] {
    let mut x = [b' '; 8];
    for (i, c) in s.bytes().take(8).enumerate() {
        x[i] = c;
    }
    x
}

/// Book 1's firm_match.configurable (lmm share 0).
fn configurable(book: &[(i64, bool)], qty: i64, top_pct: i64, fifo_pct: i64, min_alloc: i64) -> Vec<i64> {
    let n = book.len();
    let mut fills = vec![0i64; n];
    fn take(fills: &mut [i64], book: &[(i64, bool)], i: usize, want: i64, left: i64) -> i64 {
        let got = want.min(book[i].0 - fills[i]).min(left);
        if got > 0 {
            fills[i] += got;
        }
        left - got.max(0)
    }
    let total: i64 = book.iter().map(|b| b.0).sum();
    let mut left = qty.min(total);
    if let Some(i) = book.iter().position(|b| b.1) {
        left = take(&mut fills, book, i, qty * top_pct / 100, left);
    }
    let mut by_time = left * fifo_pct / 100;
    for i in 0..n {
        if by_time <= 0 {
            break;
        }
        let before = left;
        left = take(&mut fills, book, i, by_time, left);
        by_time -= before - left;
    }
    let open: Vec<i64> = (0..n).map(|i| book[i].0 - fills[i]).collect();
    let tot: i64 = open.iter().sum();
    left = left.min(tot);
    if left <= 0 {
        return fills;
    }
    let target = left;
    for i in 0..n {
        let share = target * open[i] / tot;
        if share >= min_alloc {
            left = take(&mut fills, book, i, share, left);
        }
    }
    for i in 0..n {
        left = take(&mut fills, book, i, book[i].0, left);
    }
    fills
}

struct Uncrossing {
    price: Option<i64>,
    volume: i64,
    surplus: i64,
    fills: Vec<(usize, i64)>,
}

/// Book 1's firm_auction.uncross.
fn uncross(orders: &[(i32, i64, Option<i64>, u64)], reference: i64) -> Uncrossing {
    let mut ps: BTreeSet<i64> = orders.iter().filter_map(|o| o.2).collect();
    ps.insert(reference);
    let table: Vec<(i64, i64, i64)> = ps
        .iter()
        .map(|&p| {
            let d: i64 = orders
                .iter()
                .filter(|o| o.0 > 0 && o.2.is_none_or(|x| x >= p))
                .map(|o| o.1)
                .sum();
            let s: i64 = orders
                .iter()
                .filter(|o| o.0 < 0 && o.2.is_none_or(|x| x <= p))
                .map(|o| o.1)
                .sum();
            (p, d, s)
        })
        .collect();
    let best = table.iter().map(|r| r.1.min(r.2)).max().unwrap_or(0);
    if best == 0 {
        return Uncrossing {
            price: None,
            volume: 0,
            surplus: 0,
            fills: Vec::new(),
        };
    }
    let c: Vec<_> = table.iter().copied().filter(|r| r.1.min(r.2) == best).collect();
    let least = c.iter().map(|r| (r.1 - r.2).abs()).min().unwrap_or(0);
    let c2: Vec<_> = c.into_iter().filter(|r| (r.1 - r.2).abs() == least).collect();
    let pick = if c2.iter().all(|r| r.1 > r.2) {
        *c2.last().unwrap()
    } else if c2.iter().all(|r| r.1 < r.2) {
        c2[0]
    } else {
        let mut best_r = c2[0];
        for r in &c2 {
            let (dr, dp) = ((r.0 - reference).abs(), (best_r.0 - reference).abs());
            if dr < dp || (dr == dp && r.0 < best_r.0) {
                best_r = *r;
            }
        }
        best_r
    };
    let mut fills = Vec::new();
    for side in [1i32, -1] {
        let mut el: Vec<usize> = (0..orders.len())
            .filter(|&i| {
                let o = &orders[i];
                o.0 == side && o.2.is_none_or(|x| if side > 0 { x >= pick.0 } else { x <= pick.0 })
            })
            .collect();
        el.sort_by_key(|&i| {
            let o = &orders[i];
            (o.2.is_some(), -i64::from(side) * o.2.unwrap_or(0), o.3)
        });
        let mut left = best;
        for i in el {
            let q = left.min(orders[i].1);
            if q != 0 {
                fills.push((i, q));
            }
            left -= q;
        }
    }
    Uncrossing {
        price: Some(pick.0),
        volume: best,
        surplus: pick.1 - pick.2,
        fills,
    }
}

pub struct Engine {
    inst: BTreeMap<u16, Inst>,
    sessions: BTreeMap<u16, Sess>,
    pool: Vec<Order>,
    touched: BTreeSet<u16>,
    weights: HashMap<u8, i64>,
    engine_ns: u64,
    busy: u64,
    next_ref: u64,
    next_match: u64,
    seq: u64,
    rate: i64,
    burst: i64,
    make: i64,
    take: i64,
    cross: i64,
    fee_bp: bool,
    pub ts: u64,
    pub feed: Vec<Feed>,
    pub reports: Vec<(u16, Out)>,
    pub trades: Vec<Trade>,
}

impl Engine {
    pub fn new(cfg: &Value) -> Engine {
        let fees = cfg.get("fees").cloned().unwrap_or_default();
        let th = cfg.get("throttle").cloned().unwrap_or_default();
        let mut weights = HashMap::new();
        if let Some(Value::Obj(w)) = th.get("weights") {
            for (k, v) in w {
                if let Value::Int(i) = v {
                    weights.insert(k.as_bytes()[0], *i);
                }
            }
        }
        let mut inst = BTreeMap::new();
        for d in cfg.arr("instruments") {
            let locate = d.int("locate", 0) as u16;
            inst.insert(
                locate,
                Inst {
                    symbol: symbol8(&d.str("symbol", "")),
                    tick: d.int("tick", 1),
                    lot: d.int("lot", 1),
                    matching: d.str("matching", "F").as_bytes()[0],
                    top_pct: d.int("top_pct", 0),
                    fifo_pct: d.int("fifo_pct", 0),
                    min_alloc: d.int("min_alloc", 1),
                    book: Book::default(),
                    phase: d.str("phase", "C").as_bytes()[0],
                    ref_price: d.int("start_price", 0),
                    band_lo: 0,
                    band_hi: 0,
                    last: 0,
                    frozen: false,
                    stops: Vec::new(),
                    mkt: Vec::new(),
                    close: Vec::new(),
                    pegs: Vec::new(),
                    pegged: HashSet::new(),
                    ref_quote: None,
                },
            );
        }
        Engine {
            inst,
            sessions: BTreeMap::new(),
            pool: Vec::new(),
            touched: BTreeSet::new(),
            weights,
            engine_ns: cfg.int("engine_ns", 0) as u64,
            busy: 0,
            next_ref: 1,
            next_match: 0,
            seq: 0,
            rate: th.int("rate", 0),
            burst: th.int("burst", 0),
            make: fees.int("make", 0),
            take: fees.int("take", 0),
            cross: fees.int("cross", 0),
            fee_bp: fees.str("unit", "share") == "bp",
            ts: 0,
            feed: Vec::new(),
            reports: Vec::new(),
            trades: Vec::new(),
        }
    }

    pub fn locates(&self) -> Vec<u16> {
        self.inst.keys().copied().collect()
    }

    /// One journal record; outputs replace `feed` and `reports`.
    pub fn process(&mut self, t_ns: u64, session: u16, payload: &[u8]) {
        self.feed.clear();
        self.reports.clear();
        self.touched.clear();
        self.ts = t_ns.max(self.busy) + self.engine_ns;
        self.busy = self.ts;
        if session == 0 {
            if let Ok(c) = Ctl::decode(payload) {
                self.control(&c);
            }
        } else if self.sessions.get(&session).is_some_and(|s| s.logged) {
            if let Ok(m) = In::decode(payload) {
                let w = *self.weights.get(&m.kind).unwrap_or(&1);
                if self.throttled(session, t_ns, w) {
                    let cl = match m.kind {
                        b'O' | b'U' | b'X' => m.cl_ord_id,
                        b'Q' => m.quote_id.wrapping_mul(2),
                        _ => 0,
                    };
                    self.rej(session, cl, b'T');
                } else {
                    self.inbound(session, &m);
                }
            }
        }
        let locs: Vec<u16> = self.touched.iter().copied().collect();
        for l in locs {
            self.settle(l);
        }
    }

    pub fn snapshot(&self, locate: u16, seq: u64, at: u64) -> Vec<Feed> {
        let st = &self.inst[&locate];
        let n = st.book.orders.values().filter(|&&i| self.pool[i].visible).count() as u32;
        let mut out = vec![Feed {
            kind: b'G',
            locate,
            ts: at,
            seq,
            orders: n,
            ..Feed::default()
        }];
        out.push(Feed {
            kind: b'H',
            locate,
            ts: at,
            stock: st.symbol,
            state: state_of(st.phase),
            reason: *b"SNAP",
            ..Feed::default()
        });
        let mut body = Vec::new();
        for side in [1, -1] {
            for p in st.book.prices(side) {
                for i in st.book.level_orders(side, p) {
                    let o = &self.pool[i];
                    if !o.visible {
                        continue;
                    }
                    let a = Feed {
                        kind: b'A',
                        locate,
                        ts: at,
                        reference: o.reference,
                        side: if side == 1 { b'B' } else { b'S' },
                        shares: o.qty as u64,
                        stock: st.symbol,
                        price: p as u32,
                        ..Feed::default()
                    };
                    a.encode(&mut body);
                    out.push(a);
                }
            }
        }
        out.push(Feed {
            kind: b'W',
            locate,
            ts: at,
            seq,
            crc: crc32(&body),
            ..Feed::default()
        });
        out
    }

    // -- helpers ------------------------------------------------------------------------------------------------
    fn throttled(&mut self, session: u16, t: u64, weight: i64) -> bool {
        if self.rate <= 0 {
            return false;
        }
        let (rate, cap) = (self.rate, i128::from(self.burst) * i128::from(NANO));
        let s = self.sessions.get_mut(&session).unwrap();
        if let Some(last) = s.last_t {
            let refill = i128::from(s.tokens) + i128::from(t as i64 - last as i64) * i128::from(rate);
            s.tokens = refill.min(cap) as i64;
        }
        s.last_t = Some(t);
        if s.tokens >= weight * NANO {
            s.tokens -= weight * NANO;
            false
        } else {
            true
        }
    }
    fn fee(&self, liq: u8, price: i64, qty: i64) -> i64 {
        let rate = match liq {
            b'A' => self.make,
            b'R' => self.take,
            _ => self.cross,
        };
        if !self.fee_bp {
            return rate * qty;
        }
        (i128::from(price) * i128::from(qty) * i128::from(rate) / 10_000) as i64
    }
    fn new_ref(&mut self) -> u64 {
        let r = self.next_ref;
        self.next_ref += 1;
        r
    }
    fn next_seq(&mut self) -> u64 {
        self.seq += 1;
        self.seq
    }
    fn rep(&mut self, session: u16, m: Out) {
        self.reports.push((session, m));
    }
    fn rej(&mut self, session: u16, cl: u64, reason: u8) {
        let m = Out {
            kind: b'J',
            ts: self.ts,
            cl_ord_id: cl,
            reason,
            ..Out::default()
        };
        self.rep(session, m);
    }
    fn rep_c(&mut self, session: u16, cl: u64, dec: i64, reason: u8) {
        let m = Out {
            kind: b'C',
            ts: self.ts,
            cl_ord_id: cl,
            decrement: dec as u32,
            reason,
            ..Out::default()
        };
        self.rep(session, m);
    }
    #[allow(clippy::too_many_arguments)]
    fn rep_e(&mut self, session: u16, cl: u64, q: i64, p: i64, m: u64, liq: u8, fee: i64, leaves: i64) {
        let e = Out {
            kind: b'E',
            ts: self.ts,
            cl_ord_id: cl,
            qty: q as u32,
            price: p as u32,
            matched: m,
            liquidity: liq,
            fee,
            leaves: leaves as u32,
            ..Out::default()
        };
        self.rep(session, e);
    }
    fn fbase(&self, kind: u8, locate: u16) -> Feed {
        Feed {
            kind,
            locate,
            ts: self.ts,
            ..Feed::default()
        }
    }
    fn feed_a(&mut self, loc: u16, i: usize, shown: i64, price: i64) {
        let o = &self.pool[i];
        let a = Feed {
            reference: o.reference,
            side: if o.side == 1 { b'B' } else { b'S' },
            shares: shown as u64,
            stock: self.inst[&loc].symbol,
            price: price as u32,
            ..self.fbase(b'A', loc)
        };
        self.feed.push(a);
    }
    fn feed_d(&mut self, loc: u16, r: u64) {
        let d = Feed {
            reference: r,
            ..self.fbase(b'D', loc)
        };
        self.feed.push(d);
    }
    fn feed_x(&mut self, loc: u16, r: u64, q: i64) {
        let x = Feed {
            reference: r,
            shares: q as u64,
            ..self.fbase(b'X', loc)
        };
        self.feed.push(x);
    }
    fn feed_u(&mut self, loc: u16, r: u64, nr: u64, q: i64, p: i64) {
        let u = Feed {
            reference: r,
            new_ref: nr,
            shares: q as u64,
            price: p as u32,
            ..self.fbase(b'U', loc)
        };
        self.feed.push(u);
    }
    fn st(&mut self, loc: u16) -> &mut Inst {
        self.inst.get_mut(&loc).unwrap()
    }
    fn book_add(&mut self, loc: u16, i: usize) {
        let (r, side, price, vis) = {
            let o = &self.pool[i];
            (o.reference, o.side, o.price, o.visible)
        };
        let st = self.inst.get_mut(&loc).unwrap();
        assert!(st.book.orders.insert(r, i).is_none(), "duplicate reference");
        let lv = st.book.side_map(side).entry(price).or_default();
        if vis {
            lv.vis.push_back(i);
        } else {
            lv.hid.push_back(i);
        }
    }
    fn book_remove(&mut self, loc: u16, r: u64) -> usize {
        let st = self.inst.get_mut(&loc).unwrap();
        let i = st.book.orders.remove(&r).expect("remove: unknown reference");
        let (side, price, vis) = {
            let o = &self.pool[i];
            (o.side, o.price, o.visible)
        };
        let st = self.inst.get_mut(&loc).unwrap();
        let m = st.book.side_map(side);
        let lv = m.get_mut(&price).unwrap();
        let q = if vis { &mut lv.vis } else { &mut lv.hid };
        let pos = q.iter().position(|&x| x == i).unwrap();
        q.remove(pos);
        if lv.vis.is_empty() && lv.hid.is_empty() {
            m.remove(&price);
        }
        i
    }
    fn book_reduce(&mut self, loc: u16, r: u64, q: i64) {
        let i = self.inst[&loc].book.orders[&r];
        assert!(q > 0 && q <= self.pool[i].qty, "reduce: bad quantity");
        self.pool[i].qty -= q;
        if self.pool[i].qty == 0 {
            self.book_remove(loc, r);
        }
    }
    fn erase(v: &mut Vec<usize>, i: usize) {
        if let Some(p) = v.iter().position(|&x| x == i) {
            v.remove(p);
        }
    }

    fn done(&mut self, i: usize) {
        self.pool[i].place = Where::None;
        let (session, cl, loc) = (self.pool[i].session, self.pool[i].cl, self.pool[i].locate);
        let live = &mut self.sessions.get_mut(&session).unwrap().live;
        if live.get(&cl) == Some(&i) {
            live.remove(&cl);
        }
        Self::erase(&mut self.st(loc).pegs, i);
    }
    fn remove_from_container(&mut self, loc: u16, i: usize) {
        match self.pool[i].place {
            Where::Book => {
                let r = self.pool[i].reference;
                self.book_remove(loc, r);
                self.st(loc).pegged.remove(&r);
                if self.pool[i].visible {
                    self.feed_d(loc, r);
                }
            }
            Where::Stop => Self::erase(&mut self.st(loc).stops, i),
            Where::Mkt => Self::erase(&mut self.st(loc).mkt, i),
            Where::Close => Self::erase(&mut self.st(loc).close, i),
            _ => {}
        }
        self.pool[i].place = Where::None;
    }
    fn cancel(&mut self, i: usize, reason: u8) {
        let loc = self.pool[i].locate;
        let d = self.pool[i].remaining();
        self.remove_from_container(loc, i);
        let (s, cl) = (self.pool[i].session, self.pool[i].cl);
        self.rep_c(s, cl, d, reason);
        self.done(i);
        self.touched.insert(loc);
    }
    fn decrement(&mut self, i: usize, d: i64, reason: u8) {
        let loc = self.pool[i].locate;
        if d >= self.pool[i].remaining() {
            self.cancel(i, reason);
            return;
        }
        let from_res = self.pool[i].reserve.min(d);
        self.pool[i].reserve -= from_res;
        let shown = d - from_res;
        if shown != 0 {
            if self.pool[i].place == Where::Book {
                let r = self.pool[i].reference;
                self.book_reduce(loc, r, shown);
                if self.pool[i].visible {
                    self.feed_x(loc, r, shown);
                }
            } else {
                self.pool[i].qty -= shown;
            }
        }
        let (s, cl) = (self.pool[i].session, self.pool[i].cl);
        self.rep_c(s, cl, d, reason);
        self.touched.insert(loc);
    }
    fn slice(&self, i: usize, rem: i64) -> (i64, i64) {
        let o = &self.pool[i];
        if o.visible && o.display_qty != 0 {
            let shown = o.display_qty.min(rem);
            (shown, rem - shown)
        } else {
            (rem, 0)
        }
    }
    fn rest(&mut self, loc: u16, i: usize, rem: i64) {
        let (shown, reserve) = self.slice(i, rem);
        self.pool[i].qty = shown;
        self.pool[i].reserve = reserve;
        let best = self.inst[&loc].book.best(self.pool[i].side);
        let (side, price) = (self.pool[i].side, self.pool[i].price);
        self.pool[i].top = match best {
            None => true,
            Some(b) => {
                if side == 1 {
                    price > b
                } else {
                    price < b
                }
            }
        };
        self.book_add(loc, i);
        self.pool[i].place = Where::Book;
        if matches!(self.pool[i].display, b'M' | b'P') {
            let r = self.pool[i].reference;
            self.st(loc).pegged.insert(r);
        }
        if self.pool[i].visible {
            self.feed_a(loc, i, shown, price);
        }
    }
    fn would_cross(&self, loc: u16, side: i32, lim: i64) -> bool {
        self.inst[&loc]
            .book
            .best(-side)
            .is_some_and(|p| marketable(side, lim, p))
    }
    fn stp_conflict(&self, a: usize, b: usize) -> bool {
        let (x, y) = (&self.pool[a], &self.pool[b]);
        x.stp_group != 0 && x.stp_group == y.stp_group && x.firm == y.firm
    }
    fn peg_target(&self, loc: u16, i: usize) -> Option<i64> {
        let st = &self.inst[&loc];
        let o = &self.pool[i];
        let mut p = if o.display == b'M' {
            let (b, a) = match st.ref_quote {
                Some(q) => q,
                None => (st.book.best_visible(1)?, st.book.best_visible(-1)?),
            };
            (b + a).div_euclid(2)
        } else {
            let mut found = None;
            for px in st.book.prices(o.side) {
                let any = st
                    .book
                    .level_orders(o.side, px)
                    .iter()
                    .any(|&x| self.pool[x].visible && !st.pegged.contains(&self.pool[x].reference));
                if any {
                    found = Some(px);
                    break;
                }
            }
            found?
        };
        if o.limit != 0 {
            p = if o.side == 1 { p.min(o.limit) } else { p.max(o.limit) };
        }
        Some(p)
    }

    // -- matching -----------------------------------------------------------------------------------------------
    fn in_band(&self, loc: u16, p: i64) -> bool {
        let st = &self.inst[&loc];
        st.band_hi == 0 || (st.band_lo <= p && p <= st.band_hi)
    }
    fn eligible(&self, loc: u16, i: usize, lim: i64, rem: i64) -> i64 {
        let side = self.pool[i].side;
        let st = &self.inst[&loc];
        let mut total = 0;
        for p in st.book.prices(-side) {
            if !marketable(side, lim, p) || !self.in_band(loc, p) {
                break;
            }
            for r in st.book.level_orders(-side, p) {
                if self.stp_conflict(i, r) || (self.pool[r].min_qty != 0 && rem < self.pool[r].min_qty) {
                    continue;
                }
                total += self.pool[r].remaining();
            }
        }
        total
    }
    fn execute(&mut self, loc: u16, r: usize, o: usize, q: i64, p: i64, rem_after: i64) {
        self.next_match += 1;
        let m = self.next_match;
        let rr = self.pool[r].reference;
        if self.pool[r].visible {
            let e = Feed {
                reference: rr,
                shares: q as u64,
                matched: m,
                ..self.fbase(b'E', loc)
            };
            self.feed.push(e);
        } else {
            let x = Feed {
                reference: 0,
                side: if self.pool[r].side == 1 { b'B' } else { b'S' },
                shares: q as u64,
                stock: self.inst[&loc].symbol,
                price: p as u32,
                matched: m,
                ..self.fbase(b'P', loc)
            };
            self.feed.push(x);
        }
        self.book_reduce(loc, rr, q);
        if self.pool[r].qty == 0 {
            self.st(loc).pegged.remove(&rr);
            if self.pool[r].reserve > 0 {
                let shown = self.pool[r].display_qty.min(self.pool[r].reserve);
                self.pool[r].reserve -= shown;
                self.pool[r].qty = shown;
                self.pool[r].reference = self.new_ref();
                self.pool[r].seq = self.next_seq();
                self.pool[r].top = false;
                self.book_add(loc, r);
                let price = self.pool[r].price;
                self.feed_a(loc, r, shown, price);
            } else {
                self.pool[r].place = Where::None;
            }
        }
        let (rs, rcl, rrem) = (self.pool[r].session, self.pool[r].cl, self.pool[r].remaining());
        let f = self.fee(b'A', p, q);
        self.rep_e(rs, rcl, q, p, m, b'A', f, rrem);
        if rrem == 0 {
            self.done(r);
        }
        let (os, ocl) = (self.pool[o].session, self.pool[o].cl);
        let f = self.fee(b'R', p, q);
        self.rep_e(os, ocl, q, p, m, b'R', f, rem_after);
        self.st(loc).last = p;
        self.trades.push(Trade {
            matched: m,
            locate: loc,
            price: p,
            qty: q,
        });
    }
    fn do_match(&mut self, loc: u16, o: usize, lim: i64, mut rem: i64) -> i64 {
        let side = self.pool[o].side;
        let opp = -side;
        for p in self.inst[&loc].book.prices(opp) {
            if rem == 0 || !marketable(side, lim, p) || !self.in_band(loc, p) {
                break;
            }
            while rem > 0 {
                let level = self.inst[&loc].book.level_orders(opp, p);
                if level.is_empty() {
                    break;
                }
                let mut elig = Vec::new();
                for &r in &level {
                    if self.stp_conflict(o, r) && self.pool[o].stp_mode != b'N' {
                        let (cr, ci, dec) = stp_actions(self.pool[o].stp_mode);
                        let (os, ocl) = (self.pool[o].session, self.pool[o].cl);
                        if dec {
                            let d = rem.min(self.pool[r].remaining());
                            self.decrement(r, d, b'S');
                            rem -= d;
                            self.rep_c(os, ocl, d, b'S');
                            if rem == 0 {
                                return 0;
                            }
                            continue;
                        }
                        if cr {
                            self.cancel(r, b'S');
                        }
                        if ci {
                            self.rep_c(os, ocl, rem, b'S');
                            return -1;
                        }
                        continue;
                    }
                    if self.pool[r].min_qty != 0 && rem < self.pool[r].min_qty {
                        continue;
                    }
                    elig.push(r);
                }
                if elig.is_empty() {
                    if self.inst[&loc].book.level_orders(opp, p).len() == level.len() {
                        break;
                    }
                    continue;
                }
                let st = &self.inst[&loc];
                let alloc = if st.matching == b'F' {
                    let mut a = vec![0i64; elig.len()];
                    let mut left = rem;
                    for (k, &r) in elig.iter().enumerate() {
                        a[k] = self.pool[r].qty.min(left);
                        left -= a[k];
                        if left == 0 {
                            break;
                        }
                    }
                    a
                } else {
                    let bk: Vec<(i64, bool)> = elig.iter().map(|&r| (self.pool[r].qty, self.pool[r].top)).collect();
                    configurable(&bk, rem, st.top_pct, st.fifo_pct, st.min_alloc)
                };
                for (k, &r) in elig.iter().enumerate() {
                    if alloc[k] > 0 {
                        rem -= alloc[k];
                        self.execute(loc, r, o, alloc[k], p, rem);
                    }
                }
            }
        }
        rem
    }
    fn incoming(&mut self, loc: u16, o: usize, lim: i64, rem: i64) {
        let tif = self.pool[o].tif;
        let need = if tif == b'F' { rem } else { self.pool[o].min_qty };
        if need != 0 && self.eligible(loc, o, lim, rem) < need {
            if tif == b'I' || tif == b'F' {
                let (s, cl) = (self.pool[o].session, self.pool[o].cl);
                self.rep_c(s, cl, rem, b'I');
                self.done(o);
            } else {
                self.pool[o].price = lim;
                self.rest(loc, o, rem);
            }
            return;
        }
        let rem = self.do_match(loc, o, lim, rem);
        if rem <= 0 {
            if rem == 0 {
                self.pool[o].qty = 0;
                self.pool[o].reserve = 0;
            }
            self.done(o);
            return;
        }
        if lim == 0 || tif == b'I' || tif == b'F' {
            let (s, cl) = (self.pool[o].session, self.pool[o].cl);
            self.rep_c(s, cl, rem, b'I');
            self.done(o);
            return;
        }
        self.pool[o].price = lim;
        self.rest(loc, o, rem);
    }

    // -- order entry --------------------------------------------------------------------------------------------
    fn validate(&self, m: &In, loc: u16) -> u8 {
        let st = &self.inst[&loc];
        let (qty, dq) = (i64::from(m.qty), i64::from(m.display_qty));
        if st.phase == b'C' || st.phase == b'H' {
            return b'H';
        }
        if qty <= 0 || qty > MAX_QTY || dq > qty {
            return b'Q';
        }
        if !b"BS".contains(&m.side)
            || !b"DGIFOC".contains(&m.tif)
            || !b"YNMP".contains(&m.display)
            || !b"NOWBD".contains(&m.stp_mode)
        {
            return b'Q';
        }
        if m.min_qty != 0 && !(m.tif == b'I' || m.display == b'M') {
            return b'Q';
        }
        if m.display_qty != 0 && m.display != b'Y' {
            return b'Q';
        }
        if i64::from(m.price) % st.tick != 0 || i64::from(m.stop_price) % st.tick != 0 {
            return b'X';
        }
        if m.tif == b'O' && st.phase != b'O' {
            return b'H';
        }
        if m.tif == b'C' && (st.frozen || !b"TKO".contains(&st.phase)) {
            return if st.frozen { b'C' } else { b'H' };
        }
        let p = i64::from(m.price);
        if p != 0 && st.band_hi != 0 && !(st.band_lo <= p && p <= st.band_hi) {
            return b'B';
        }
        0
    }
    fn accept(&mut self, session: u16, m: &In) -> usize {
        let r = self.new_ref();
        let seq = self.next_seq();
        let firm = self.sessions[&session].firm;
        self.pool.push(Order {
            reference: r,
            side: if m.side == b'B' { 1 } else { -1 },
            price: i64::from(m.price),
            qty: i64::from(m.qty),
            visible: m.display == b'Y' || m.display == b'P',
            seq,
            session,
            cl: m.cl_ord_id,
            firm,
            locate: m.locate,
            tif: m.tif,
            display: m.display,
            post_only: m.post_only == b'Y',
            display_qty: i64::from(m.display_qty),
            reserve: 0,
            min_qty: i64::from(m.min_qty),
            stp_group: m.stp_group,
            stp_mode: m.stp_mode,
            stop_price: i64::from(m.stop_price),
            limit: i64::from(m.price),
            place: Where::None,
            top: false,
        });
        let i = self.pool.len() - 1;
        let s = self.sessions.get_mut(&session).unwrap();
        s.used.insert(m.cl_ord_id);
        s.live.insert(m.cl_ord_id, i);
        let a = Out {
            kind: b'A',
            ts: self.ts,
            cl_ord_id: m.cl_ord_id,
            reference: r,
            locate: m.locate,
            side: m.side,
            qty: m.qty,
            price: m.price,
            tif: m.tif,
            display: m.display,
            state: if m.stop_price != 0 { b'S' } else { b'L' },
            ..Out::default()
        };
        self.rep(session, a);
        i
    }
    fn enter(&mut self, session: u16, m: &In) {
        if !self.inst.contains_key(&m.locate) {
            self.rej(session, m.cl_ord_id, b'S');
            return;
        }
        let loc = m.locate;
        if self.sessions[&session].used.contains(&m.cl_ord_id) {
            self.rej(session, m.cl_ord_id, b'D');
            return;
        }
        let mut why = self.validate(m, loc);
        if why == 0
            && m.post_only == b'Y'
            && self.inst[&loc].phase == b'T'
            && m.stop_price == 0
            && (m.display == b'Y' || m.display == b'N')
            && self.would_cross(loc, if m.side == b'B' { 1 } else { -1 }, i64::from(m.price))
        {
            why = b'O';
        }
        if why != 0 {
            self.rej(session, m.cl_ord_id, why);
            return;
        }
        self.touched.insert(loc);
        let o = self.accept(session, m);
        if m.stop_price != 0 {
            self.pool[o].place = Where::Stop;
            self.st(loc).stops.push(o);
            return;
        }
        if m.tif == b'C' {
            self.pool[o].place = Where::Close;
            self.st(loc).close.push(o);
            return;
        }
        if m.display == b'M' || m.display == b'P' {
            self.st(loc).pegs.push(o);
            self.pool[o].place = Where::Peg;
            return;
        }
        if is_call(self.inst[&loc].phase) {
            self.park_in_call(loc, o);
            return;
        }
        let (lim, q) = (self.pool[o].limit, self.pool[o].qty);
        self.incoming(loc, o, lim, q);
    }
    fn park_in_call(&mut self, loc: u16, o: usize) {
        let tif = self.pool[o].tif;
        if tif == b'I' || tif == b'F' {
            let (s, cl, rem) = (self.pool[o].session, self.pool[o].cl, self.pool[o].remaining());
            self.rep_c(s, cl, rem, b'I');
            self.done(o);
        } else if self.pool[o].limit == 0 {
            self.pool[o].place = Where::Mkt;
            self.st(loc).mkt.push(o);
        } else {
            self.pool[o].price = self.pool[o].limit;
            let rem = self.pool[o].remaining();
            self.rest(loc, o, rem);
        }
    }
    fn inbound(&mut self, session: u16, m: &In) {
        match m.kind {
            b'O' => self.enter(session, m),
            b'X' => self.in_cancel(session, m),
            b'M' => self.in_mass(session, m),
            b'U' => self.in_replace(session, m),
            b'Q' => self.in_quote(session, m),
            _ => {}
        }
    }
    fn in_cancel(&mut self, session: u16, m: &In) {
        let Some(&o) = self.sessions[&session].live.get(&m.cl_ord_id) else {
            self.rej(session, m.cl_ord_id, b'L');
            return;
        };
        let rem = self.pool[o].remaining();
        if i64::from(m.leave_qty) >= rem {
            return;
        }
        if m.leave_qty == 0 {
            self.cancel(o, b'U');
        } else {
            self.decrement(o, rem - i64::from(m.leave_qty), b'U');
        }
    }
    fn by_seq(&self, live: &HashMap<u64, usize>) -> Vec<usize> {
        let mut v: Vec<usize> = live.values().copied().collect();
        v.sort_by_key(|&i| self.pool[i].seq);
        v
    }
    fn in_mass(&mut self, session: u16, m: &In) {
        let side = match m.side {
            b'B' => 1,
            b'S' => -1,
            _ => 0,
        };
        for o in self.by_seq(&self.sessions[&session].live) {
            let (loc, s) = (self.pool[o].locate, self.pool[o].side);
            if (m.locate == 0 || loc == m.locate) && (side == 0 || s == side) {
                self.cancel(o, b'M');
            }
        }
    }
    fn in_replace(&mut self, session: u16, m: &In) {
        let Some(&o) = self.sessions[&session].live.get(&m.cl_ord_id) else {
            self.rej(session, m.cl_ord_id, b'L');
            return;
        };
        let loc = self.pool[o].locate;
        if self.sessions[&session].used.contains(&m.new_cl_ord_id) {
            self.rej(session, m.new_cl_ord_id, b'D');
            return;
        }
        let (price, qty) = (i64::from(m.price), i64::from(m.qty));
        let st = &self.inst[&loc];
        let oo = &self.pool[o];
        let why = if st.phase == b'C' || st.phase == b'H' {
            b'H'
        } else if qty <= 0 || qty > MAX_QTY {
            b'Q'
        } else if price % st.tick != 0 || ((price == 0) != (oo.limit == 0)) {
            b'X'
        } else if price != 0 && st.band_hi != 0 && !(st.band_lo <= price && price <= st.band_hi) {
            b'B'
        } else if oo.post_only
            && st.phase == b'T'
            && oo.place == Where::Book
            && oo.display != b'M'
            && oo.display != b'P'
            && price != oo.limit
            && self.would_cross(loc, oo.side, price)
        {
            b'O'
        } else {
            0
        };
        if why != 0 {
            self.rej(session, m.new_cl_ord_id, why);
            return;
        }
        self.touched.insert(loc);
        let old_cl = self.pool[o].cl;
        {
            let s = self.sessions.get_mut(&session).unwrap();
            s.used.insert(m.new_cl_ord_id);
            s.live.remove(&old_cl);
            s.live.insert(m.new_cl_ord_id, o);
        }
        self.pool[o].cl = m.new_cl_ord_id;
        let mut u = Out {
            kind: b'U',
            ts: self.ts,
            cl_ord_id: old_cl,
            new_cl_ord_id: m.new_cl_ord_id,
            qty: m.qty,
            price: m.price,
            ..Out::default()
        };
        if price == self.pool[o].limit && qty <= self.pool[o].remaining() && self.pool[o].place != Where::None {
            let d = self.pool[o].remaining() - qty;
            if d != 0 {
                let from_res = self.pool[o].reserve.min(d);
                self.pool[o].reserve -= from_res;
                let shown = d - from_res;
                if shown != 0 {
                    if self.pool[o].place == Where::Book {
                        let r = self.pool[o].reference;
                        self.book_reduce(loc, r, shown);
                        if self.pool[o].visible {
                            self.feed_x(loc, r, shown);
                        }
                    } else {
                        self.pool[o].qty -= shown;
                    }
                }
            }
            u.reference = self.pool[o].reference;
            u.priority = b'Y';
            self.rep(session, u);
            return;
        }
        let was_book = self.pool[o].place == Where::Book;
        let vis = self.pool[o].visible;
        let old_ref = self.pool[o].reference;
        if was_book {
            self.book_remove(loc, old_ref);
            self.st(loc).pegged.remove(&old_ref);
            self.pool[o].place = Where::None;
        }
        self.pool[o].limit = price;
        self.pool[o].seq = self.next_seq();
        self.pool[o].qty = qty;
        self.pool[o].reserve = 0;
        if was_book {
            self.pool[o].reference = self.new_ref();
        }
        u.reference = self.pool[o].reference;
        u.priority = b'N';
        self.rep(session, u);
        if !was_book {
            return;
        }
        if self.pool[o].display == b'M' || self.pool[o].display == b'P' {
            if vis {
                self.feed_d(loc, old_ref);
            }
            self.pool[o].place = Where::Peg;
            return;
        }
        let side = self.pool[o].side;
        if self.inst[&loc].phase == b'T' && self.would_cross(loc, side, price) {
            if vis {
                self.feed_d(loc, old_ref);
            }
            self.incoming(loc, o, price, qty);
            return;
        }
        self.pool[o].price = price;
        let (shown, reserve) = self.slice(o, qty);
        self.pool[o].qty = shown;
        self.pool[o].reserve = reserve;
        self.pool[o].top = false;
        self.book_add(loc, o);
        self.pool[o].place = Where::Book;
        if vis {
            let nr = self.pool[o].reference;
            self.feed_u(loc, old_ref, nr, shown, price);
        }
    }
    fn in_quote(&mut self, session: u16, m: &In) {
        if !self.inst.contains_key(&m.locate) {
            self.rej(session, m.quote_id.wrapping_mul(2), b'S');
            return;
        }
        if let Some(ids) = self.sessions.get_mut(&session).unwrap().quotes.remove(&m.locate) {
            for cl in ids {
                if let Some(&o) = self.sessions[&session].live.get(&cl) {
                    self.cancel(o, b'U');
                }
            }
        }
        let legs = [
            (m.quote_id.wrapping_mul(2), b'B', m.bid_price, m.bid_qty),
            (m.quote_id.wrapping_mul(2).wrapping_add(1), b'S', m.ask_price, m.ask_qty),
        ];
        let mut ids = Vec::new();
        for (cl, side, px, qty) in legs {
            if qty == 0 {
                continue;
            }
            ids.push(cl);
            let o = In {
                kind: b'O',
                cl_ord_id: cl,
                locate: m.locate,
                side,
                qty,
                price: px,
                ..In::default()
            };
            self.enter(session, &o);
        }
        self.sessions.get_mut(&session).unwrap().quotes.insert(m.locate, ids);
    }

    // -- settle -------------------------------------------------------------------------------------------------
    fn settle(&mut self, loc: u16) {
        let mut stuck = false;
        for _ in 0..64 {
            let mut changed = false;
            if self.inst[&loc].phase == b'T' {
                let last = self.inst[&loc].last;
                let trig: Vec<usize> = self.inst[&loc]
                    .stops
                    .iter()
                    .copied()
                    .filter(|&i| {
                        let o = &self.pool[i];
                        last > 0
                            && if o.side == 1 {
                                last >= o.stop_price
                            } else {
                                last <= o.stop_price
                            }
                    })
                    .collect();
                for o in trig {
                    if self.pool[o].place != Where::Stop {
                        continue;
                    }
                    Self::erase(&mut self.st(loc).stops, o);
                    self.pool[o].place = Where::None;
                    self.pool[o].stop_price = 0;
                    if matches!(self.pool[o].display, b'M' | b'P') {
                        self.st(loc).pegs.push(o);
                        self.pool[o].place = Where::Peg;
                    } else {
                        let (lim, q) = (self.pool[o].limit, self.pool[o].qty);
                        self.incoming(loc, o, lim, q);
                    }
                    changed = true;
                }
                let pegs = self.inst[&loc].pegs.clone();
                for o in pegs {
                    let place = self.pool[o].place;
                    if place != Where::Book && place != Where::Peg {
                        continue;
                    }
                    let target = self.peg_target(loc, o);
                    if place == Where::Book && target == Some(self.pool[o].price) {
                        continue;
                    }
                    if place == Where::Peg && target.is_none() {
                        continue;
                    }
                    changed = true;
                    let (old_ref, vis) = (self.pool[o].reference, self.pool[o].visible);
                    if place == Where::Book {
                        self.book_remove(loc, old_ref);
                        self.st(loc).pegged.remove(&old_ref);
                        let rem = self.pool[o].remaining();
                        self.pool[o].qty = rem;
                        self.pool[o].reserve = 0;
                        let Some(target) = target else {
                            self.pool[o].place = Where::Peg;
                            if vis {
                                self.feed_d(loc, old_ref);
                            }
                            continue;
                        };
                        self.pool[o].place = Where::None;
                        if self.would_cross(loc, self.pool[o].side, target) {
                            if vis {
                                self.feed_d(loc, old_ref);
                                self.pool[o].reference = self.new_ref();
                            }
                            self.incoming(loc, o, target, rem);
                            continue;
                        }
                        self.pool[o].price = target;
                        self.pool[o].top = false;
                        if vis {
                            self.pool[o].reference = self.new_ref();
                        }
                        self.book_add(loc, o);
                        let nr = self.pool[o].reference;
                        self.st(loc).pegged.insert(nr);
                        self.pool[o].place = Where::Book;
                        if vis {
                            let q = self.pool[o].qty;
                            self.feed_u(loc, old_ref, nr, q, target);
                        }
                    } else {
                        self.pool[o].place = Where::None;
                        let q = self.pool[o].qty;
                        self.incoming(loc, o, target.unwrap(), q);
                    }
                }
                let (b, a) = (self.inst[&loc].book.best(1), self.inst[&loc].book.best(-1));
                if let (Some(b), Some(a)) = (b, a) {
                    if b >= a && !stuck {
                        let before = self.trades.len();
                        let rb = self.inst[&loc].book.level_orders(1, b)[0];
                        let ra = self.inst[&loc].book.level_orders(-1, a)[0];
                        let agg = if self.pool[rb].seq > self.pool[ra].seq { rb } else { ra };
                        let rem = self.pool[agg].remaining();
                        let r = self.pool[agg].reference;
                        self.book_remove(loc, r);
                        self.st(loc).pegged.remove(&r);
                        if self.pool[agg].visible {
                            self.feed_d(loc, r);
                            self.pool[agg].reference = self.new_ref();
                        }
                        self.pool[agg].qty = rem;
                        self.pool[agg].reserve = 0;
                        self.pool[agg].place = Where::None;
                        let price = self.pool[agg].price;
                        self.incoming(loc, agg, price, rem);
                        if self.trades.len() == before {
                            stuck = true;
                        }
                        changed = true;
                    }
                }
            }
            if !changed {
                return;
            }
        }
        panic!("settle did not converge");
    }

    // -- auctions -----------------------------------------------------------------------------------------------
    fn auction_orders(&self, loc: u16, cross_type: u8) -> Vec<usize> {
        let st = &self.inst[&loc];
        let mut out = Vec::new();
        for side in [1, -1] {
            for p in st.book.prices(side) {
                for i in st.book.level_orders(side, p) {
                    if !matches!(self.pool[i].display, b'M' | b'P') {
                        out.push(i);
                    }
                }
            }
        }
        out.extend(st.mkt.iter().copied());
        if cross_type == b'C' {
            out.extend(st.close.iter().copied());
        }
        out
    }
    fn uncross_calc(&self, loc: u16, cross_type: u8) -> (Vec<usize>, Uncrossing) {
        let orders = self.auction_orders(loc, cross_type);
        let ao: Vec<(i32, i64, Option<i64>, u64)> = orders
            .iter()
            .map(|&i| {
                let o = &self.pool[i];
                (
                    o.side,
                    o.remaining(),
                    if o.limit != 0 { Some(o.limit) } else { None },
                    o.seq,
                )
            })
            .collect();
        let st = &self.inst[&loc];
        let reference = if st.ref_price != 0 { st.ref_price } else { st.last };
        (orders, uncross(&ao, reference))
    }
    fn do_uncross(&mut self, loc: u16, cross_type: u8) {
        let (orders, u) = self.uncross_calc(loc, cross_type);
        self.touched.insert(loc);
        if u.volume > 0 {
            self.next_match += 1;
            let m = self.next_match;
            let p = u.price.unwrap();
            for &(idx, q) in &u.fills {
                let o = orders[idx];
                if self.pool[o].place == Where::Book {
                    let shown = q.min(self.pool[o].qty);
                    let r = self.pool[o].reference;
                    if self.pool[o].visible {
                        let c = Feed {
                            reference: r,
                            shares: shown as u64,
                            matched: m,
                            printable: b'N',
                            price: p as u32,
                            ..self.fbase(b'C', loc)
                        };
                        self.feed.push(c);
                    }
                    self.book_reduce(loc, r, shown);
                    self.pool[o].reserve -= q - shown;
                    if self.pool[o].qty == 0 && self.pool[o].reserve > 0 {
                        let s2 = self.pool[o].display_qty.min(self.pool[o].reserve);
                        self.pool[o].reserve -= s2;
                        self.pool[o].qty = s2;
                        self.pool[o].reference = self.new_ref();
                        self.pool[o].seq = self.next_seq();
                        self.pool[o].top = false;
                        self.book_add(loc, o);
                        let price = self.pool[o].price;
                        self.feed_a(loc, o, s2, price);
                    } else if self.pool[o].qty == 0 {
                        self.pool[o].place = Where::None;
                    }
                } else {
                    self.pool[o].qty -= q;
                    if self.pool[o].qty == 0 {
                        if self.pool[o].place == Where::Mkt {
                            Self::erase(&mut self.st(loc).mkt, o);
                        } else {
                            Self::erase(&mut self.st(loc).close, o);
                        }
                        self.pool[o].place = Where::None;
                    }
                }
                let (s, cl, rem) = (self.pool[o].session, self.pool[o].cl, self.pool[o].remaining());
                let f = self.fee(b'C', p, q);
                self.rep_e(s, cl, q, p, m, b'C', f, rem);
                if rem == 0 {
                    self.done(o);
                }
                self.trades.push(Trade {
                    matched: m,
                    locate: loc,
                    price: p,
                    qty: q,
                });
            }
            let x = Feed {
                shares: u.volume as u64,
                stock: self.inst[&loc].symbol,
                price: p as u32,
                matched: m,
                cross_type,
                ..self.fbase(b'Q', loc)
            };
            self.feed.push(x);
            let st = self.st(loc);
            st.last = p;
            st.ref_price = p;
        }
        let st = &self.inst[&loc];
        let mut left: Vec<usize> = st.mkt.clone();
        if cross_type == b'O' {
            for side in [1, -1] {
                for px in st.book.prices(side) {
                    for i in st.book.level_orders(side, px) {
                        if self.pool[i].tif == b'O' {
                            left.push(i);
                        }
                    }
                }
            }
        }
        if cross_type == b'C' {
            left.extend(st.close.iter().copied());
        }
        left.sort_by_key(|&i| self.pool[i].seq);
        for o in left {
            let place = self.pool[o].place;
            if place != Where::None {
                self.cancel(o, if place == Where::Mkt { b'I' } else { b'E' });
            }
        }
    }

    // -- control ------------------------------------------------------------------------------------------------
    fn scope(&self, locate: u16) -> Vec<u16> {
        if locate == 0 {
            self.inst.keys().copied().collect()
        } else {
            vec![locate]
        }
    }
    fn control(&mut self, m: &Ctl) {
        match m.kind {
            b'L' => {
                let burst = self.burst;
                let s = self.sessions.entry(m.session).or_insert_with(|| Sess {
                    firm: m.firm,
                    cod: m.cod == b'Y',
                    logged: true,
                    tokens: burst * NANO,
                    last_t: None,
                    used: HashSet::new(),
                    live: HashMap::new(),
                    quotes: BTreeMap::new(),
                });
                s.logged = true;
                s.cod = m.cod == b'Y';
            }
            b'D' => {
                if let Some(s) = self.sessions.get_mut(&m.session) {
                    s.logged = false;
                    if s.cod {
                        let live = s.live.clone();
                        for o in self.by_seq(&live) {
                            self.cancel(o, b'D');
                        }
                    }
                }
            }
            b'P' => {
                for loc in self.scope(m.locate) {
                    let old = self.inst[&loc].phase;
                    self.st(loc).phase = m.phase;
                    let h = Feed {
                        stock: self.inst[&loc].symbol,
                        state: state_of(m.phase),
                        reserved: b' ',
                        reason: m.reason,
                        ..self.fbase(b'H', loc)
                    };
                    self.feed.push(h);
                    self.touched.insert(loc);
                    if is_call(old) && (m.phase == b'T' || m.phase == b'C') && old != m.phase {
                        let ct = match old {
                            b'O' => b'O',
                            b'K' => b'C',
                            b'U' => b'H',
                            _ => b'B',
                        };
                        self.do_uncross(loc, ct);
                    } else if old == b'T' && m.phase == b'C' {
                        self.do_uncross(loc, b'C');
                    }
                }
            }
            b'X' => {
                for loc in self.scope(m.locate) {
                    self.do_uncross(loc, m.cross_type);
                }
            }
            b'I' => {
                for loc in self.scope(m.locate) {
                    let (_, u) = self.uncross_calc(loc, m.cross_type);
                    let p = if u.volume == 0 { 0 } else { u.price.unwrap() };
                    let x = Feed {
                        paired: u.volume as u64,
                        imbalance: u.surplus.unsigned_abs(),
                        direction: if u.volume == 0 {
                            b'O'
                        } else if u.surplus > 0 {
                            b'B'
                        } else if u.surplus < 0 {
                            b'S'
                        } else {
                            b'N'
                        },
                        stock: self.inst[&loc].symbol,
                        far: p as u32,
                        near: p as u32,
                        ref_price: self.inst[&loc].ref_price as u32,
                        cross_type: m.cross_type,
                        variation: b' ',
                        ..self.fbase(b'I', loc)
                    };
                    self.feed.push(x);
                }
            }
            b'R' => {
                let st = self.st(m.locate);
                st.ref_price = i64::from(m.ref_price);
                st.band_lo = i64::from(m.band_lo);
                st.band_hi = i64::from(m.band_hi);
            }
            b'N' => {
                let st = self.st(m.locate);
                st.ref_quote = if m.bid > 0 && m.ask > 0 {
                    Some((i64::from(m.bid), i64::from(m.ask)))
                } else {
                    None
                };
                self.touched.insert(m.locate);
            }
            b'E' => {
                let mut v: Vec<usize> = Vec::new();
                for s in self.sessions.values() {
                    for &o in s.live.values() {
                        let oo = &self.pool[o];
                        if (m.locate == 0 || oo.locate == m.locate) && (m.tif == b'A' || oo.tif != b'G') {
                            v.push(o);
                        }
                    }
                }
                v.sort_by_key(|&i| self.pool[i].seq);
                for o in v {
                    self.cancel(o, b'E');
                }
            }
            b'F' => {
                for loc in self.scope(m.locate) {
                    self.st(loc).frozen = m.freeze == b'Y';
                }
            }
            b'S' => {
                let s = Feed {
                    event: m.event,
                    ..self.fbase(b'S', 0)
                };
                self.feed.push(s);
                if m.event == b'O' {
                    for loc in self.scope(0) {
                        let st = &self.inst[&loc];
                        let r = Feed {
                            stock: st.symbol,
                            tick: st.tick as u32,
                            lot: st.lot as u32,
                            matching: st.matching,
                            ..self.fbase(b'R', loc)
                        };
                        self.feed.push(r);
                    }
                }
                let ids: Vec<u16> = self
                    .sessions
                    .iter()
                    .filter(|(_, s)| s.logged)
                    .map(|(k, _)| *k)
                    .collect();
                for sid in ids {
                    let o = Out {
                        kind: b'S',
                        ts: self.ts,
                        event: m.event,
                        ..Out::default()
                    };
                    self.rep(sid, o);
                }
            }
            _ => {}
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::codec::{be_get, be_put, journal_records};
    use std::fs;

    fn data(f: &str) -> Vec<u8> {
        fs::read(format!("{}/../data/{f}", env!("CARGO_MANIFEST_DIR"))).unwrap()
    }

    #[test]
    fn fixture_is_byte_identical_to_python() {
        let cfg = crate::json::parse(&String::from_utf8(data("fixture_config.json")).unwrap()).unwrap();
        let mut e = Engine::new(&cfg);
        let journal = data("fixture_journal.bin");
        let want = data("fixture_out.bin");
        let mut out = Vec::new();
        let mut feed_n = 0u64;
        for (idx, (t, s, p)) in journal_records(&journal).unwrap().into_iter().enumerate() {
            e.process(t, s, p);
            let start = out.len();
            be_put(&mut out, idx as u64, 4);
            be_put(&mut out, e.feed.len() as u64, 2);
            be_put(&mut out, e.reports.len() as u64, 2);
            for m in &e.feed {
                let mut b = Vec::new();
                m.encode(&mut b);
                be_put(&mut out, b.len() as u64, 2);
                out.extend_from_slice(&b);
            }
            for (sess, m) in &e.reports {
                let mut b = Vec::new();
                m.encode(&mut b);
                be_put(&mut out, u64::from(*sess), 2);
                be_put(&mut out, b.len() as u64, 2);
                out.extend_from_slice(&b);
            }
            feed_n += e.feed.len() as u64;
            assert!(
                out.len() <= want.len() && out[start..] == want[start..out.len()],
                "record {idx} differs"
            );
        }
        for loc in e.locates() {
            let snap = e.snapshot(loc, feed_n, e.ts);
            be_put(&mut out, 0xFFFF_FFFF, 4);
            be_put(&mut out, u64::from(loc), 2);
            be_put(&mut out, snap.len() as u64, 2);
            for m in &snap {
                let mut b = Vec::new();
                m.encode(&mut b);
                be_put(&mut out, b.len() as u64, 2);
                out.extend_from_slice(&b);
            }
        }
        assert_eq!(out, want);
        assert!(!e.trades.is_empty());
    }

    #[test]
    fn golden_messages_round_trip() {
        for (file, kind) in [("feed.bin", 0), ("in.bin", 1), ("out.bin", 2), ("ctl.bin", 3)] {
            let b = data(&format!("golden/{file}"));
            let mut i = 0;
            let mut n = 0;
            while i < b.len() {
                let len = be_get(&b, i, 2) as usize;
                let s = &b[i + 2..i + 2 + len];
                let mut again = Vec::new();
                match kind {
                    0 => Feed::decode(s).unwrap().encode(&mut again),
                    1 => In::decode(s).unwrap().encode(&mut again),
                    2 => Out::decode(s).unwrap().encode(&mut again),
                    _ => Ctl::decode(s).unwrap().encode(&mut again),
                }
                assert_eq!(again, s, "{file} at {i}");
                i += 2 + len;
                n += 1;
            }
            assert!(n > 10);
        }
    }
}
