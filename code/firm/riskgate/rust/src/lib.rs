//! firm.riskgate (Rust): the pre-trade risk gate, twin of the C++20 and Python ones. Dense tables by instrument and
//! strategy, every check computed into a bit mask, the lowest set bit reported; replays data/events.txt to the
//! decisions of data/expected.txt.

use firm_exchsim::json::{self, Value};

pub const CODES: &[u8; 12] = b"KSRCQNLHOGTD";
const ONE: i64 = 1_000_000_000;
const DUP_SLOTS: usize = 16;
const NEVER: i64 = -(1 << 62);

#[derive(Clone, Default)]
pub struct InstrLimits {
    pub collar_bp: i64,
    pub max_qty: i64,
    pub max_notional: i64,
    pub max_long: i64,
    pub max_short: i64,
}

#[derive(Clone, Default)]
pub struct StratLimits {
    pub desk: usize,
    pub rate: i64,
    pub burst: i64,
    pub max_open: i64,
}

#[derive(Clone, Default)]
pub struct Limits {
    pub max_age: i64,
    pub ref_max_age: i64,
    pub dup_ns: i64,
    pub firm_gross: i64,
    pub desk_gross: Vec<i64>,
    pub strat: Vec<StratLimits>,
    pub instr: Vec<InstrLimits>,
}

/// Strategy and desk names, indexed in the order of the keys (sorted, as the JSON reader keeps them).
#[derive(Default)]
pub struct Names {
    pub strat: Vec<String>,
    pub desk: Vec<String>,
}

fn index(v: &mut Vec<String>, s: &str) -> usize {
    match v.iter().position(|x| x == s) {
        Some(i) => i,
        None => {
            v.push(s.to_string());
            v.len() - 1
        }
    }
}

fn obj(v: &Value) -> Vec<(&String, &Value)> {
    match v {
        Value::Obj(m) => m.iter().collect(),
        _ => vec![],
    }
}

pub fn parse_limits(v: &Value, names: &mut Names) -> Limits {
    let mut l = Limits {
        max_age: v.int("max_age_ns", 0),
        ref_max_age: v.int("ref_max_age_ns", 0),
        dup_ns: v.int("dup_ns", 0),
        firm_gross: v.get("firm").map_or(0, |f| f.int("max_gross", 0)),
        ..Limits::default()
    };
    for (name, d) in obj(v.get("desks").unwrap()) {
        let i = index(&mut names.desk, name);
        l.desk_gross.resize(names.desk.len(), 0);
        l.desk_gross[i] = d.int("max_gross", 0);
    }
    for (name, s) in obj(v.get("strategies").unwrap()) {
        let i = index(&mut names.strat, name);
        l.strat.resize(names.strat.len(), StratLimits::default());
        let desk = index(&mut names.desk, &s.str("desk", ""));
        l.strat[i] = StratLimits { desk, rate: s.int("rate", 0), burst: s.int("burst", 0), max_open: s.int("max_open", 0) };
    }
    for (loc, s) in obj(v.get("instruments").unwrap()) {
        let k: usize = loc.parse().unwrap();
        if l.instr.len() <= k {
            l.instr.resize(k + 1, InstrLimits::default());
        }
        l.instr[k] = InstrLimits {
            collar_bp: s.int("collar_bp", 0),
            max_qty: s.int("max_qty", 0),
            max_notional: s.int("max_notional", 0),
            max_long: s.int("max_long", 0),
            max_short: s.int("max_short", 0),
        };
    }
    l
}

#[derive(Clone, Copy)]
struct Recent {
    t: i64,
    instr: usize,
    side: u8,
    qty: i64,
    price: i64,
}

#[derive(Clone)]
struct StratState {
    tokens: i64,
    last: i64,
    open: i64,
    recent: [Recent; DUP_SLOTS],
    head: usize,
    killed: bool,
}

