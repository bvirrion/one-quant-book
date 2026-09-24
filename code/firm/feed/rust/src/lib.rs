//! Feed normaliser (build of Book 1, Chapter 28), Rust. Same wire format as `firm_feed.py`.
//! The decoder borrows the input and allocates nothing per message.

use std::collections::{BTreeMap, HashMap};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct Msg {
    pub kind: u8,
    pub locate: u16,
    pub ts: u64, // nanoseconds since midnight
    pub reference: u64,
    pub side: u8,
    pub shares: u32,
    pub price: u32, // 1/10,000 dollar
    pub matched: u64,
}

#[derive(Debug, PartialEq, Eq)]
pub enum DecodeError {
    TruncatedPrefix,
    TruncatedMessage,
    BadLength { kind: u8, len: usize },
}

fn be(b: &[u8]) -> u64 {
    b.iter().fold(0u64, |v, &x| (v << 8) | u64::from(x))
}

fn expected_length(kind: u8) -> Option<usize> {
    match kind {
        b'A' => Some(36),
        b'E' => Some(31),
        b'X' => Some(23),
        b'D' => Some(19),
        b'P' => Some(44),
        _ => None,
    }
}

/// An iterator over the framed messages of a buffer.
pub struct Decoder<'a> {
    buf: &'a [u8],
    failed: bool,
}

pub fn decode(buf: &[u8]) -> Decoder<'_> {
    Decoder { buf, failed: false }
}

impl Iterator for Decoder<'_> {
    type Item = Result<Msg, DecodeError>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.failed || self.buf.is_empty() {
            return None;
        }
        let fail = |s: &mut Self, e| {
            s.failed = true;
            Some(Err(e))
        };
        if self.buf.len() < 2 {
            return fail(self, DecodeError::TruncatedPrefix);
        }
        let n = be(&self.buf[..2]) as usize;
        if self.buf.len() < 2 + n {
            return fail(self, DecodeError::TruncatedMessage);
        }
        let body = &self.buf[2..2 + n];
        let kind = body.first().copied().unwrap_or(0);
        if expected_length(kind) != Some(n) {
            return fail(self, DecodeError::BadLength { kind, len: n });
        }
        let mut m = Msg {
            kind,
            locate: be(&body[1..3]) as u16,
            ts: be(&body[5..11]),
            reference: be(&body[11..19]),
            ..Msg::default()
        };
        match kind {
            b'A' => {
                m.side = body[19];
                m.shares = be(&body[20..24]) as u32;
                m.price = be(&body[32..36]) as u32;
            }
            b'E' => {
                m.shares = be(&body[19..23]) as u32;
                m.matched = be(&body[23..31]);
            }
            b'X' => m.shares = be(&body[19..23]) as u32,
            b'P' => {
                m.side = body[19];
                m.shares = be(&body[20..24]) as u32;
                m.price = be(&body[32..36]) as u32;
                m.matched = be(&body[36..44]);
            }
            _ => {}
        }
        self.buf = &self.buf[2 + n..];
        Some(Ok(m))
    }
}

#[derive(Debug, Clone, Copy)]
struct Order {
    side: u8,
    shares: u32,
    price: u32,
    locate: u16,
}

#[derive(Debug, Default, PartialEq, Eq)]
pub struct Summary {
    pub best_bid: Option<u32>,
    pub bid_size: u64,
    pub best_ask: Option<u32>,
    pub ask_size: u64,
    pub trades: u64,
    pub shares_traded: u64,
    pub live_orders: u64,
}

#[derive(Default)]
pub struct Book {
    orders: HashMap<u64, Order>,
    levels: HashMap<(u16, u8), BTreeMap<u32, u64>>,
    trades: HashMap<u16, (u64, u64)>,
    last_ts: u64,
    pub errors: u64,
}

impl Book {
    fn reduce(&mut self, reference: u64, shares: Option<u32>) -> bool {
        let Some(o) = self.orders.get_mut(&reference) else {
            self.errors += 1;
            return false;
        };
        let mut q = shares.unwrap_or(o.shares);
        if q > o.shares {
            self.errors += 1;
            q = o.shares;
        }
        let level = self.levels.entry((o.locate, o.side)).or_default();
        if let Some(sz) = level.get_mut(&o.price) {
            *sz -= u64::from(q);
            if *sz == 0 {
                level.remove(&o.price);
            }
        }
        o.shares -= q;
        if o.shares == 0 {
            self.orders.remove(&reference);
        }
        true
    }

