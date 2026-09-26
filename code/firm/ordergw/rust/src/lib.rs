//! firm.ordergw (Rust): the order gateway, twin of the C++20 and Python ones. A table-driven order state machine with
//! pending states, worst-case exposure kept as running sums, a token-bucket throttle in integer nano-tokens, and
//! cancel-fill race counting; orders live in a ring indexed by client order identifier. Replays the journals in
//! data/ to the summaries in data/expected.txt.

pub const STATE_NAMES: [&str; 8] =
    ["pending_new", "live", "partial", "pending_cancel", "pending_replace", "filled", "cancelled", "rejected"];
pub const EVENT_NAMES: [&str; 9] =
    ["ack", "reject", "fill", "fill_all", "cancel_req", "cancel_ack", "too_late", "replace_req", "replace_ack"];
const PN: u8 = 0;
const LIVE: u8 = 1;
const PART: u8 = 2;
const PC: u8 = 3;
const PR: u8 = 4;
const FILLED: u8 = 5;
const CXL: u8 = 6;
const REJ: u8 = 7;
pub const X: u8 = 0xff;
const ACK: usize = 0;
const REJECT: usize = 1;
const FILL: usize = 2;
const FILL_ALL: usize = 3;
const CANCEL_REQ: usize = 4;
const CANCEL_ACK: usize = 5;
const TOO_LATE: usize = 6;
const REPLACE_REQ: usize = 7;
const REPLACE_ACK: usize = 8;

/// TABLE[state][event] -> next state (X: not allowed). CANCEL_ACK is any cancellation the venue reports, ours or
/// its own (disconnect, halt, mass cancel, expiry), so it reaches every open state.
pub const TABLE: [[u8; 9]; 8] = [
    [LIVE, REJ, PART, FILLED, PC, CXL, X, X, X],
    [X, X, PART, FILLED, PC, CXL, X, PR, X],
    [X, X, PART, FILLED, PC, CXL, X, PR, X],
    [PC, X, PC, FILLED, X, CXL, FILLED, X, X],
    [X, X, PR, FILLED, X, CXL, FILLED, X, LIVE],
    [X, X, X, X, X, X, FILLED, X, X],
    [X, X, X, X, X, X, CXL, X, X],
    [X; 9],
];

const ONE: i64 = 1_000_000_000;

pub struct TokenBucket {
    rate: i64,
    cap: i64,
    tokens: i64,
    last: Option<i64>,
}

impl TokenBucket {
    pub fn new(rate_per_s: i64, burst: i64) -> Self {
        TokenBucket { rate: rate_per_s, cap: burst * ONE, tokens: burst * ONE, last: None }
    }
    pub fn allow(&mut self, t: i64) -> bool {
        if let Some(l) = self.last {
            self.tokens = self.cap.min(self.tokens + self.rate * (t - l));
        }
        self.last = Some(t);
        if self.tokens < ONE {
            return false;
        }
        self.tokens -= ONE;
        true
    }
}

#[derive(Clone, Copy, Default)]
pub struct Order {
    pub cl: u64,
    pub side: u8,
    pub state: u8,
    pub qty: i64,
    pub price: i64,
    pub filled: i64,
    pub pending_qty: i64,
    pub pending_price: i64,
    pub new_cl: u64,
}

