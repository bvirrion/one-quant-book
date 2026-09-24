//! firm.bs -- Black-Scholes and Black kernels (build of Chapter 3, One Quant Book 5), Rust twin of
//! firm_bs.py: price on the forward, analytic Greeks, implied volatility by Newton's method
//! safeguarded by bisection. No dependencies: the complementary error function is computed by a
//! series and a continued fraction.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Right {
    Call,
    Put,
}

fn sign(r: Right) -> f64 {
    match r {
        Right::Call => 1.0,
        Right::Put => -1.0,
    }
}

/// Complementary error function without tabulated constants: the positive-term series
/// erf(x) = 2/sqrt(pi) exp(-x^2) sum_n 2^n x^(2n+1) / (1*3*...*(2n+1)) for |x| < 2.5, and the
/// continued fraction erfc(x) = exp(-x^2)/sqrt(pi) / (x + (1/2)/(x + 1/(x + (3/2)/(x + ...))))
/// (modified Lentz) beyond. Relative error about 1e-15.
pub fn erfc(x: f64) -> f64 {
    let ax = x.abs();
    let r = if ax < 2.5 {
        let (mut term, mut sum, mut n) = (ax, ax, 0.0_f64);
        while term > 1e-17 * sum {
            n += 1.0;
            term *= 2.0 * ax * ax / (2.0 * n + 1.0);
            sum += term;
        }
        1.0 - 2.0 / std::f64::consts::PI.sqrt() * (-ax * ax).exp() * sum
    } else {
        let tiny = 1e-300;
        let (mut f, mut c, mut d) = (ax, ax, 0.0_f64);
        for k in 1..300 {
            let a = 0.5 * k as f64;
            d = ax + a * d;
            d = if d.abs() < tiny { tiny } else { d };
            c = ax + a / c;
            c = if c.abs() < tiny { tiny } else { c };
            d = 1.0 / d;
            let delta = c * d;
            f *= delta;
            if (delta - 1.0).abs() < 1e-16 {
                break;
            }
        }
        (-ax * ax).exp() / std::f64::consts::PI.sqrt() / f
    };
    if x < 0.0 {
        2.0 - r
    } else {
        r
    }
}

pub fn ncdf(x: f64) -> f64 {
    0.5 * erfc(-x / std::f64::consts::SQRT_2)
}

pub fn npdf(x: f64) -> f64 {
    (-0.5 * x * x).exp() / (2.0 * std::f64::consts::PI).sqrt()
}

pub fn black(fwd: f64, strike: f64, t: f64, df: f64, vol: f64, right: Right) -> f64 {
    let s_ = sign(right);
    if t <= 0.0 || vol <= 0.0 {
        return df * (s_ * (fwd - strike)).max(0.0);
    }
    let s = vol * t.sqrt();
    let d1 = (fwd / strike).ln() / s + 0.5 * s;
    df * s_ * (fwd * ncdf(s_ * d1) - strike * ncdf(s_ * (d1 - s)))
}

pub fn bs(spot: f64, strike: f64, t: f64, r: f64, q: f64, vol: f64, right: Right) -> f64 {
    black(
        spot * ((r - q) * t).exp(),
        strike,
        t,
        (-r * t).exp(),
        vol,
        right,
    )
}

#[derive(Clone, Copy, Debug)]
pub struct Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
    pub vanna: f64,
    pub volga: f64,
}

pub fn greeks(spot: f64, strike: f64, t: f64, r: f64, q: f64, vol: f64, right: Right) -> Greeks {
    let sg = sign(right);
    let sq = t.sqrt();
    let s = vol * sq;
    let d1 = ((spot / strike).ln() + (r - q) * t) / s + 0.5 * s;
    let d2 = d1 - s;
    let (eq, er, pdf) = ((-q * t).exp(), (-r * t).exp(), npdf(d1));
    let vega = spot * eq * pdf * sq;
    Greeks {
        delta: sg * eq * ncdf(sg * d1),
        gamma: eq * pdf / (spot * s),
        vega,
        theta: -spot * eq * pdf * vol / (2.0 * sq) - sg * r * strike * er * ncdf(sg * d2)
            + sg * q * spot * eq * ncdf(sg * d1),
        rho: sg * strike * t * er * ncdf(sg * d2),
        vanna: -eq * pdf * d2 / vol,
        volga: vega * d1 * d2 / vol,
    }
}

