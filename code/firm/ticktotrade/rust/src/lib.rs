//! firm.ticktotrade (Rust): the trading path of chapter 26 replayed offline, twin of the C++20 `firm::t2t::Path`: the
//! recorded line decoded by the feed handler, each event through the strategy engine, each order through the risk
//! gate and the order gateway. Produces the same orders, hash for hash (data/expected.txt).

use firm_feedhandler as fh;
use firm_ordergw::Gateway;
use firm_riskgate::{Gate, InstrLimits, Limits, StratLimits};
use firm_stratengine::{read_events, Action, Engine, Params, TimedEvent};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct OrderOut {
    pub t: u64,
    pub kind: u8,
    pub side: u8,
    pub cl: u64,
    pub new_cl: u64,
    pub qty: u32,
    pub price: u32,
}

pub fn order_hash(v: &[OrderOut]) -> u64 {
    let mut h: u64 = 0xCBF29CE484222325;
    let mut mix = |b: &[u8]| {
        for &x in b {
            h = (h ^ u64::from(x)).wrapping_mul(0x100000001B3);
        }
    };
    for o in v {
        mix(&o.t.to_le_bytes());
        mix(&[o.kind, o.side]);
        mix(&o.cl.to_le_bytes());
        mix(&o.new_cl.to_le_bytes());
        mix(&o.qty.to_le_bytes());
        mix(&o.price.to_le_bytes());
    }
    h
}

pub fn harness_limits() -> Limits {
    let big = 1i64 << 60;
    let mut instr = vec![InstrLimits::default(); 2];
    instr[1] = InstrLimits { collar_bp: 10_000, max_qty: 100_000, max_notional: 1 << 50, max_long: 1_000_000, max_short: 1_000_000 };
    Limits {
        max_age: 1 << 62,
        ref_max_age: 1 << 62,
        dup_ns: 0,
        firm_gross: big,
        desk_gross: vec![big],
        strat: vec![StratLimits { desk: 0, rate: 1_000_000, burst: 10_000, max_open: 1_000_000 }],
        instr,
    }
}

pub struct Path {
    engine: Engine,
    gate: Gate,
    gw: Gateway,
    live: [u64; 2],
    quote: [u64; 2],
    replacing: [u64; 2],
    pub out: Vec<OrderOut>,
    pub refused_risk: u64,
    pub refused_gateway: u64,
}

impl Path {
    pub fn new(tick: u32) -> Self {
        Path {
            engine: Engine::new(tick, Params::default()),
            gate: Gate::new(&harness_limits(), 0),
            gw: Gateway::new(1_000_000_000, 1_000_000_000, 1_000_000_000, 1_000_000_000),
            live: [0; 2],
            quote: [0; 2],
            replacing: [0; 2],
            out: vec![],
            refused_risk: 0,
            refused_gateway: 0,
        }
    }

    pub fn on_event(&mut self, e: &TimedEvent) {
        let first = self.engine.actions.len();
        self.engine.run(std::slice::from_ref(e), &[]);
        let new: Vec<Action> = self.engine.actions[first..].to_vec();
        for a in &new {
            self.act(a);
        }
    }

    fn act(&mut self, a: &Action) {
        let t = a.t as i64;
        let k = usize::from(a.side != b'B');
        let mut o = OrderOut { t: a.t, kind: 0, side: a.side, cl: a.id, new_cl: 0, qty: a.qty, price: a.price };
        let mut sent = false;
        match a.kind {
            b'N' | b'R' => {
                if a.kind == b'R' && self.quote[k] != 0 {
                    self.gate.on_done(self.quote[k]);
                }
                self.gate.set_reference(t, 1, i64::from(a.price));
                let (code, _) = self.gate.check(t, 0, 1, a.side, i64::from(a.qty), i64::from(a.price), a.id);
                if code != b'.' {
                    self.refused_risk += 1;
                    return;
                }
                if a.kind == b'R' && self.live[k] != 0 {
                    let old = self.live[k];
                    if self.gw.replace(t, old, a.id, i64::from(a.qty), i64::from(a.price)).is_ok() {
                        o.kind = b'U';
                        o.cl = old;
                        o.new_cl = a.id;
                        self.replacing[k] = old;
                        sent = true;
                    }
                }
                if !sent {
                    sent = self.gw.new_order(t, a.id, a.side, i64::from(a.qty), i64::from(a.price)).is_ok();
                    o.kind = b'O';
                }
                self.quote[k] = a.id;
            }
            b'P' => {
                self.gate.on_done(a.id);
                let cl = if self.live[k] != 0 { self.live[k] } else { a.id };
                sent = self.gw.cancel(t, cl).is_ok();
                o.kind = b'X';
                o.cl = cl;
                self.live[k] = 0;
                self.quote[k] = 0;
                self.replacing[k] = 0;
            }
            b'A' => {
                if self.replacing[k] != 0 {
                    self.gw.on_report(b'U', self.replacing[k], 0, 0, b' ', a.id);
                    self.replacing[k] = 0;
                } else {
                    self.gw.on_report(b'A', a.id, 0, 0, b' ', 0);
                }
                self.live[k] = a.id;
                return;
            }
            b'F' => {
                self.gw.on_report(b'E', a.id, i64::from(a.qty), 0, b' ', 0);
                self.gate.on_fill(a.id, i64::from(a.qty), i64::from(a.price));
                self.live[k] = 0;
                self.quote[k] = 0;
                return;
            }
            _ => return,
        }
        if !sent {
            self.refused_gateway += 1;
            return;
        }
        self.out.push(o);
    }
}

/// The recorded line decoded by the feed handler (sent on both lines), as the engine's timed events.
pub fn events_from_line(raw: &[u8]) -> Vec<TimedEvent> {
    let pk = fh::recorded(raw);
    let mut h = fh::Handler::new(None);
    h.run(&pk, &pk, &[]);
    let mut rec = Vec::with_capacity(h.events.len() * 48);
    for e in &h.events {
        let mut b = [0u8; 48];
        b[0] = e.kind;
        b[1] = e.side;
        b[2..4].copy_from_slice(&e.locate.to_le_bytes());
        b[4..12].copy_from_slice(&e.seq.to_le_bytes());
        b[12..20].copy_from_slice(&e.ts.to_le_bytes());
        b[20..28].copy_from_slice(&e.r#ref.to_le_bytes());
        b[28..36].copy_from_slice(&e.ref2.to_le_bytes());
        b[36..40].copy_from_slice(&e.price.to_le_bytes());
        b[40..48].copy_from_slice(&e.qty.to_le_bytes());
        rec.extend_from_slice(&b);
    }
    read_events(&rec)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_line_gives_the_committed_orders() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
        let raw = std::fs::read(dir.join("ticktotrade/data/line.bin")).unwrap();
        let ev = events_from_line(&raw);
        let small = std::fs::read(dir.join("bookbuilder/data/events_small.bin")).unwrap();
        assert_eq!(ev.len(), small.len() / 48);
        let mut p = Path::new(1);
        for e in &ev {
            p.on_event(e);
        }
        let want = std::fs::read_to_string(dir.join("ticktotrade/data/expected.txt")).unwrap();
        let h = format!("{:016x}", order_hash(&p.out));
        assert!(want.contains(&h), "orders hash {h}, {} orders", p.out.len());
        assert_eq!((p.refused_risk, p.refused_gateway), (0, 0));
    }
}
