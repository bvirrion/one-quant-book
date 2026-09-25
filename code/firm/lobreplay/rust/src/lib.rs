//! firm.lobreplay -- the 'fifo' queue-position model for shadow orders (One Quant Book 7, chapter 18), Rust twin of
//! firm_lobreplay.track_fifo. Arrivals and cancellations take effect before any market message at the same time; a
//! shadow joins behind the orders resting at its price, moves up as they are executed or cancelled, and fills when an
//! execution reaches an order behind it. Checked on data/fixture_*.csv.
use std::collections::{BTreeMap, HashMap, VecDeque};

#[derive(Debug, Clone, Copy)]
pub struct Msg {
    pub t: f64,
    pub kind: char,
    pub oid: i64,
    pub side: i8,
    pub price: i64,
    pub qty: i64,
}

#[derive(Debug, Clone, Copy)]
pub struct VOrder {
    pub vid: usize,
    pub side: i8,
    pub price: i64,
    pub qty: i64,
    pub arrive: f64,
    pub cancel: f64,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Fill {
    pub vid: usize,
    pub t: f64,
    pub qty: i64,
}

#[derive(Default)]
struct Book {
    levels: HashMap<i8, BTreeMap<i64, VecDeque<(i64, i64)>>>,
    at: HashMap<i64, (i8, i64)>,
}

impl Book {
    fn apply(&mut self, m: &Msg) {
        if m.kind == 'A' {
            self.levels.entry(m.side).or_default().entry(m.price).or_default().push_back((m.oid, m.qty));
            self.at.insert(m.oid, (m.side, m.price));
            return;
        }
        let (side, px) = self.at[&m.oid];
        let lv = self.levels.get_mut(&side).unwrap();
        let q = lv.get_mut(&px).unwrap();
        if let Some(i) = q.iter().position(|(o, _)| *o == m.oid) {
            q[i].1 -= m.qty;
            if q[i].1 <= 0 {
                q.remove(i);
                self.at.remove(&m.oid);
            }
        }
        if q.is_empty() {
            lv.remove(&px);
        }
    }

    fn level(&self, side: i8, px: i64) -> Option<&VecDeque<(i64, i64)>> {
        self.levels.get(&side).and_then(|l| l.get(&px))
    }
}

struct Shadow {
    o: VOrder,
    filled: i64,
    status: u8, // 0 sent, 1 working, 2 filled, 3 cancelled
    ahead: HashMap<i64, i64>,
}

pub fn track_fifo(msgs: &[Msg], orders: &[VOrder]) -> Vec<Fill> {
    let mut sh: Vec<Shadow> = orders.iter().map(|o| Shadow { o: *o, filled: 0, status: 0, ahead: HashMap::new() }).collect();
    let mut ev: Vec<(f64, u8, usize)> = Vec::new();
    for o in orders {
        ev.push((o.arrive, 0, o.vid));
        if o.cancel.is_finite() {
            ev.push((o.cancel, 1, o.vid));
        }
    }
    ev.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let mut book = Book::default();
    let mut out = Vec::new();
    let mut active: Vec<usize> = Vec::new(); // in activation order, like the Python dict
    let mut j = 0;
    for m in msgs {
        while j < ev.len() && ev[j].0 <= m.t {
            let (_, kind, vid) = ev[j];
            if kind == 0 && sh[vid].status == 0 {
                sh[vid].status = 1;
                if let Some(q) = book.level(sh[vid].o.side, sh[vid].o.price) {
                    sh[vid].ahead = q.iter().copied().collect();
                }
                active.push(vid);
            } else if kind == 1 && sh[vid].status <= 1 {
                sh[vid].status = 3;
                active.retain(|&v| v != vid);
            }
            j += 1;
        }
        let now = active.clone();
        for v in now {
            let s = &mut sh[v];
            if s.o.side != m.side || s.o.price != m.price || m.kind == 'A' {
                continue;
            }
            if let Some(n) = s.ahead.get_mut(&m.oid) {
                *n -= m.qty.min(*n);
                if *n <= 0 {
                    s.ahead.remove(&m.oid);
                }
            } else if m.kind == 'E' {
                let q = (s.o.qty - s.filled).min(m.qty);
                if q > 0 {
                    s.filled += q;
                    out.push(Fill { vid: v, t: m.t, qty: q });
                    if s.filled >= s.o.qty {
                        s.status = 2;
                        active.retain(|&x| x != v);
                    }
                }
            }
        }
        book.apply(m);
    }
    out
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
    fn reproduces_the_python_fills() {
        let msgs: Vec<Msg> = read("fixture_msgs.csv")
            .iter()
            .map(|r| Msg {
                t: r[0].parse().unwrap(),
                kind: r[1].chars().next().unwrap(),
                oid: r[2].parse().unwrap(),
                side: r[3].parse().unwrap(),
                price: r[4].parse().unwrap(),
                qty: r[5].parse().unwrap(),
            })
            .collect();
        let orders: Vec<VOrder> = read("fixture_orders.csv")
            .iter()
            .map(|r| VOrder {
                vid: r[0].parse().unwrap(),
                side: r[1].parse().unwrap(),
                price: r[2].parse().unwrap(),
                qty: r[3].parse().unwrap(),
                arrive: r[4].parse().unwrap(),
                cancel: r[5].parse().unwrap(),
            })
            .collect();
        let got = track_fifo(&msgs, &orders);
        let want = read("fixture_fills.csv");
        assert_eq!(got.len(), want.len());
        for (g, w) in got.iter().zip(want.iter()) {
            assert_eq!(g.vid, w[0].parse::<usize>().unwrap());
            assert_eq!(g.t, w[1].parse::<f64>().unwrap());
            assert_eq!(g.qty, w[2].parse::<i64>().unwrap());
        }
    }
}