pub fn implied_vol(
    price: f64,
    fwd: f64,
    strike: f64,
    t: f64,
    df: f64,
    right: Right,
) -> Result<f64, String> {
    let sg = sign(right);
    let lo_p = df * (sg * (fwd - strike)).max(0.0);
    let hi_p = df * if right == Right::Call { fwd } else { strike };
    if !(lo_p <= price && price < hi_p) {
        return Err(format!("price {price} outside ({lo_p}, {hi_p})"));
    }
    if price - lo_p < 1e-15 * df * fwd.max(strike) {
        return Ok(0.0);
    }
    let x = (fwd / strike).ln();
    let c = price / df - 0.5 * sg * (fwd - strike);
    let disc = (c * c - (fwd - strike).powi(2) / std::f64::consts::PI).max(0.0);
    let guess = (2.0 * std::f64::consts::PI).sqrt() / (fwd + strike) * (c + disc.sqrt()) / t.sqrt();
    let (mut lo, mut hi) = (0.0_f64, 1.0_f64);
    while black(fwd, strike, t, df, hi, right) < price {
        hi *= 2.0;
        if hi > 100.0 {
            return Err("no volatility below 10000%".into());
        }
    }
    let mut v = if guess > 0.0 && x.abs() < 1.0 {
        guess.max(1e-4).min(hi)
    } else {
        0.5 * hi
    };
    for _ in 0..100 {
        let f = black(fwd, strike, t, df, v, right) - price;
        if f.abs() < 1e-12 * price.max(1e-300) || hi - lo < 1e-15 {
            return Ok(v);
        }
        if f > 0.0 {
            hi = v;
        } else {
            lo = v;
        }
        let s = v * t.sqrt();
        let vega = df * fwd * npdf(x / s + 0.5 * s) * t.sqrt();
        let step = if vega > 0.0 { v - f / vega } else { -1.0 };
        v = if lo < step && step < hi {
            step
        } else {
            0.5 * (lo + hi)
        };
    }
    Ok(v)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn near(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    #[test]
    fn textbook_value_and_parity() {
        assert!(near(
            bs(100.0, 100.0, 1.0, 0.05, 0.0, 0.2, Right::Call),
            10.450_583_572_185_58,
            1e-11
        ));
        let c = bs(100.0, 110.0, 0.5, 0.03, 0.01, 0.25, Right::Call);
        let p = bs(100.0, 110.0, 0.5, 0.03, 0.01, 0.25, Right::Put);
        assert!(near(
            c - p,
            100.0 * (-0.005_f64).exp() - 110.0 * (-0.015_f64).exp(),
            1e-12
        ));
    }

    #[test]
    fn erfc_values() {
        assert!(near(erfc(0.0), 1.0, 1e-15));
        // reference values: Python's math.erfc
        for (x, v) in [
            (1.0, 0.157_299_207_050_285_13),
            (-2.0, 1.995_322_265_018_952_7),
            (2.4, 6.885_138_966_450_786e-4),
            (2.6, 2.360_344_165_293_492e-4),
            (0.3, 0.671_373_240_540_872_6),
        ] {
            assert!((erfc(x) / v - 1.0).abs() < 1e-13, "erfc({x})");
        }
        assert!((erfc(6.0) / 2.151_973_671_249_891_3e-17 - 1.0).abs() < 1e-12);
    }

    #[test]
    fn greeks_match_differences() {
        let h = 1e-4;
        let g = greeks(100.0, 110.0, 0.5, 0.03, 0.01, 0.25, Right::Put);
        let p = |s: f64, v: f64| bs(s, 110.0, 0.5, 0.03, 0.01, v, Right::Put);
        assert!(near(
            g.delta,
            (p(100.0 + h, 0.25) - p(100.0 - h, 0.25)) / (2.0 * h),
            1e-7
        ));
        assert!(near(
            g.vega,
            (p(100.0, 0.25 + h) - p(100.0, 0.25 - h)) / (2.0 * h),
            1e-6
        ));
    }

    #[test]
    fn implied_vol_round_trips() {
        for k in [40.0, 80.0, 100.0, 125.0, 300.0] {
            for t in [0.01, 0.25, 1.0, 10.0] {
                for v in [0.05, 0.2, 0.8] {
                    for r in [Right::Call, Right::Put] {
                        let p = black(100.0, k, t, 0.97, v, r);
                        if p < 1e-8 {
                            continue;
                        }
                        let iv = implied_vol(p, 100.0, k, t, 0.97, r).unwrap();
                        assert!(near(black(100.0, k, t, 0.97, iv, r), p, 1e-10 * p.max(1.0)));
                    }
                }
            }
        }
        assert!(implied_vol(0.5, 100.0, 80.0, 1.0, 1.0, Right::Call).is_err());
    }
}
