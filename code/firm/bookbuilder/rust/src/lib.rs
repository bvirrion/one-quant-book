//! firm.bookbuilder -- the ladder book in Rust (build of One Quant Book 13, chapter 19), the twin of the C++20 header:
//! an open-addressing order map with backward-shift deletion, a dense ladder around the touch with recentring and a
//! sparse fallback, and the same level-2 hash after every event of the shared fixtures.

use std::collections::BTreeMap;

/// The feed handler's normalised event (the 48-byte record's fields).
#[derive(Clone, Copy, Debug, Default)]
pub struct Event {
    pub kind: u8,
    pub side: u8,
    pub seq: u64,
    pub r#ref: u64,
    pub ref2: u64,
    pub price: u32,
    pub qty: u64,
}

impl Event {
    pub fn from_record(b: &[u8]) -> Event {
        let u = |o: usize| u64::from_le_bytes(b[o..o + 8].try_into().unwrap());
        Event {
            kind: b[0],
            side: b[1],
            seq: u(4),
            r#ref: u(20),
            ref2: u(28),
            price: u32::from_le_bytes(b[36..40].try_into().unwrap()),
            qty: u(40),
        }
    }
}

pub struct OrderMap {
    keys: Vec<u64>,
    vals: Vec<u32>,
    mask: usize,
}

impl OrderMap {
    pub fn new(capacity_pow2: usize) -> Self {
        OrderMap { keys: vec![0; capacity_pow2], vals: vec![0; capacity_pow2], mask: capacity_pow2 - 1 }
    }
    fn slot(&self, r: u64) -> usize {
        ((r.wrapping_mul(0x9E3779B97F4A7C15)) >> 20) as usize & self.mask
    }
    pub fn find(&self, r: u64) -> Option<u32> {
        let mut i = self.slot(r);
        loop {
            if self.keys[i] == r {
                return Some(self.vals[i]);
            }
            if self.keys[i] == 0 {
                return None;
            }
            i = (i + 1) & self.mask;
        }
    }
    pub fn insert(&mut self, r: u64, v: u32) {
        let mut i = self.slot(r);
        while self.keys[i] != 0 && self.keys[i] != r {
            i = (i + 1) & self.mask;
        }
        self.keys[i] = r;
        self.vals[i] = v;
    }
    pub fn erase(&mut self, r: u64) {
        let mut i = self.slot(r);
        while self.keys[i] != r {
            if self.keys[i] == 0 {
                return;
            }
            i = (i + 1) & self.mask;
        }
        let mut j = (i + 1) & self.mask;
        while self.keys[j] != 0 {
            let home = self.slot(self.keys[j]);
            if (j.wrapping_sub(home) & self.mask) >= (j.wrapping_sub(i) & self.mask) {
                self.keys[i] = self.keys[j];
                self.vals[i] = self.vals[j];
                i = j;
            }
            j = (j + 1) & self.mask;
        }
        self.keys[i] = 0;
    }
}

#[derive(Clone, Copy, Default)]
struct Order {
    price: u32,
    qty: u64,
    side: u8,
    live: bool,
}

pub const BID: u8 = b'B';
pub const ASK: u8 = b'S';

pub struct LadderBook {
    tick: i64,
    w: i64,
    base: i64,
    centred: bool,
    bids: Vec<u64>,
    asks: Vec<u64>,
    bb: i64,
    ba: i64,
    far_bids: BTreeMap<u32, u64>,
    far_asks: BTreeMap<u32, u64>,
    pool: Vec<Order>,
    free: Vec<u32>,
    map: OrderMap,
    pub stale: bool,
    pub recentrings: u64,
}

