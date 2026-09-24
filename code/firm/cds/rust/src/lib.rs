//! firm.cds -- credit default swaps with a flat hazard rate, and the settlement auction (build of
//! Chapter 23, One Quant Book 2), Rust twin of firm_cds.py. Quarterly premiums, half a period of
//! accrued premium on default, default paid at the period's end; auction prices per 100 of par.

#[derive(Clone, Copy, Debug)]
pub struct Cds {
    pub maturity: f64,
    pub coupon: f64,
    pub recovery: f64,
    pub freq: u32,
}

impl Cds {
    pub fn new(maturity: f64, coupon: f64) -> Cds {
        Cds { maturity, coupon, recovery: 0.40, freq: 4 }
    }
}

/// (risky annuity, protection leg value), per unit notional.
pub fn legs(c: &Cds, lam: f64, r: f64) -> (f64, f64) {
    let dt = 1.0 / c.freq as f64;
    let n = (c.maturity * c.freq as f64).round() as u32;
    let (mut annuity, mut protection) = (0.0, 0.0);
    for k in 1..=n {
        let (q0, q1) = ((-lam * (k - 1) as f64 * dt).exp(), (-lam * k as f64 * dt).exp());
        let df = (-r * k as f64 * dt).exp();
        annuity += dt * df * (q1 + 0.5 * (q0 - q1));
        protection += (1.0 - c.recovery) * df * (q0 - q1);
    }
    (annuity, protection)
}

pub fn par_spread(c: &Cds, lam: f64, r: f64) -> f64 {
    let (a, p) = legs(c, lam, r);
    p / a
}

pub fn upfront(c: &Cds, lam: f64, r: f64) -> f64 {
    let (a, p) = legs(c, lam, r);
    p - c.coupon * a
}

pub fn hazard_from_spread(c: &Cds, spread: f64, r: f64) -> f64 {
    let (mut lo, mut hi) = (1e-9, 5.0);
    for _ in 0..200 {
        let mid = 0.5 * (lo + hi);
        if par_spread(c, mid, r) < spread { lo = mid } else { hi = mid }
    }
    0.5 * (lo + hi)
}

pub fn inside_market_midpoint(bids: &[f64], offers: &[f64]) -> f64 {
    let mut b = bids.to_vec();
    let mut o = offers.to_vec();
    b.sort_by(|x, y| y.total_cmp(x));
    o.sort_by(|x, y| x.total_cmp(y));
    let mut i = 0;
    while i < b.len() && i < o.len() && b[i] >= o[i] {
        i += 1;
    }
    let h = (b.len() - i).div_ceil(2);
    let sum: f64 = (0..h).map(|k| b[i + k] + o[i + k]).sum();
    (sum / (2.0 * h as f64) * 8.0).round() / 8.0
}

/// Second stage: `orders` are (price, size); `oi` > 0 is an open interest to sell bonds.
pub fn final_price(imm: f64, oi: f64, orders: &[(f64, f64)]) -> f64 {
    if oi == 0.0 {
        return imm;
    }
    let mut o = orders.to_vec();
    let (mut filled, mut price) = (0.0, imm);
    if oi > 0.0 {
        o.sort_by(|x, y| y.0.total_cmp(&x.0));
        for (p, s) in o {
            filled += s;
            price = p;
            if filled >= oi {
                break;
            }
        }
        return price.min(imm + 1.0);
    }
    o.sort_by(|x, y| x.0.total_cmp(&y.0));
    for (p, s) in o {
        filled += s;
        price = p;
        if filled >= -oi {
            break;
        }
    }
    price.max(imm - 1.0)
}

pub fn cash_settlement(notional: f64, price: f64) -> f64 {
    notional * (100.0 - price) / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn par_round_trip() {
        let ig = Cds::new(5.0, 0.01);
        let lam = hazard_from_spread(&ig, 0.01, 0.04);
        assert!((lam - 0.0166666908).abs() < 1e-9);
        assert!((par_spread(&ig, lam, 0.04) - 0.01).abs() < 1e-12);
        assert!((upfront(&ig, hazard_from_spread(&ig, 0.02, 0.04), 0.04) - 0.0416490885).abs() < 1e-9);
    }

    #[test]
    fn lehman_auction() {
        let bids = [8.0, 8.0, 8.0, 8.0, 8.25, 8.75, 8.875, 9.0, 9.0, 9.25, 9.25, 9.5, 9.5, 10.0];
        let offers = [10.0, 10.0, 10.0, 10.0, 10.25, 10.75, 10.875, 11.0, 11.0, 11.0, 11.25, 11.5, 11.5, 12.0];
        assert_eq!(inside_market_midpoint(&bids, &offers), 9.75);
        let orders = [(11.0, 100.0), (10.0, 400.0), (9.0, 1500.0), (8.625, 3000.0), (7.0, 5000.0)];
        assert_eq!(final_price(9.75, 4920.0, &orders), 8.625);
        assert_eq!(final_price(9.75, 4920.0, &[(12.0, 6000.0)]), 10.75);
        assert_eq!(cash_settlement(10e6, 8.625), 9_137_500.0);
    }
}