#[derive(Clone, Copy, Default)]
struct Order {
    cl: u64,
    strat: usize,
    instr: usize,
    side: u8,
    qty: i64,
    price: i64,
    filled: i64,
}

pub struct Gate {
    lim: Limits,
    lim_t: i64,
    reference: Vec<i64>,
    ref_t: Vec<i64>,
    lo: Vec<i64>,
    hi: Vec<i64>,
    pos: Vec<i64>,
    open_buy: Vec<i64>,
    open_sell: Vec<i64>,
    desk_gross: Vec<i64>,
    desk_killed: Vec<bool>,
    firm_gross: i64,
    firm_killed: bool,
    strat: Vec<StratState>,
    orders: Vec<Order>,
    mask: u64,
}

impl Gate {
    pub fn new(l: &Limits, t: i64) -> Self {
        let n = 1 << 12;
        let mut g = Gate {
            lim: Limits::default(),
            lim_t: t,
            reference: vec![0; n],
            ref_t: vec![NEVER; n],
            lo: vec![0; n],
            hi: vec![0; n],
            pos: vec![0; n],
            open_buy: vec![0; n],
            open_sell: vec![0; n],
            desk_gross: vec![],
            desk_killed: vec![],
            firm_gross: 0,
            firm_killed: false,
            strat: vec![],
            orders: vec![Order::default(); 1 << 16],
            mask: (1 << 16) - 1,
        };
        g.set_limits(t, l);
        g
    }
    pub fn set_limits(&mut self, t: i64, l: &Limits) {
        self.lim = l.clone();
        self.lim_t = t;
        let empty = Recent { t: NEVER, instr: 0, side: 0, qty: 0, price: 0 };
        self.strat.resize(
            l.strat.len(),
            StratState { tokens: 0, last: -1, open: 0, recent: [empty; DUP_SLOTS], head: 0, killed: false },
        );
        self.desk_gross.resize(l.desk_gross.len(), 0);
        self.desk_killed.resize(l.desk_gross.len(), false);
        for (s, st) in self.strat.iter_mut().enumerate() {
            if st.last < 0 {
                st.tokens = l.strat[s].burst * ONE;
            }
        }
        for i in 0..l.instr.len().min(self.reference.len()) {
            self.band(i);
        }
    }
    fn band(&mut self, i: usize) {
        let bp = self.lim.instr.get(i).map_or(0, |x| x.collar_bp);
        let b = self.reference[i] * bp / 10_000;
        self.lo[i] = self.reference[i] - b;
        self.hi[i] = self.reference[i] + b;
    }
    pub fn heartbeat(&mut self, t: i64) {
        self.lim_t = t;
    }
    pub fn set_reference(&mut self, t: i64, instr: usize, price: i64) {
        self.reference[instr] = price;
        self.ref_t[instr] = t;
        self.band(instr);
    }