impl LadderBook {
    pub fn new(tick: u32, width: usize, max_orders: usize) -> Self {
        LadderBook {
            tick: tick as i64,
            w: width as i64,
            base: 0,
            centred: false,
            bids: vec![0; width],
            asks: vec![0; width],
            bb: -1,
            ba: width as i64,
            far_bids: BTreeMap::new(),
            far_asks: BTreeMap::new(),
            pool: vec![Order::default(); max_orders],
            free: (0..max_orders as u32).rev().collect(),
            map: OrderMap::new(4 * max_orders),
            stale: false,
            recentrings: 0,
        }
    }

    fn price_of(&self, i: i64) -> u32 {
        (self.base + i * self.tick) as u32
    }
    fn index_of(&self, p: u32) -> i64 {
        (p as i64 - self.base) / self.tick
    }

    fn level_add(&mut self, side: u8, price: u32, dq: i64) {
        let i = self.index_of(price);
        if (0..self.w).contains(&i) {
            let lv = if side == BID { &mut self.bids[i as usize] } else { &mut self.asks[i as usize] };
            *lv = (*lv as i64 + dq) as u64;
            let q = *lv;
            if side == BID {
                if q > 0 && i > self.bb {
                    self.bb = i;
                }
                if i == self.bb && q == 0 {
                    while self.bb >= 0 && self.bids[self.bb as usize] == 0 {
                        self.bb -= 1;
                    }
                }
            } else {
                if q > 0 && i < self.ba {
                    self.ba = i;
                }
                if i == self.ba && q == 0 {
                    while self.ba < self.w && self.asks[self.ba as usize] == 0 {
                        self.ba += 1;
                    }
                }
            }
            return;
        }
        let far = if side == BID { &mut self.far_bids } else { &mut self.far_asks };
        let lv = far.entry(price).or_insert(0);
        *lv = (*lv as i64 + dq) as u64;
        if *lv == 0 {
            far.remove(&price);
        }
    }

    fn centre(&mut self, mid: u32) {
        self.base = mid as i64 - (self.w / 2) * self.tick;
        self.base -= self.base % self.tick;
        self.centred = true;
        self.bids.iter_mut().for_each(|x| *x = 0);
        self.asks.iter_mut().for_each(|x| *x = 0);
        self.far_bids.clear();
        self.far_asks.clear();
        self.bb = -1;
        self.ba = self.w;
        for k in 0..self.pool.len() {
            let o = self.pool[k];
            if o.live {
                self.level_add(o.side, o.price, o.qty as i64);
            }
        }
    }

    fn maybe_recentre(&mut self) {
        let (bid, ask) = (self.bb >= 0, self.ba < self.w);
        let inside = |i: i64, w: i64| i >= w / 4 && i < 3 * w / 4;
        if (!bid || inside(self.bb, self.w)) && (!ask || inside(self.ba, self.w)) {
            return;
        }
        let mid = if bid && ask {
            (self.price_of(self.bb) as i64 + self.price_of(self.ba) as i64) / 2
        } else {
            self.price_of(if bid { self.bb } else { self.ba }) as i64
        };
        self.centre(mid as u32);
        self.recentrings += 1;
    }

    fn add(&mut self, r: u64, side: u8, price: u32, qty: u64) {
        if self.free.is_empty() || self.map.find(r).is_some() {
            return;
        }
        if !self.centred {
            self.centre(price);
        }
        let i = self.index_of(price);
        if (side == BID && i >= self.w) || (side == ASK && i < 0) {
            self.centre(price);
            self.recentrings += 1;
        }
        let s = self.free.pop().unwrap();
        self.pool[s as usize] = Order { price, qty, side, live: true };
        self.map.insert(r, s);
        self.level_add(side, price, qty as i64);
        self.maybe_recentre();
    }

    fn reduce(&mut self, r: u64, qty: u64) {
        let Some(s) = self.map.find(r) else { return };
        let o = &mut self.pool[s as usize];
        let q = qty.min(o.qty);
        o.qty -= q;
        let (side, price, left) = (o.side, o.price, o.qty);
        if left == 0 {
            o.live = false;
            self.free.push(s);
            self.map.erase(r);
        }
        self.level_add(side, price, -(q as i64));
        self.maybe_recentre();
    }