impl Order {
    pub fn leaves(&self) -> i64 {
        if self.state >= FILLED {
            0
        } else {
            self.qty - self.filled
        }
    }
    pub fn worst_leaves(&self) -> i64 {
        if self.state == PR {
            (self.qty - self.filled).max(self.pending_qty)
        } else {
            self.leaves()
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Refused {
    Throttle = 0,
    Exposure = 1,
    State = 2,
}

pub struct Gateway {
    bucket: TokenBucket,
    max_long: i64,
    max_short: i64,
    orders: Vec<Order>,
    mask: u64,
    pub position: i64,
    exp_b: i64,
    exp_s: i64,
    pub races: i64,
    pub sent: i64,
    pub refused: [i64; 3],
}

impl Gateway {
    pub fn new(rate_per_s: i64, burst: i64, max_long: i64, max_short: i64) -> Self {
        Gateway {
            bucket: TokenBucket::new(rate_per_s, burst),
            max_long,
            max_short,
            orders: vec![Order::default(); 1 << 16],
            mask: (1 << 16) - 1,
            position: 0,
            exp_b: 0,
            exp_s: 0,
            races: 0,
            sent: 0,
            refused: [0; 3],
        }
    }
    pub fn worst_long(&self) -> i64 {
        self.position + self.exp_b
    }
    pub fn worst_short(&self) -> i64 {
        -self.position + self.exp_s
    }
    fn slot(&self, cl: u64) -> Option<usize> {
        let i = (cl & self.mask) as usize;
        (self.orders[i].cl == cl && cl != 0).then_some(i)
    }
    fn add(&mut self, i: usize, sign: i64) {
        let o = self.orders[i];
        if o.side == b'B' {
            self.exp_b += sign * o.worst_leaves();
        } else {
            self.exp_s += sign * o.worst_leaves();
        }
    }
    fn refuse(&mut self, why: Refused) -> Result<(), Refused> {
        self.refused[why as usize] += 1;
        Err(why)
    }
    fn throttle(&mut self, t: i64) -> Result<(), Refused> {
        if !self.bucket.allow(t) {
            return self.refuse(Refused::Throttle);
        }
        self.sent += 1;
        Ok(())
    }

    pub fn new_order(&mut self, t: i64, cl: u64, side: u8, qty: i64, price: i64) -> Result<(), Refused> {
        if (side == b'B' && self.worst_long() + qty > self.max_long)
            || (side == b'S' && self.worst_short() + qty > self.max_short)
        {
            return self.refuse(Refused::Exposure);
        }
        let i = (cl & self.mask) as usize;
        if self.orders[i].cl != 0 && self.orders[i].state < FILLED {
            return self.refuse(Refused::State);
        }
        self.throttle(t)?;
        self.orders[i] = Order { cl, side, state: PN, qty, price, ..Order::default() };
        self.add(i, 1);
        Ok(())
    }
    pub fn cancel(&mut self, t: i64, cl: u64) -> Result<(), Refused> {
        let Some(i) = self.slot(cl).filter(|&i| self.orders[i].state <= PART) else {
            return self.refuse(Refused::State);
        };
        self.throttle(t)?;
        self.add(i, -1);
        self.orders[i].state = TABLE[self.orders[i].state as usize][CANCEL_REQ];
        self.add(i, 1);
        Ok(())
    }
    pub fn replace(&mut self, t: i64, cl: u64, new_cl: u64, qty: i64, price: i64) -> Result<(), Refused> {
        let Some(i) = self.slot(cl).filter(|&i| matches!(self.orders[i].state, LIVE | PART)) else {
            return self.refuse(Refused::State);
        };
        let o = self.orders[i];
        let extra = (qty - (o.qty - o.filled)).max(0);
        if (o.side == b'B' && self.worst_long() + extra > self.max_long)
            || (o.side == b'S' && self.worst_short() + extra > self.max_short)
        {
            return self.refuse(Refused::Exposure);
        }
        self.throttle(t)?;
        self.add(i, -1);
        let o = &mut self.orders[i];
        o.state = TABLE[o.state as usize][REPLACE_REQ];
        o.pending_qty = qty;
        o.pending_price = price;
        o.new_cl = new_cl;
        self.add(i, 1);
        Ok(())
    }
    /// A report from the venue; false if the state machine does not allow it.
    pub fn on_report(&mut self, kind: u8, cl: u64, qty: i64, leaves: i64, reason: u8, new_cl: u64) -> bool {
        let Some(i) = self.slot(cl) else { return true };
        let st = self.orders[i].state;
        let ev = match kind {
            b'A' => ACK,
            b'E' => {
                if st == PC || st == PR {
                    self.races += 1;
                }
                if leaves == 0 {
                    FILL_ALL
                } else {
                    FILL
                }
            }
            b'C' => CANCEL_ACK,
            b'U' => REPLACE_ACK,
            b'J' if reason == b'L' => TOO_LATE,
            b'J' => REJECT,
            _ => return false,
        };
        let next = TABLE[st as usize][ev];
        if next == X {
            return false;
        }
        self.add(i, -1);
        let side = self.orders[i].side;
        let o = &mut self.orders[i];
        o.state = next;
        if kind == b'E' {
            o.filled += qty;
            self.position += if side == b'B' { qty } else { -qty };
        } else if kind == b'U' {
            o.qty = o.filled + o.pending_qty;
            o.price = o.pending_price;
        }
        self.add(i, 1);
        if kind == b'U' {
            let mut moved = self.orders[i];
            moved.cl = if moved.new_cl != 0 { moved.new_cl } else { new_cl };
            self.orders[i].cl = 0;
            let j = (moved.cl & self.mask) as usize;
            self.orders[j] = moved;
        }
        true
    }
    pub fn summary(&self) -> String {
        let mut n = [0usize; 8];
        let mut total = 0;
        for o in self.orders.iter().filter(|o| o.cl != 0) {
            n[o.state as usize] += 1;
            total += 1;
        }
        let mut st: Vec<(&str, usize)> = (0..8).filter(|&s| n[s] > 0).map(|s| (STATE_NAMES[s], n[s])).collect();
        st.sort();
        let states: Vec<String> = st.iter().map(|(k, v)| format!("{k}:{v}")).collect();
        format!(
            "orders {} position {} races {} sent {} refused {}/{}/{} worst {}/{} states {}",
            total,
            self.position,
            self.races,
            self.sent,
            self.refused[0],
            self.refused[1],
            self.refused[2],
            self.worst_long(),
            self.worst_short(),
            states.join(",")
        )
    }
}

/// Replays a journal (see make_ordergw_fixtures.py); returns the gateway and the number of mismatches.
pub fn replay(text: &str, rate: i64, burst: i64) -> (Gateway, usize) {
    let mut g = Gateway::new(rate, burst, 1_000_000_000, 1_000_000_000);
    let mut bad = 0;
    for line in text.lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        let t: i64 = f[0].parse().unwrap();
        let num = |k: usize| f[k].parse::<i64>().unwrap();
        if f[1] == "Q" {
            let r = match f[2] {
                "N" => g.new_order(t, num(3) as u64, f[4].as_bytes()[0], num(5), num(6)),
                "X" => g.cancel(t, num(3) as u64),
                _ => g.replace(t, num(3) as u64, num(4) as u64, num(5), num(6)),
            };
            bad += usize::from(r.is_ok() != (f[f.len() - 1] == "send"));
        } else {
            let reason = if f[7] == "-" { b' ' } else { f[7].as_bytes()[0] };
            bad += usize::from(!g.on_report(f[2].as_bytes()[0], num(3) as u64, num(4), num(6), reason, num(8) as u64));
        }
    }
    (g, bad)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn data(name: &str) -> String {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../data");
        std::fs::read_to_string(dir.join(name)).unwrap()
    }

    #[test]
    fn table_matches_the_reference() {
        let rows: Vec<String> = data("table.txt").lines().map(String::from).collect();
        let mut n = 0;
        for (s, row) in TABLE.iter().enumerate() {
            for (e, &next) in row.iter().enumerate() {
                if next != X {
                    n += 1;
                    let want = format!("{} {} {}", STATE_NAMES[s], EVENT_NAMES[e], STATE_NAMES[next as usize]);
                    assert!(rows.contains(&want), "{want}");
                }
            }
        }
        assert_eq!(n, rows.len());
    }

    #[test]
    fn journals_replay_to_the_expected_summaries() {
        for line in data("expected.txt").lines() {
            let (name, want) = line.split_once(' ').unwrap();
            let (rate, burst) = if name == "replace" { (300, 2) } else { (10_000, 100) };
            let (g, bad) = replay(&data(&format!("journal_{name}.txt")), rate, burst);
            assert_eq!(bad, 0, "{name}");
            assert_eq!(g.summary(), want, "{name}");
        }
    }

    #[test]
    fn worst_case_accounting_refuses_the_second_order() {
        let mut g = Gateway::new(1000, 50, 100, 100);
        g.new_order(0, 1, b'B', 100, 1000).unwrap();
        assert!(g.on_report(b'A', 1, 0, 0, b' ', 0));
        g.cancel(20, 1).unwrap();
        assert_eq!(g.new_order(21, 2, b'B', 100, 1000), Err(Refused::Exposure));
        assert!(g.on_report(b'E', 1, 100, 0, b' ', 0));
        assert!(g.on_report(b'J', 1, 0, 0, b'L', 0));
        assert_eq!((g.position, g.races), (100, 1));
        let mut b = TokenBucket::new(1000, 2);
        assert_eq!([b.allow(0), b.allow(0), b.allow(0), b.allow(1_000_000)], [true, true, false, true]);
    }
}
