//! firm.wsbook -- websocket order-book builder (build of Chapter 26, One Quant Book 3), Rust twin of the
//! C++20 builder and of firm_wsbook.py: snapshot plus (U, u)-numbered deltas with absolute quantities, gap
//! detection and resync, and a CRC32 checksum over the ten best asks (low to high) then bids (high to low).

use std::collections::BTreeMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Status {
    Ignored,
    Applied,
    Gap,
}

pub fn crc32(data: &[u8]) -> u32 {
    let mut c: u32 = 0xFFFF_FFFF;
    for &byte in data {
        c ^= u32::from(byte);
        for _ in 0..8 {
            c = (c >> 1) ^ if c & 1 == 1 { 0xEDB8_8320 } else { 0 };
        }
    }
    c ^ 0xFFFF_FFFF
}

#[derive(Default)]
pub struct Book {
    pub bids: BTreeMap<i64, i64>,
    pub asks: BTreeMap<i64, i64>,
    pub update_id: i64,
    pub synced: bool,
}

impl Book {
    pub fn snapshot(&mut self, id: i64, bids: &[(i64, i64)], asks: &[(i64, i64)]) {
        self.bids = bids.iter().copied().collect();
        self.asks = asks.iter().copied().collect();
        self.update_id = id;
        self.synced = true;
    }

    pub fn apply(&mut self, first: i64, last: i64, bids: &[(i64, i64)], asks: &[(i64, i64)]) -> Status {
        if !self.synced {
            return Status::Gap;
        }
        if last < self.update_id + 1 {
            return Status::Ignored;
        }
        if first > self.update_id + 1 {
            self.synced = false;
            return Status::Gap;
        }
        for (side, levels) in [(&mut self.bids, bids), (&mut self.asks, asks)] {
            for &(p, q) in levels {
                if q == 0 {
                    side.remove(&p);
                } else {
                    side.insert(p, q);
                }
            }
        }
        self.update_id = last;
        Status::Applied
    }

    pub fn checksum(&self) -> u32 {
        let mut s = String::new();
        for (p, q) in self.asks.iter().take(10) {
            s.push_str(&format!("{p}{q}"));
        }
        for (p, q) in self.bids.iter().rev().take(10) {
            s.push_str(&format!("{p}{q}"));
        }
        crc32(s.as_bytes())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn book() -> Book {
        let mut b = Book::default();
        b.snapshot(100, &[(999, 5), (998, 7)], &[(1001, 4), (1002, 6)]);
        b
    }

    #[test]
    fn sequence_rules() {
        let mut b = book();
        assert_eq!(b.apply(95, 100, &[(999, 1)], &[]), Status::Ignored);
        assert_eq!(b.apply(99, 101, &[(999, 0)], &[(1001, 9)]), Status::Applied);
        assert_eq!(b.bids.len(), 1);
        assert_eq!(b.asks[&1001], 9);
        assert_eq!(b.apply(103, 104, &[], &[(1003, 1)]), Status::Gap);
        assert!(!b.synced);
        assert_eq!(b.apply(105, 105, &[], &[]), Status::Gap);
    }

    #[test]
    fn checksum_matches_python() {
        assert_eq!(book().checksum(), 3_348_617_501);
        assert_eq!(crc32(b"123456789"), 0xCBF4_3926);
    }
}
