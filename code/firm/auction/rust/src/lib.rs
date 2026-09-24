//! firm.auction -- call-auction uncrossing (build of Chapter 13, One Quant Book 1).
//! Four rules: executable volume, surplus, market pressure, reference price.

use std::collections::BTreeSet;

#[derive(Clone, Debug)]
pub struct AuctionOrder {
    pub id: &'static str,
    pub side: i32,
    pub quantity: i64,
    pub price: Option<i64>,
    pub seq: i64,
}

#[derive(Debug, Default, PartialEq, Eq)]
pub struct Uncrossing {
    pub price: Option<i64>,
    pub volume: i64,
    pub surplus: i64,
    pub fills: Vec<(&'static str, i64)>,
}

fn eligible(o: &AuctionOrder, side: i32, p: i64) -> bool {
    o.side == side && o.price.is_none_or(|x| if side > 0 { x >= p } else { x <= p })
}

fn interest(orders: &[AuctionOrder], side: i32, p: i64) -> i64 {
    orders.iter().filter(|o| eligible(o, side, p)).map(|o| o.quantity).sum()
}

pub fn uncross(orders: &[AuctionOrder], reference: i64) -> Uncrossing {
    let mut prices: BTreeSet<i64> = orders.iter().filter_map(|o| o.price).collect();
    prices.insert(reference);
    let mut rows: Vec<(i64, i64, i64)> =
        prices.iter().map(|&p| (p, interest(orders, 1, p), interest(orders, -1, p))).collect();
    let best = rows.iter().map(|r| r.1.min(r.2)).max().unwrap_or(0);
    if best == 0 {
        return Uncrossing::default();
    }
    rows.retain(|r| r.1.min(r.2) == best); // rule 1
    let least = rows.iter().map(|r| (r.1 - r.2).abs()).min().unwrap();
    rows.retain(|r| (r.1 - r.2).abs() == least); // rule 2
    let pick = if rows.iter().all(|r| r.1 > r.2) {
        *rows.last().unwrap() // rule 3: buy pressure
    } else if rows.iter().all(|r| r.1 < r.2) {
        rows[0] // rule 3: sell pressure
    } else {
        *rows.iter().min_by_key(|r| ((r.0 - reference).abs(), r.0)).unwrap() // rule 4
    };
    let mut fills = Vec::new();
    for side in [1, -1] {
        let mut el: Vec<&AuctionOrder> = orders.iter().filter(|o| eligible(o, side, pick.0)).collect();
        el.sort_by_key(|o| (o.price.is_some(), -(side as i64) * o.price.unwrap_or(0), o.seq));
        let mut left = best;
        for o in el {
            let q = left.min(o.quantity);
            if q > 0 {
                fills.push((o.id, q));
            }
            left -= q;
        }
    }
    Uncrossing { price: Some(pick.0), volume: best, surplus: pick.1 - pick.2, fills }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn o(id: &'static str, side: i32, quantity: i64, price: Option<i64>, seq: i64) -> AuctionOrder {
        AuctionOrder { id, side, quantity, price, seq }
    }

    #[test]
    fn chapter_example() {
        let book = [
            o("b1", 1, 300, None, 1), o("b2", 1, 500, Some(1003), 2), o("b3", 1, 400, Some(1001), 3),
            o("b4", 1, 600, Some(1000), 4), o("s1", -1, 200, None, 5), o("s2", -1, 400, Some(999), 6),
            o("s3", -1, 500, Some(1001), 7), o("s4", -1, 700, Some(1002), 8),
        ];
        let u = uncross(&book, 1000);
        assert_eq!((u.price, u.volume, u.surplus), (Some(1001), 1100, 100));
        assert!(u.fills.contains(&("b3", 300)) && !u.fills.iter().any(|f| f.0 == "s4"));
    }

    #[test]
    fn pressure_reference_and_priority() {
        assert_eq!(uncross(&[o("b", 1, 100, Some(990), 1), o("s", -1, 100, Some(1010), 2)], 1000).price, None);
        assert_eq!(uncross(&[o("b", 1, 500, Some(1005), 1), o("s", -1, 200, Some(1000), 2)], 1002).price, Some(1005));
        assert_eq!(uncross(&[o("b", 1, 200, Some(1005), 1), o("s", -1, 500, Some(1000), 2)], 1002).price, Some(1000));
        assert_eq!(uncross(&[o("b", 1, 300, Some(1006), 1), o("s", -1, 300, Some(1000), 2)], 1004).price, Some(1004));
        let t = uncross(&[o("early", 1, 300, Some(1000), 1), o("late", 1, 300, Some(1000), 2), o("s", -1, 400, Some(1000), 3)], 1000);
        assert_eq!(t.fills, vec![("early", 300), ("late", 100), ("s", 400)]);
    }
}
