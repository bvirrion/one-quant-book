//! firm.quoteengine -- from target quotes to orders (One Quant Book 11, chapter 10), Rust twin of
//! firm_quoteengine.QuoteEngine: same rules and decision order, checked on data/fixture_*.csv.
use std::collections::BTreeMap;

pub struct TokenBucket {
    rate: f64,
    burst: f64,
    tokens: f64,
    t: Option<f64>,
}

impl TokenBucket {
    pub fn new(rate: f64, burst: f64) -> Self {
        TokenBucket { rate, burst, tokens: burst, t: None }
    }

    pub fn take(&mut self, t: f64) -> bool {
        if self.rate.is_infinite() {
            return true;
        }
        if let Some(t0) = self.t {
            self.tokens = self.burst.min(self.tokens + self.rate * (t - t0));
        }
        self.t = Some(t);
        if self.tokens >= 1.0 {
            self.tokens -= 1.0;
            true
        } else {
            false
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum State {
    PendingNew,
    Live,
    PendingAmend,
    PendingCancel,
}

#[derive(Clone, Copy, Debug)]
pub struct Order {
    pub oid: i64,
    pub side: i64,
    pub price: i64,
    pub leaves: i64,
    pub state: State,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Action {
    New { oid: i64, side: i64, price: i64, qty: i64 },
    Amend { oid: i64, qty: i64 },
    Cancel { oid: i64 },
}

impl Action {
    pub fn text(&self) -> String {
        match self {
            Action::New { oid, side, price, qty } => format!("new {oid} {side} {price} {qty}"),
            Action::Amend { oid, qty } => format!("amend {oid} {qty}"),
            Action::Cancel { oid } => format!("cancel {oid}"),
        }
    }
}

#[derive(Default, Debug)]
pub struct Stats {
    pub new: i64,
    pub amend: i64,
    pub cancel: i64,
    pub dropped: i64,
    pub fills: i64,
    pub races: i64,
}

pub struct QuoteEngine {
    min_move: i64,
    min_size: i64,
    bucket: TokenBucket,
    orders: BTreeMap<i64, Order>,
    next: i64,
    pub stats: Stats,
}

impl QuoteEngine {
    pub fn new(min_move: i64, min_size: i64, rate: f64, burst: f64) -> Self {
        QuoteEngine { min_move, min_size, bucket: TokenBucket::new(rate, burst), orders: BTreeMap::new(), next: 0,
                      stats: Stats::default() }
    }

    pub fn update(&mut self, t: f64, side: i64, input: &[(i64, i64)]) -> Vec<Action> {
        let tg: Vec<(i64, i64)> = input.iter().copied().filter(|x| x.1 > 0).collect();
        let mut covered = vec![false; tg.len()];
        let mut first: Vec<Action> = Vec::new();
        let mut amends: Vec<Action> = Vec::new();
        let mut news: Vec<(i64, i64)> = Vec::new();
        let mut mine: Vec<Order> = self.orders.values().filter(|o| o.side == side).copied().collect();
        mine.sort_by_key(|o| (-side * o.price, o.oid));
        for o in &mine {
            if o.state != State::Live {
                if o.state != State::PendingCancel {
                    if let Some(k) = (0..tg.len()).find(|&k| !covered[k] && tg[k].0 == o.price) {
                        covered[k] = true;
                    }
                }
                continue;
            }
            if let Some(k) = (0..tg.len()).find(|&k| !covered[k] && tg[k].0 == o.price) {
                covered[k] = true;
                let q = tg[k].1;
                if o.leaves - q >= self.min_size {
                    amends.push(Action::Amend { oid: o.oid, qty: q });
                } else if q - o.leaves >= self.min_size {
                    news.push((o.price, q - o.leaves));
                }
                continue;
            }
            let mut best: Option<usize> = None;
            for k in 0..tg.len() {
                let d = (tg[k].0 - o.price).abs();
                if covered[k] || d >= self.min_move {
                    continue;
                }
                if best.is_none_or(|b| d < (tg[b].0 - o.price).abs()) {
                    best = Some(k);
                }
            }
            if let Some(b) = best {
                covered[b] = true;
                continue;
            }
            first.push(Action::Cancel { oid: o.oid });
        }
        for (k, x) in tg.iter().enumerate() {
            if !covered[k] {
                news.push(*x);
            }
        }
        first.extend(amends);
        let mut out = Vec::new();
        for a in first {
            if !self.bucket.take(t) {
                self.stats.dropped += 1;
                continue;
            }
            match &a {
                Action::Cancel { oid } => {
                    self.orders.get_mut(oid).unwrap().state = State::PendingCancel;
                    self.stats.cancel += 1;
                }
                Action::Amend { oid, qty } => {
                    let o = self.orders.get_mut(oid).unwrap();
                    o.state = State::PendingAmend;
                    o.leaves = *qty;
                    self.stats.amend += 1;
                }
                Action::New { .. } => {}
            }
            out.push(a);
        }
        for (p, q) in news {
            if !self.bucket.take(t) {
                self.stats.dropped += 1;
                continue;
            }
            self.next += 1;
            self.orders.insert(self.next, Order { oid: self.next, side, price: p, leaves: q, state: State::PendingNew });
            self.stats.new += 1;
            out.push(Action::New { oid: self.next, side, price: p, qty: q });
        }
        out
    }

    pub fn ack(&mut self, oid: i64) {
        let cancel = match self.orders.get(&oid) {
            None => return,
            Some(o) => o.state == State::PendingCancel,
        };
        if cancel {
            self.orders.remove(&oid);
        } else if let Some(o) = self.orders.get_mut(&oid) {
            o.state = State::Live;
        }
    }

    pub fn fill(&mut self, oid: i64, qty: i64) {
        let Some(o) = self.orders.get_mut(&oid) else { return };
        self.stats.fills += 1;
        if o.state == State::PendingCancel {
            self.stats.races += 1;
        }
        o.leaves -= qty;
        if o.leaves <= 0 {
            self.orders.remove(&oid);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn read(name: &str) -> Vec<String> {
        let path = format!("{}/../data/{}", env!("CARGO_MANIFEST_DIR"), name);
        fs::read_to_string(path).unwrap().lines().skip(1).map(|s| s.to_string()).collect()
    }

    #[test]
    fn replays_the_fixture_like_python() {
        let par: Vec<String> = read("fixture_params.csv")[0].split(',').map(|s| s.to_string()).collect();
        let mut e = QuoteEngine::new(par[0].parse().unwrap(), par[1].parse().unwrap(), par[2].parse().unwrap(),
                                     par[3].parse().unwrap());
        let mut got = Vec::new();
        for line in read("fixture_events.csv") {
            let r: Vec<&str> = line.split(',').collect();
            match r[1] {
                "U" => {
                    let tg: Vec<(i64, i64)> = r[4]
                        .split('|')
                        .filter(|s| !s.is_empty())
                        .map(|s| {
                            let (p, q) = s.split_once(':').unwrap();
                            (p.parse().unwrap(), q.parse().unwrap())
                        })
                        .collect();
                    for a in e.update(r[2].parse().unwrap(), r[3].parse().unwrap(), &tg) {
                        got.push(format!("{},{}", r[0], a.text()));
                    }
                }
                "A" => e.ack(r[5].parse().unwrap()),
                _ => e.fill(r[5].parse().unwrap(), r[6].parse().unwrap()),
            }
        }
        let expected = read("fixture_expected.csv");
        assert!(expected.len() > 1000);
        assert_eq!(got, expected);
    }

    #[test]
    fn an_empty_bucket_drops_actions() {
        let mut e = QuoteEngine::new(1, 1, 1.0, 1.0);
        assert_eq!(e.update(0.0, 1, &[(100, 100), (99, 100)]).len(), 1);
        assert_eq!(e.stats.dropped, 1);
    }
}