    /// The decision: b'.' or the code of the first failed check, and the mask of all failed checks.
    #[allow(clippy::too_many_arguments)]
    pub fn check(&mut self, t: i64, s: usize, instr: usize, side: u8, qty: i64, price: i64, cl: u64) -> (u8, u32) {
        let sl = &self.lim.strat[s];
        let il = &self.lim.instr[instr];
        let st = &self.strat[s];
        let buy = side == b'B';
        let notional = qty * price;
        let tokens = if st.last < 0 { st.tokens } else { (sl.burst * ONE).min(st.tokens + sl.rate * (t - st.last)) };
        let dup = st.recent.iter().any(|r| {
            t - r.t <= self.lim.dup_ns && r.instr == instr && r.side == side && r.qty == qty && r.price == price
        });
        let conds = [
            self.firm_killed || self.desk_killed[sl.desk] || st.killed,
            t - self.lim_t > self.lim.max_age,
            self.reference[instr] <= 0 || t - self.ref_t[instr] > self.lim.ref_max_age,
            if buy { price > self.hi[instr] } else { price < self.lo[instr] },
            qty > il.max_qty,
            notional > il.max_notional,
            buy && self.pos[instr] + self.open_buy[instr] + qty > il.max_long,
            !buy && -self.pos[instr] + self.open_sell[instr] + qty > il.max_short,
            st.open >= sl.max_open,
            self.desk_gross[sl.desk] + notional > self.lim.desk_gross[sl.desk]
                || self.firm_gross + notional > self.lim.firm_gross,
            tokens < ONE,
            self.lim.dup_ns != 0 && dup,
        ];
        let m = conds.iter().enumerate().fold(0u32, |m, (i, &c)| m | (u32::from(c) << i));
        if m != 0 {
            return (CODES[m.trailing_zeros() as usize], m);
        }
        let desk = sl.desk;
        let st = &mut self.strat[s];
        st.tokens = tokens - ONE;
        st.last = t;
        st.open += 1;
        st.recent[st.head] = Recent { t, instr, side, qty, price };
        st.head = (st.head + 1) % DUP_SLOTS;
        self.orders[(cl & self.mask) as usize] = Order { cl, strat: s, instr, side, qty, price, filled: 0 };
        if buy {
            self.open_buy[instr] += qty;
        } else {
            self.open_sell[instr] += qty;
        }
        self.desk_gross[desk] += notional;
        self.firm_gross += notional;
        (b'.', 0)
    }
    fn slot(&self, cl: u64) -> Option<usize> {
        let i = (cl & self.mask) as usize;
        (cl != 0 && self.orders[i].cl == cl).then_some(i)
    }
    pub fn on_fill(&mut self, cl: u64, qty: i64, price: i64) {
        let Some(i) = self.slot(cl) else { return };
        let o = &mut self.orders[i];
        o.filled += qty;
        let o = *o;
        if o.side == b'B' {
            self.pos[o.instr] += qty;
            self.open_buy[o.instr] -= qty;
        } else {
            self.pos[o.instr] -= qty;
            self.open_sell[o.instr] -= qty;
        }
        let d = qty * (price - o.price);
        self.desk_gross[self.lim.strat[o.strat].desk] += d;
        self.firm_gross += d;
        if o.filled == o.qty {
            self.on_done(cl);
        }
    }
    pub fn on_done(&mut self, cl: u64) {
        let Some(i) = self.slot(cl) else { return };
        let o = self.orders[i];
        let rest = o.qty - o.filled;
        if o.side == b'B' {
            self.open_buy[o.instr] -= rest;
        } else {
            self.open_sell[o.instr] -= rest;
        }
        self.desk_gross[self.lim.strat[o.strat].desk] -= rest * o.price;
        self.firm_gross -= rest * o.price;
        self.strat[o.strat].open -= 1;
        self.orders[i].cl = 0;
    }
    /// level b'F' firm, b'D' desk, b'S' strategy; returns the open orders under the node when asked to cancel.
    pub fn kill(&mut self, level: u8, idx: usize, cancel: bool) -> Vec<u64> {
        self.set_kill(level, idx, true);
        if !cancel {
            return vec![];
        }
        self.orders
            .iter()
            .filter(|o| {
                o.cl != 0
                    && (level == b'F'
                        || (level == b'S' && o.strat == idx)
                        || (level == b'D' && self.lim.strat[o.strat].desk == idx))
            })
            .map(|o| o.cl)
            .collect()
    }
    pub fn unkill(&mut self, level: u8, idx: usize) {
        self.set_kill(level, idx, false);
    }
    fn set_kill(&mut self, level: u8, idx: usize, on: bool) {
        match level {
            b'F' => self.firm_killed = on,
            b'D' => self.desk_killed[idx] = on,
            _ => self.strat[idx].killed = on,
        }
    }
    pub fn position(&self, instr: usize) -> i64 {
        self.pos[instr]
    }
}

