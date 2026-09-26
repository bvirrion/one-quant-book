//! firm.sequencer (Rust): the journal with fencing epochs and the replicated trading state machine, twin of the C++20
//! and Python ones; replays data/journal.txt to the states of data/expected.txt.

use std::collections::BTreeMap;

pub const LIMIT: i64 = 1_000;
pub const SIZE: i64 = 100;
pub const AGGRESS: i64 = 300;
pub const MAX_OPEN: usize = 3;

/// kind: b'M' price | b'E' cl qty leaves | b'C' cl | b'J' cl reason | b'Q' cl | b'A' key_seq key_idx new_cl
#[derive(Clone, Copy, Debug, Default)]
pub struct Entry {
    pub epoch: i64,
    pub seq: i64,
    pub kind: u8,
    pub a: i64,
    pub b: i64,
    pub c: i64,
    pub reason: u8,
}

pub fn parse(line: &str) -> Entry {
    let f: Vec<&str> = line.split_whitespace().collect();
    let num = |k: usize| f.get(k).map_or(0, |s| s.parse::<i64>().unwrap());
    let kind = f[2].as_bytes()[0];
    let mut e = Entry { epoch: num(0), seq: num(1), kind, a: num(3), ..Entry::default() };
    if kind == b'J' {
        e.reason = f[4].as_bytes()[0];
    } else {
        e.b = num(4);
        e.c = num(5);
    }
    e
}

#[derive(Default)]
pub struct Journal {
    pub entries: Vec<Entry>,
    pub epoch: i64,
}

impl Journal {
    pub fn new() -> Self {
        Journal { entries: vec![], epoch: 1 }
    }
    /// The new entry's sequence number, or an error if the writer's epoch has been fenced off.
    pub fn append(&mut self, mut e: Entry) -> Result<i64, String> {
        if e.epoch < self.epoch {
            return Err("fenced".into());
        }
        e.seq = self.entries.len() as i64 + 1;
        self.entries.push(e);
        Ok(e.seq)
    }
    pub fn fence(&mut self, epoch: i64) -> Result<(), String> {
        if epoch <= self.epoch {
            return Err("a new epoch must be larger".into());
        }
        self.epoch = epoch;
        Ok(())
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Order {
    pub key: (i64, i64),
    pub side: u8,
    pub qty: i64,
    pub price: i64,
    pub filled: i64,
}

pub struct Replica {
    pub position: i64,
    pub last_price: i64,
    pub applied: i64,
    pub reports_seen: i64,
    pub hash: u64,
    pub open: BTreeMap<i64, Order>,
    pub abandoned: BTreeMap<i64, Order>,
}

impl Default for Replica {
    fn default() -> Self {
        Replica {
            position: 0,
            last_price: 0,
            applied: 0,
            reports_seen: 0,
            hash: 0xCBF29CE484222325,
            open: BTreeMap::new(),
            abandoned: BTreeMap::new(),
        }
    }
}

impl Replica {
    fn mix(&mut self, vals: &[i64]) {
        for v in vals {
            for b in v.to_le_bytes() {
                self.hash = (self.hash ^ u64::from(b)).wrapping_mul(0x100000001B3);
            }
        }
    }
    fn open_qty(&self, side: u8) -> i64 {
        self.open.values().filter(|o| o.side == side).map(|o| o.qty - o.filled).sum()
    }
    /// Applies the next entry; returns the orders it decides to send (client id, side, quantity, price).
    pub fn apply(&mut self, e: &Entry) -> Result<Vec<(i64, u8, i64, i64)>, String> {
        if e.seq != self.applied + 1 {
            return Err(format!("gap: expected {}, got {}", self.applied + 1, e.seq));
        }
        self.applied = e.seq;
        let mut out = vec![];
        match e.kind {
            b'M' => {
                let p = e.a;
                if self.last_price != 0 && p != self.last_price && self.open.len() < MAX_OPEN {
                    let side = if p < self.last_price { b'B' } else { b'S' };
                    let pos = if side == b'B' { self.position } else { -self.position };
                    if LIMIT - pos - self.open_qty(side) >= SIZE {
                        let cl = e.seq * 16;
                        let price = if side == b'B' { p + AGGRESS } else { p - AGGRESS };
                        self.open.insert(cl, Order { key: (e.seq, 0), side, qty: SIZE, price, filled: 0 });
                        out.push((cl, side, SIZE, price));
                        self.mix(&[e.seq, 0, i64::from(side), SIZE, price]);
                    }
                }
                self.last_price = p;
            }
            b'A' => {
                if let Some(old) = self.open.iter().find(|(_, o)| o.key == (e.a, e.b)).map(|(c, _)| *c) {
                    let o = self.open.remove(&old).unwrap();
                    self.abandoned.insert(old, o);
                    self.open.insert(e.c, Order { filled: 0, ..o });
                }
                self.mix(&[e.seq, e.c]);
            }
            _ => {
                self.reports_seen += 1;
                let cl = e.a;
                if let Some(o) = self.open.get_mut(&cl) {
                    match e.kind {
                        b'E' => {
                            o.filled += e.b;
                            self.position += if o.side == b'B' { e.b } else { -e.b };
                            if e.c == 0 {
                                self.open.remove(&cl);
                            }
                        }
                        b'C' => {
                            self.open.remove(&cl);
                        }
                        b'J' if e.reason != b'D' => {
                            self.open.remove(&cl);
                        }
                        _ => {}
                    }
                } else if let Some(o) = self.abandoned.get(&cl).copied() {
                    if e.kind == b'E' {
                        self.position += if o.side == b'B' { e.b } else { -e.b };
                    }
                    if e.kind == b'C' || (e.kind == b'E' && e.c == 0) {
                        self.abandoned.remove(&cl);
                    }
                }
            }
        }
        let (s, p, n) = (e.seq, self.position, self.open.len() as i64);
        self.mix(&[s, p, n]);
        Ok(out)
    }
    pub fn unacknowledged(&self) -> Vec<(i64, i64)> {
        let mut k: Vec<(i64, i64)> = self.open.values().filter(|o| o.filled == 0).map(|o| o.key).collect();
        k.sort_unstable();
        k
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn replays_the_failover_journal() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../data");
        let journal = std::fs::read_to_string(dir.join("journal.txt")).unwrap();
        let want: BTreeMap<i64, String> = std::fs::read_to_string(dir.join("expected.txt"))
            .unwrap()
            .lines()
            .map(|l| (l.split_whitespace().nth(1).unwrap().parse().unwrap(), l.to_string()))
            .collect();
        let mut r = Replica::default();
        for line in journal.lines() {
            let e = parse(line);
            r.apply(&e).unwrap();
            if let Some(w) = want.get(&e.seq) {
                let keys: Vec<String> = r.unacknowledged().iter().map(|(s, i)| format!("{s}.{i}")).collect();
                let keys = if keys.is_empty() { "-".to_string() } else { keys.join(",") };
                let got = format!("prefix {} {:016x} {} {} {}", e.seq, r.hash, r.position, r.open.len(), keys);
                assert_eq!(&got, w);
            }
        }
    }

    #[test]
    fn fencing_refuses_an_old_epoch() {
        let mut j = Journal::new();
        j.append(Entry { epoch: 1, kind: b'M', a: 1_000_000, ..Entry::default() }).unwrap();
        j.fence(2).unwrap();
        assert!(j.append(Entry { epoch: 1, kind: b'M', a: 1_000_100, ..Entry::default() }).is_err());
        assert_eq!(j.append(Entry { epoch: 2, kind: b'M', a: 1_000_200, ..Entry::default() }), Ok(2));
    }
}
