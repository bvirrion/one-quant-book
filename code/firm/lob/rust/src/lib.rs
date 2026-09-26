//! firm.lob (One Quant Book 10, chapter 1), Rust: the public book rebuilt from a market-by-order stream.
//! Same semantics as `firm_lob.MessageBook` and `cpp/firm_lob.hpp`.

use std::collections::{BTreeMap, HashMap};

#[derive(Debug, Clone, Copy)]
struct Resting {
    side: i8,
    price: i64,
    qty: i64,
}

#[derive(Debug, PartialEq, Eq)]
pub enum BookError {
    Duplicate(u64),
    Unknown(u64),
    BadReduce(u64),
}

#[derive(Default)]
pub struct MessageBook {
    orders: HashMap<u64, Resting>,
    bids: BTreeMap<i64, i64>,
    asks: BTreeMap<i64, i64>,
}

impl MessageBook {
    pub fn new() -> Self {
        Self::default()
    }

    fn level(&mut self, side: i8) -> &mut BTreeMap<i64, i64> {
        if side == 1 {
            &mut self.bids
        } else {
            &mut self.asks
        }
    }

    fn take(&mut self, side: i8, price: i64, qty: i64) {
        let lv = self.level(side);
        let left = lv.get(&price).copied().unwrap_or(0) - qty;
        if left == 0 {
            lv.remove(&price);
        } else {
            lv.insert(price, left);
        }
    }

    pub fn add(&mut self, r: u64, side: i8, price: i64, qty: i64) -> Result<(), BookError> {
        if self.orders.contains_key(&r) {
            return Err(BookError::Duplicate(r));
        }
        self.orders.insert(r, Resting { side, price, qty });
        *self.level(side).entry(price).or_insert(0) += qty;
        Ok(())
    }

    pub fn reduce(&mut self, r: u64, qty: i64) -> Result<(), BookError> {
        let o = *self.orders.get(&r).ok_or(BookError::Unknown(r))?;
        if qty <= 0 || qty > o.qty {
            return Err(BookError::BadReduce(r));
        }
        self.take(o.side, o.price, qty);
        if o.qty == qty {
            self.orders.remove(&r);
        } else {
            self.orders.insert(r, Resting { qty: o.qty - qty, ..o });
        }
        Ok(())
    }

    pub fn remove(&mut self, r: u64) -> Result<(), BookError> {
        let o = self.orders.remove(&r).ok_or(BookError::Unknown(r))?;
        self.take(o.side, o.price, o.qty);
        Ok(())
    }

    pub fn replace(&mut self, r: u64, new_ref: u64, price: i64, qty: i64) -> Result<(), BookError> {
        let side = self.orders.get(&r).ok_or(BookError::Unknown(r))?.side;
        self.remove(r)?;
        self.add(new_ref, side, price, qty)
    }

    /// Best `n` levels of one side, best first.
    pub fn depth(&self, side: i8, n: usize) -> Vec<(i64, i64)> {
        if side == 1 {
            self.bids.iter().rev().take(n).map(|(p, q)| (*p, *q)).collect()
        } else {
            self.asks.iter().take(n).map(|(p, q)| (*p, *q)).collect()
        }
    }

    pub fn live(&self) -> usize {
        self.orders.len()
    }
}

/// The canonical two-line text of `firm_lob.l2_lines`.
pub fn l2_lines(b: &MessageBook, n: usize) -> String {
    let side = |s: i8| -> String {
        b.depth(s, n)
            .iter()
            .map(|(p, q)| format!(" {p}:{q}"))
            .collect::<String>()
    };
    format!("B{}\nS{}", side(1), side(-1))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn fixture_matches_python() {
        let dir = concat!(env!("CARGO_MANIFEST_DIR"), "/../data/");
        let msgs = fs::read_to_string(format!("{dir}fixture_msgs.csv")).unwrap();
        let expect = fs::read_to_string(format!("{dir}fixture_l2.txt")).unwrap();
        let mut want = std::collections::HashMap::new();
        let lines: Vec<&str> = expect.lines().collect();
        for c in lines.chunks(3) {
            let i: usize = c[0].trim_start_matches("# ").parse().unwrap();
            want.insert(i, format!("{}\n{}", c[1], c[2]));
        }
        let mut book = MessageBook::new();
        let mut checked = 0;
        for (i, line) in msgs.lines().skip(1).enumerate() {
            let f: Vec<&str> = line.split(',').collect();
            let r: u64 = f[1].parse().unwrap();
            if f[0] == "A" {
                book.add(r, f[2].parse().unwrap(), f[3].parse().unwrap(), f[4].parse().unwrap())
                    .unwrap();
            } else {
                book.reduce(r, f[4].parse().unwrap()).unwrap();
            }
            if let Some(w) = want.get(&(i + 1)) {
                assert_eq!(&l2_lines(&book, 5), w, "after message {}", i + 1);
                checked += 1;
            }
        }
        assert_eq!(checked, 147);
    }

    #[test]
    fn replace_moves_to_new_reference() {
        let mut b = MessageBook::new();
        b.add(1, 1, 100, 300).unwrap();
        b.add(2, 1, 100, 200).unwrap();
        b.replace(1, 3, 101, 100).unwrap();
        assert_eq!(b.depth(1, 5), vec![(101, 100), (100, 200)]);
        assert_eq!(b.reduce(9, 1), Err(BookError::Unknown(9)));
        assert_eq!(b.live(), 2);
    }
}
