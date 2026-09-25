//! firm.lobfeat -- streaming order-book features (One Quant Book 7, chapter 8), Rust twin of firm_lobfeat.py.
//! Same state, same operation order, same outputs (checked on data/fixture_*.csv).
use std::cmp::Reverse;
use std::collections::{BTreeMap, HashMap};

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Features {
    pub bid: i64,
    pub ask: i64,
    pub bid_qty: i64,
    pub ask_qty: i64,
    pub imbalance: f64,
    pub depth_imbalance: f64,
    pub ofi: i64,
    pub ofi_cum: i64,
    pub wmid: f64,
    pub micro: f64,
}

pub fn bucket(imbalance: f64, n: usize) -> usize {
    let b = ((imbalance + 1.0) / 2.0 * n as f64) as usize;
    b.min(n - 1)
}

struct Order {
    qty: i64,
}

#[derive(Default)]
pub struct LobFeatures {
    levels: usize,
    g: Vec<f64>,
    orders: HashMap<i64, Order>,
    bids: BTreeMap<Reverse<i64>, i64>,
    asks: BTreeMap<i64, i64>,
    prev: Option<(i64, i64, i64, i64)>,
    ofi_cum: i64,
}

impl LobFeatures {
    pub fn new(levels: usize, g: Vec<f64>) -> Self {
        LobFeatures { levels, g, ..Default::default() }
    }

    pub fn on(&mut self, kind: char, oid: i64, side: i32, price: i64, qty: i64) -> Option<Features> {
        if kind == 'A' {
            self.orders.insert(oid, Order { qty });
            if side == 1 {
                *self.bids.entry(Reverse(price)).or_insert(0) += qty;
            } else {
                *self.asks.entry(price).or_insert(0) += qty;
            }
        } else {
            let left = {
                let o = self.orders.get_mut(&oid).expect("unknown order");
                o.qty -= qty;
                o.qty
            };
            if left == 0 {
                self.orders.remove(&oid);
            }
            if side == 1 {
                let q = self.bids.get_mut(&Reverse(price)).expect("unknown level");
                *q -= qty;
                if *q == 0 {
                    self.bids.remove(&Reverse(price));
                }
            } else {
                let q = self.asks.get_mut(&price).expect("unknown level");
                *q -= qty;
                if *q == 0 {
                    self.asks.remove(&price);
                }
            }
        }
        let (&Reverse(bb), &qb) = self.bids.iter().next()?;
        let (&ba, &qa) = self.asks.iter().next()?;
        let e = match self.prev {
            None => 0,
            Some((pb, pqb, pa, pqa)) => {
                (if bb >= pb { qb } else { 0 }) - (if bb <= pb { pqb } else { 0 })
                    - (if ba <= pa { qa } else { 0 })
                    + (if ba >= pa { pqa } else { 0 })
            }
        };
        self.prev = Some((bb, qb, ba, qa));
        self.ofi_cum += e;
        let imb = (qb - qa) as f64 / (qb + qa) as f64;
        let db: i64 = self.bids.values().take(self.levels).sum();
        let da: i64 = self.asks.values().take(self.levels).sum();
        let dimb = (db - da) as f64 / (db + da) as f64;
        let mid = 0.5 * (bb + ba) as f64;
        let wmid = (ba * qb + bb * qa) as f64 / (qb + qa) as f64;
        let micro = if !self.g.is_empty() && ba - bb == 1 { mid + self.g[bucket(imb, self.g.len())] } else { mid };
        Some(Features {
            bid: bb, ask: ba, bid_qty: qb, ask_qty: qa, imbalance: imb, depth_imbalance: dimb,
            ofi: e, ofi_cum: self.ofi_cum, wmid, micro,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn read(name: &str) -> Vec<Vec<String>> {
        let path = format!("{}/../data/{}", env!("CARGO_MANIFEST_DIR"), name);
        let text = fs::read_to_string(path).expect("fixture");
        text.lines().skip(1).map(|l| l.split(',').map(|c| c.to_string()).collect()).collect()
    }

    #[test]
    fn replays_the_fixture_like_python() {
        let g: Vec<f64> = read("fixture_g.csv").iter().map(|r| r[1].parse().unwrap()).collect();
        let msgs = read("fixture_msgs.csv");
        let exp = read("fixture_expected.csv");
        assert_eq!(msgs.len(), exp.len());
        let mut eng = LobFeatures::new(5, g);
        let mut checked = 0;
        for (m, e) in msgs.iter().zip(exp.iter()) {
            let f = eng.on(m[0].chars().next().unwrap(), m[1].parse().unwrap(), m[2].parse().unwrap(),
                           m[3].parse().unwrap(), m[4].parse().unwrap());
            if e[0] == "nan" {
                assert!(f.is_none());
                continue;
            }
            let f = f.expect("features");
            let close = |a: f64, b: &str| (a - b.parse::<f64>().unwrap()).abs() < 1e-12;
            assert_eq!((f.bid, f.ask, f.bid_qty, f.ask_qty), (e[0].parse().unwrap(), e[1].parse().unwrap(),
                        e[2].parse().unwrap(), e[3].parse().unwrap()));
            assert!(close(f.imbalance, &e[4]) && close(f.depth_imbalance, &e[5]));
            assert_eq!((f.ofi, f.ofi_cum), (e[6].parse().unwrap(), e[7].parse().unwrap()));
            assert!(close(f.wmid, &e[8]) && close(f.micro, &e[9]));
            checked += 1;
        }
        assert!(checked > 1000);
    }
}