    fn reset(&mut self) {
        let n = self.pool.len();
        *self = LadderBook::new(self.tick as u32, self.w as usize, n);
    }

    pub fn apply(&mut self, e: &Event) {
        match e.kind {
            b'A' => self.add(e.r#ref, e.side, e.price, e.qty),
            b'E' | b'X' | b'C' => self.reduce(e.r#ref, e.qty),
            b'D' => {
                if let Some(s) = self.map.find(e.r#ref) {
                    let q = self.pool[s as usize].qty;
                    self.reduce(e.r#ref, q);
                }
            }
            b'U' => {
                if let Some(s) = self.map.find(e.r#ref) {
                    let o = self.pool[s as usize];
                    self.reduce(e.r#ref, o.qty);
                    self.add(e.ref2, o.side, e.price, e.qty);
                }
            }
            b'G' => {
                let rec = self.recentrings;
                self.reset();
                self.recentrings = rec;
                self.stale = true;
            }
            b'W' => self.stale = false,
            _ => {}
        }
    }

    /// Up to n levels of a side, best first.
    pub fn depth(&self, side: u8, n: usize) -> Vec<(u32, u64)> {
        let mut out = Vec::with_capacity(n);
        if side == BID {
            let mut i = self.bb;
            while i >= 0 && out.len() < n {
                if self.bids[i as usize] > 0 {
                    out.push((self.price_of(i), self.bids[i as usize]));
                }
                i -= 1;
            }
            out.extend(self.far_bids.iter().rev().take(n - out.len()).map(|(&p, &q)| (p, q)));
        } else {
            let mut i = self.ba;
            while i < self.w && out.len() < n {
                if self.asks[i as usize] > 0 {
                    out.push((self.price_of(i), self.asks[i as usize]));
                }
                i += 1;
            }
            out.extend(self.far_asks.iter().take(n - out.len()).map(|(&p, &q)| (p, q)));
        }
        out
    }
}

pub fn l2_hash(b: &LadderBook, mut h: u64) -> u64 {
    for side in [BID, ASK] {
        let mut d = b.depth(side, 5);
        d.resize(5, (0, 0));
        for (p, q) in d {
            for x in p.to_le_bytes().iter().chain(q.to_le_bytes().iter()) {
                h = (h ^ *x as u64).wrapping_mul(0x100000001B3);
            }
        }
    }
    h
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixtures_match_the_reference() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../data");
        let expected = std::fs::read_to_string(dir.join("expected.txt")).unwrap();
        for line in expected.lines() {
            let mut it = line.split_whitespace();
            let (name, n, want) = (it.next().unwrap(), it.next().unwrap(), it.next().unwrap());
            let raw = std::fs::read(dir.join(format!("{name}.bin"))).unwrap();
            let events: Vec<Event> = raw.chunks(48).map(Event::from_record).collect();
            assert_eq!(events.len().to_string(), n);
            let tick = if name == "events_sim" { 100 } else { 1 };
            for width in [4096, 256] {
                let mut b = LadderBook::new(tick, width, 1 << 16);
                let mut h = 0xCBF29CE484222325u64;
                for e in &events {
                    b.apply(e);
                    h = l2_hash(&b, h);
                }
                assert_eq!(format!("{h:016x}"), want, "{name} width {width}");
            }
        }
    }

    #[test]
    fn order_map_backward_shift() {
        let mut m = OrderMap::new(16);
        for k in 1..=10u64 {
            m.insert(k * 1024, k as u32);
        }
        m.erase(3 * 1024);
        m.erase(1024);
        assert!(m.find(1024).is_none() && m.find(3 * 1024).is_none());
        for k in [2u64, 4, 5, 6, 7, 8, 9, 10] {
            assert_eq!(m.find(k * 1024), Some(k as u32));
        }
    }
}