/// Replays the fixture's events; returns the decision string.
pub fn replay(limits_json: &str, events: &str) -> String {
    let j = json::parse(limits_json).unwrap();
    let mut names = Names::default();
    let mut lim = std::collections::BTreeMap::new();
    for (k, v) in obj(&j) {
        lim.insert(k.parse::<i64>().unwrap(), parse_limits(v, &mut names));
    }
    let mut g: Option<Gate> = None;
    let mut out = String::new();
    for line in events.lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        let t: i64 = f[0].parse().unwrap();
        let num = |k: usize| f[k].parse::<i64>().unwrap();
        let level = |s: &str| match s {
            "firm" => b'F',
            "desk" => b'D',
            _ => b'S',
        };
        let idx = |names: &Names, lv: u8, s: &str| match lv {
            b'D' => names.desk.iter().position(|x| x == s).unwrap(),
            b'S' => names.strat.iter().position(|x| x == s).unwrap(),
            _ => 0,
        };
        match f[1] {
            "L" => {
                let l = &lim[&num(2)];
                match g.as_mut() {
                    None => g = Some(Gate::new(l, t)),
                    Some(gate) => gate.set_limits(t, l),
                }
            }
            "H" => g.as_mut().unwrap().heartbeat(t),
            "P" => g.as_mut().unwrap().set_reference(t, num(2) as usize, num(3)),
            "O" => {
                let s = names.strat.iter().position(|x| x == f[3]).unwrap();
                let (c, _) =
                    g.as_mut().unwrap().check(t, s, num(4) as usize, f[5].as_bytes()[0], num(6), num(7), num(2) as u64);
                out.push(c as char);
            }
            "F" => g.as_mut().unwrap().on_fill(num(2) as u64, num(3), num(4)),
            "X" => g.as_mut().unwrap().on_done(num(2) as u64),
            "K" => {
                let lv = level(f[2]);
                g.as_mut().unwrap().kill(lv, idx(&names, lv, f[3]), f[4] == "cancel");
            }
            "U" => {
                let lv = level(f[2]);
                g.as_mut().unwrap().unkill(lv, idx(&names, lv, f[3]));
            }
            _ => {}
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn replays_to_the_reference_decisions() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../data");
        let rd = |p: &str| std::fs::read_to_string(dir.join(p)).unwrap();
        let out = replay(&rd("limits.json"), &rd("events.txt"));
        let exp = rd("expected.txt");
        let mut lines = exp.lines();
        let head = lines.next().unwrap();
        assert_eq!(out, lines.next().unwrap());
        let mut h: u64 = 0xcbf29ce484222325;
        for b in out.bytes() {
            h = (h ^ u64::from(b)).wrapping_mul(0x100000001b3);
        }
        assert!(head.contains(&format!("{h:016x}")));
    }

    #[test]
    fn boundaries() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../data");
        let j = json::parse(&std::fs::read_to_string(dir.join("limits.json")).unwrap()).unwrap();
        let mut names = Names::default();
        let l = parse_limits(j.get("1").unwrap(), &mut names);
        let mut g = Gate::new(&l, 0);
        g.set_reference(0, 1, 1_000_000);
        let got: Vec<u8> = [
            (b'B', 100, 1_020_000),
            (b'B', 100, 1_020_001),
            (b'S', 100, 980_000),
            (b'S', 100, 979_999),
            (b'B', 2_000, 1_000_000),
            (b'B', 2_001, 1_000_000),
        ]
        .iter()
        .enumerate()
        .map(|(i, &(side, q, p))| g.check(i as i64 + 1, 0, 1, side, q, p, i as u64 + 1).0)
        .collect();
        assert_eq!(got, b".C.C.Q".to_vec());
        assert_eq!(g.check(l.max_age + 10, 0, 1, b'B', 100, 1_000_000, 9).0, b'S'); // stale limits: fail closed
    }
}
