//! firm.ratelimit -- weight-based rate-limit governor (build of Chapter 15, One Quant Book 3), Rust
//! twin of the C++20 governor and of firm_ratelimit.py. Fixed windows aligned on the epoch; a request
//! consumes its weight in the weight rules and one unit in the order rules if it is an order; 429 and
//! 418 block until retry-after. Times in milliseconds.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Weight,
    Orders,
}

#[derive(Clone, Debug)]
pub struct Rule {
    pub kind: Kind,
    pub interval_ms: i64,
    pub limit: i64,
    window: i64,
    used: i64,
}

impl Rule {
    pub fn new(kind: Kind, interval_ms: i64, limit: i64) -> Self {
        Rule { kind, interval_ms, limit, window: -1, used: 0 }
    }
    fn room(&self, now: i64) -> i64 {
        if now / self.interval_ms != self.window { self.limit } else { self.limit - self.used }
    }
    fn consume(&mut self, now: i64, units: i64) {
        let w = now / self.interval_ms;
        if w != self.window {
            self.window = w;
            self.used = 0;
        }
        self.used += units;
    }
    fn wait_ms(&self, now: i64) -> i64 {
        (now / self.interval_ms + 1) * self.interval_ms - now
    }
    fn need(&self, weight: i64, is_order: bool) -> i64 {
        match self.kind {
            Kind::Weight => weight,
            Kind::Orders => i64::from(is_order),
        }
    }
}

#[derive(Clone, Debug)]
pub struct Governor {
    rules: Vec<Rule>,
    blocked_until: i64,
    pub log: Vec<String>,
}

impl Governor {
    pub fn new(rules: Vec<Rule>) -> Self {
        Governor { rules, blocked_until: 0, log: Vec::new() }
    }

    /// (allowed, milliseconds to wait if not)
    pub fn try_send(&mut self, now: i64, weight: i64, is_order: bool) -> (bool, i64) {
        if now < self.blocked_until {
            return (false, self.blocked_until - now);
        }
        for r in &self.rules {
            let need = r.need(weight, is_order);
            if need > 0 && r.room(now) < need {
                return (false, r.wait_ms(now));
            }
        }
        for r in &mut self.rules {
            let need = r.need(weight, is_order);
            if need > 0 {
                r.consume(now, need);
            }
        }
        (true, 0)
    }

    pub fn on_status(&mut self, now: i64, status: u16, retry_after_ms: i64) {
        if status == 429 || status == 418 {
            self.blocked_until = self.blocked_until.max(now + retry_after_ms);
            self.log.push(format!("{status}@{now}"));
        }
    }
}

pub fn binance_like() -> Governor {
    Governor::new(vec![
        Rule::new(Kind::Weight, 60_000, 6_000),
        Rule::new(Kind::Orders, 10_000, 100),
        Rule::new(Kind::Orders, 86_400_000, 200_000),
    ])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn weight_window_and_wait() {
        let mut g = Governor::new(vec![Rule::new(Kind::Weight, 60_000, 100)]);
        assert_eq!(g.try_send(1_000, 60, false), (true, 0));
        assert_eq!(g.try_send(2_000, 50, false), (false, 58_000));
        assert_eq!(g.try_send(60_000, 50, false), (true, 0));
    }

    #[test]
    fn orders_counted_separately() {
        let mut g = binance_like();
        for i in 0..100 {
            assert!(g.try_send(i, 1, true).0);
        }
        assert_eq!(g.try_send(100, 1, true), (false, 9_900));
        assert_eq!(g.try_send(100, 1, false), (true, 0));
    }

    #[test]
    fn backoff_on_429_and_418() {
        let mut g = binance_like();
        g.on_status(5_000, 429, 3_000);
        assert_eq!(g.try_send(6_000, 1, false), (false, 2_000));
        g.on_status(9_000, 418, 120_000);
        assert_eq!(g.try_send(100_000, 1, false), (false, 29_000));
        assert_eq!(g.log, vec!["429@5000".to_string(), "418@9000".to_string()]);
    }
}
