//! firm.pblimits -- pre-trade prime-broker limit gate (build of Chapter 27, One Quant Book 2), Rust
//! twin of the C++20 gate and of firm_pblimits.py. NOP = sum of net long USD values across
//! currencies; settlement of a value date = sum of USD values of currencies to be received. An order
//! passes if it keeps both within limits or does not increase one already above its limit.

use std::collections::{BTreeMap, BTreeSet};

pub type Usd = BTreeMap<String, f64>;

#[derive(Clone, Debug)]
pub struct Limits {
    pub pb: String,
    pub fee_per_m: f64,
    pub nop_limit: f64,
    pub settle_limit: f64,
    pub max_tenor: i32,
    pub pairs: BTreeSet<String>,
}

#[derive(Clone, Debug)]
pub struct Order {
    pub pair: String,
    pub buy: bool,
    pub amount: f64,
    pub rate: f64,
    pub value_day: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Decision {
    Ok,
    Pair,
    Tenor,
    Nop,
    Settlement,
}

fn positive_sum(m: &Usd) -> f64 {
    m.values().filter(|v| **v > 0.0).sum()
}

pub fn legs(o: &Order, usd_per: &Usd) -> Vec<(String, f64)> {
    let (base, quote) = (o.pair[..3].to_string(), o.pair[3..6].to_string());
    let sign = if o.buy { 1.0 } else { -1.0 };
    let b = sign * o.amount * usd_per[&base];
    let q = -sign * o.amount * o.rate * usd_per[&quote];
    vec![(base, b), (quote, q)]
}

#[derive(Clone, Debug)]
pub struct Book {
    pub limits: Limits,
    pub net: Usd,
    pub settle: BTreeMap<i32, Usd>,
}

impl Book {
    pub fn new(limits: Limits) -> Book {
        Book { limits, net: Usd::new(), settle: BTreeMap::new() }
    }

    pub fn nop(&self) -> f64 {
        positive_sum(&self.net)
    }

    pub fn settlement(&self, day: i32) -> f64 {
        self.settle.get(&day).map_or(0.0, positive_sum)
    }

    pub fn check(&self, o: &Order, usd_per: &Usd) -> Decision {
        if !self.limits.pairs.contains(&o.pair) {
            return Decision::Pair;
        }
        if o.value_day > self.limits.max_tenor {
            return Decision::Tenor;
        }
        let mut n = self.net.clone();
        let mut f = self.settle.get(&o.value_day).cloned().unwrap_or_default();
        for (c, v) in legs(o, usd_per) {
            *n.entry(c.clone()).or_insert(0.0) += v;
            *f.entry(c).or_insert(0.0) += v;
        }
        let (new_nop, new_set) = (positive_sum(&n), positive_sum(&f));
        if new_nop > self.limits.nop_limit && new_nop > self.nop() {
            return Decision::Nop;
        }
        if new_set > self.limits.settle_limit && new_set > self.settlement(o.value_day) {
            return Decision::Settlement;
        }
        Decision::Ok
    }

    pub fn apply(&mut self, o: &Order, usd_per: &Usd) {
        let day = self.settle.entry(o.value_day).or_default();
        for (c, v) in legs(o, usd_per) {
            *self.net.entry(c.clone()).or_insert(0.0) += v;
            *day.entry(c).or_insert(0.0) += v;
        }
    }
}

/// Give the order up to the cheapest prime broker that accepts it.
pub fn route(books: &mut [Book], o: &Order, usd_per: &Usd) -> Option<String> {
    let mut idx: Vec<usize> = (0..books.len()).collect();
    idx.sort_by(|a, b| books[*a].limits.fee_per_m.total_cmp(&books[*b].limits.fee_per_m));
    for i in idx {
        if books[i].check(o, usd_per) == Decision::Ok {
            books[i].apply(o, usd_per);
            return Some(books[i].limits.pb.clone());
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    fn usd() -> Usd {
        [("USD", 1.0), ("EUR", 1.10), ("JPY", 1.0 / 150.0), ("GBP", 1.30), ("MXN", 1.0 / 18.0)]
            .iter()
            .map(|(c, v)| (c.to_string(), *v))
            .collect()
    }

    fn lim(pb: &str, fee: f64, nop: f64, set: f64, tenor: i32, pairs: &[&str]) -> Limits {
        Limits {
            pb: pb.into(),
            fee_per_m: fee,
            nop_limit: nop,
            settle_limit: set,
            max_tenor: tenor,
            pairs: pairs.iter().map(|p| p.to_string()).collect(),
        }
    }

    fn books() -> Vec<Book> {
        vec![
            Book::new(lim("A", 3.0, 100e6, 500e6, 7, &["EURUSD", "USDJPY"])),
            Book::new(lim("B", 5.0, 150e6, 600e6, 30, &["EURUSD", "USDJPY", "GBPUSD"])),
            Book::new(lim("C", 8.0, 300e6, 1000e6, 370, &["EURUSD", "USDJPY", "GBPUSD", "USDMXN"])),
        ]
    }

    fn o(pair: &str, buy: bool, amount: f64, rate: f64, day: i32) -> Order {
        Order { pair: pair.into(), buy, amount, rate, value_day: day }
    }

    #[test]
    fn nop_and_settlement() {
        let u = usd();
        let mut a = books().remove(0);
        a.apply(&o("EURUSD", true, 50e6, 1.10, 2), &u);
        assert!((a.nop() - 55e6).abs() < 1e-6 && (a.settlement(2) - 55e6).abs() < 1e-6);
        a.apply(&o("USDJPY", true, 20e6, 150.0, 2), &u);
        assert!((a.nop() - 55e6).abs() < 1e-6 && (a.settlement(2) - 55e6).abs() < 1e-6);
    }

    #[test]
    fn limits_and_reducing_trades() {
        let u = usd();
        let mut a = books().remove(0);
        assert_eq!(a.check(&o("EURUSD", true, 95e6, 1.10, 2), &u), Decision::Nop);
        a.apply(&o("EURUSD", true, 90e6, 1.10, 2), &u);
        a.limits.nop_limit = 50e6;
        assert_eq!(a.check(&o("EURUSD", true, 1e6, 1.10, 2), &u), Decision::Nop);
        assert_eq!(a.check(&o("EURUSD", false, 10e6, 1.10, 2), &u), Decision::Ok);
        assert_eq!(a.check(&o("GBPUSD", true, 1e6, 1.30, 2), &u), Decision::Pair);
        assert_eq!(a.check(&o("EURUSD", true, 1e6, 1.10, 30), &u), Decision::Tenor);
    }

    #[test]
    fn settlement_by_value_date() {
        let u = usd();
        let mut b = books().remove(1);
        b.limits.nop_limit = 1e12;
        b.apply(&o("EURUSD", true, 500e6, 1.10, 2), &u);
        assert_eq!(b.check(&o("EURUSD", true, 50e6, 1.10, 2), &u), Decision::Settlement);
        assert_eq!(b.check(&o("EURUSD", true, 50e6, 1.10, 3), &u), Decision::Ok);
    }

    #[test]
    fn router() {
        let u = usd();
        let mut bs = books();
        assert_eq!(route(&mut bs, &o("EURUSD", true, 80e6, 1.10, 2), &u).as_deref(), Some("A"));
        assert_eq!(route(&mut bs, &o("EURUSD", true, 80e6, 1.10, 2), &u).as_deref(), Some("B"));
        assert_eq!(route(&mut bs, &o("USDMXN", true, 10e6, 18.0, 2), &u).as_deref(), Some("C"));
    }
}
