//! firm.nbbo -- consolidated best bid and offer (build of Chapter 9, One Quant Book 1).

pub const MAX_VENUES: usize = 32;

#[derive(Clone, Copy, Default)]
struct Quote {
    bid: i64,
    bid_size: i64,
    ask: i64,
    ask_size: i64,
    live: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Nbbo {
    pub bid: i64,
    pub bid_size: i64,
    pub bid_venues: u32,
    pub ask: i64,
    pub ask_size: i64,
    pub ask_venues: u32,
}

impl Nbbo {
    pub fn locked(&self) -> bool {
        self.bid == self.ask
    }
    pub fn crossed(&self) -> bool {
        self.bid > self.ask
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct BadQuote;

pub struct NbboBuilder {
    round_lot: i64,
    quotes: [Quote; MAX_VENUES],
}

impl NbboBuilder {
    pub fn new(round_lot: i64) -> Self {
        Self { round_lot, quotes: [Quote::default(); MAX_VENUES] }
    }

    /// Stores the venue's quote; returns the new NBBO if it changed.
    pub fn update(&mut self, venue: usize, bid: i64, bid_size: i64, ask: i64, ask_size: i64) -> Result<Option<Nbbo>, BadQuote> {
        if venue >= MAX_VENUES || bid <= 0 || ask <= 0 || bid_size < 0 || ask_size < 0 {
            return Err(BadQuote);
        }
        let before = self.nbbo();
        self.quotes[venue] = Quote { bid, bid_size, ask, ask_size, live: true };
        let after = self.nbbo();
        Ok(if after == before { None } else { after })
    }

    pub fn nbbo(&self) -> Option<Nbbo> {
        let (mut bid, mut bid_size, mut bid_venues) = (i64::MIN, 0, 0u32);
        let (mut ask, mut ask_size, mut ask_venues) = (i64::MAX, 0, 0u32);
        for (v, q) in self.quotes.iter().enumerate().filter(|(_, q)| q.live) {
            if q.bid_size >= self.round_lot {
                if q.bid > bid {
                    (bid, bid_size, bid_venues) = (q.bid, 0, 0);
                }
                if q.bid == bid {
                    bid_size += q.bid_size;
                    bid_venues |= 1 << v;
                }
            }
            if q.ask_size >= self.round_lot {
                if q.ask < ask {
                    (ask, ask_size, ask_venues) = (q.ask, 0, 0);
                }
                if q.ask == ask {
                    ask_size += q.ask_size;
                    ask_venues |= 1 << v;
                }
            }
        }
        (bid_venues != 0 && ask_venues != 0).then_some(Nbbo { bid, bid_size, bid_venues, ask, ask_size, ask_venues })
    }

    pub fn trades_through(&self, side: i32, price: i64) -> bool {
        match self.nbbo() {
            None => false,
            Some(n) => {
                if side > 0 {
                    price > n.ask
                } else {
                    price < n.bid
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn book() -> NbboBuilder {
        let mut b = NbboBuilder::new(100);
        b.update(0, 100_000, 300, 100_200, 500).unwrap();
        b.update(1, 100_100, 200, 100_200, 100).unwrap();
        b.update(2, 100_100, 400, 100_300, 900).unwrap();
        b
    }

    #[test]
    fn best_prices_sizes_and_venues() {
        let n = book().nbbo().unwrap();
        assert_eq!((n.bid, n.bid_size, n.bid_venues), (100_100, 600, 0b110));
        assert_eq!((n.ask, n.ask_size, n.ask_venues), (100_200, 600, 0b011));
    }

    #[test]
    fn odd_lots_locks_crosses_and_trade_throughs() {
        let mut b = book();
        assert_eq!(b.update(3, 100_150, 60, 100_400, 100), Ok(None));
        assert_eq!(b.update(3, 100_150, 100, 100_400, 100).unwrap().unwrap().bid, 100_150);
        assert!(b.trades_through(1, 100_300) && !b.trades_through(1, 100_200));
        assert!(b.update(0, 100_200, 300, 100_300, 500).unwrap().unwrap().locked());
        assert!(b.update(0, 100_250, 300, 100_300, 500).unwrap().unwrap().crossed());
        assert_eq!(b.update(99, 1, 1, 1, 1), Err(BadQuote));
    }
}