    pub fn apply(&mut self, m: &Msg) {
        if m.ts < self.last_ts {
            self.errors += 1;
        }
        self.last_ts = self.last_ts.max(m.ts);
        match m.kind {
            b'A' => {
                if self.orders.contains_key(&m.reference) {
                    self.errors += 1;
                    return;
                }
                self.orders.insert(m.reference, Order { side: m.side, shares: m.shares, price: m.price, locate: m.locate });
                *self.levels.entry((m.locate, m.side)).or_default().entry(m.price).or_default() += u64::from(m.shares);
            }
            b'E' => {
                if self.reduce(m.reference, Some(m.shares)) {
                    let t = self.trades.entry(m.locate).or_default();
                    t.0 += 1;
                    t.1 += u64::from(m.shares);
                }
            }
            b'X' => {
                self.reduce(m.reference, Some(m.shares));
            }
            b'D' => {
                self.reduce(m.reference, None);
            }
            b'P' => {
                let t = self.trades.entry(m.locate).or_default();
                t.0 += 1;
                t.1 += u64::from(m.shares);
            }
            _ => self.errors += 1,
        }
    }

    pub fn summary(&self, locate: u16) -> Summary {
        let bid = self.levels.get(&(locate, b'B')).and_then(|l| l.iter().next_back());
        let ask = self.levels.get(&(locate, b'S')).and_then(|l| l.iter().next());
        let (trades, shares_traded) = self.trades.get(&locate).copied().unwrap_or_default();
        Summary {
            best_bid: bid.map(|(p, _)| *p),
            bid_size: bid.map_or(0, |(_, q)| *q),
            best_ask: ask.map(|(p, _)| *p),
            ask_size: ask.map_or(0, |(_, q)| *q),
            trades,
            shares_traded,
            live_orders: self.orders.values().filter(|o| o.locate == locate).count() as u64,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn data(name: &str) -> Vec<u8> {
        std::fs::read(format!("{}/../data/{name}", env!("CARGO_MANIFEST_DIR"))).expect("sample file")
    }

    #[test]
    fn sample_matches_the_python_summary() {
        let buf = data("sample.itch");
        let mut book = Book::default();
        let mut n = 0;
        for m in decode(&buf) {
            book.apply(&m.expect("clean sample"));
            n += 1;
        }
        let want: Vec<u64> = String::from_utf8(data("sample.expected"))
            .unwrap()
            .split_whitespace()
            .map(|x| x.parse().unwrap())
            .collect();
        let s = book.summary(7);
        assert_eq!(n, 2020);
        assert_eq!(book.errors, 0);
        assert_eq!(
            vec![u64::from(s.best_bid.unwrap()), s.bid_size, u64::from(s.best_ask.unwrap()), s.ask_size, s.trades, s.shares_traded, s.live_orders],
            want
        );
    }

    #[test]
    fn truncation_is_an_error_and_stops_the_iterator() {
        let buf = data("sample.itch");
        let cut = &buf[..buf.len() - 1];
        let results: Vec<_> = decode(cut).collect();
        assert_eq!(results.last(), Some(&Err(DecodeError::TruncatedMessage)));
        assert_eq!(results.iter().filter(|r| r.is_err()).count(), 1);
    }

    #[test]
    fn a_length_that_does_not_match_the_type_is_refused() {
        let mut frame = vec![0u8, 19, b'A'];
        frame.extend([0u8; 18]);
        assert_eq!(decode(&frame).next(), Some(Err(DecodeError::BadLength { kind: b'A', len: 19 })));
    }

    #[test]
    fn unknown_order_is_counted() {
        let mut book = Book::default();
        book.apply(&Msg { kind: b'E', reference: 42, shares: 100, ..Msg::default() });
        assert_eq!(book.errors, 1);
        assert_eq!(book.summary(0), Summary::default());
    }
}
