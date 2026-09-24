//! firm.pricing (Rust twin of the core): dates, flat curves, market-data snapshots with bumps, European and
//! American options, the analytic (Black) and finite-difference engines, and desk-unit Greeks by bump-and-reprice.
//! The same arithmetic as firm_pricing.py (AnalyticEngine, PDEEngine, fd_vanilla, greeks) for flat curves and
//! volatilities.

use std::collections::BTreeMap;

use firm_bs::{black, Right};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Date {
    pub y: i32,
    pub m: u32,
    pub d: u32,
}

/// Days since 1970-01-01 of a proleptic Gregorian date (H. Hinnant's days_from_civil).
pub fn days_from_civil(x: Date) -> i64 {
    let y = x.y as i64 - if x.m <= 2 { 1 } else { 0 };
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = y - era * 400;
    let mp = (x.m as i64 + 9) % 12;
    let doy = (153 * mp + 2) / 5 + x.d as i64 - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + doe - 719_468
}

pub fn civil_from_days(z: i64) -> Date {
    let z = z + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32;
    Date { y: (yoe + era * 400 + if m <= 2 { 1 } else { 0 }) as i32, m, d }
}

pub fn year_fraction(a: Date, b: Date) -> f64 {
    (days_from_civil(b) - days_from_civil(a)) as f64 / 365.0
}

#[derive(Clone, Copy, Debug)]
pub struct FlatCurve {
    pub rate: f64,
    pub asof: Date,
}

impl FlatCurve {
    pub fn df(&self, d: Date) -> f64 {
        (-self.rate * year_fraction(self.asof, d)).exp()
    }
}

#[derive(Clone, Copy, Debug, Default)]
pub struct Dividends {
    pub div_yield: f64,
    pub borrow: f64,
}

#[derive(Clone, Debug)]
pub struct Bump {
    pub factor: String,
    pub size: f64,
    pub relative: bool,
}

impl Bump {
    pub fn new(factor: &str, size: f64, relative: bool) -> Self {
        Bump { factor: factor.to_string(), size, relative }
    }
}

#[derive(Clone, Debug)]
pub struct MarketData {
    pub asof: Date,
    pub spots: BTreeMap<String, f64>,
    pub curves: BTreeMap<String, FlatCurve>,
    pub dividends: BTreeMap<String, Dividends>,
    pub vols: BTreeMap<String, f64>,
    pub funding: BTreeMap<String, String>,
}

impl MarketData {
    pub fn t(&self, d: Date) -> f64 {
        year_fraction(self.asof, d)
    }
    pub fn df(&self, curve: &str, d: Date) -> f64 {
        let c = &self.curves[curve];
        c.df(d) / c.df(self.asof)
    }
    pub fn funding_curve(&self, und: &str) -> String {
        if let Some(c) = self.funding.get(und) {
            return c.clone();
        }
        assert!(self.curves.len() == 1, "no funding curve for {und}");
        self.curves.keys().next().unwrap().clone()
    }
    pub fn forward(&self, und: &str, d: Date) -> f64 {
        let c = self.funding_curve(und);
        let div = self.dividends.get(und).copied().unwrap_or_default();
        self.spots[und] * (-(div.borrow + div.div_yield) * self.t(d)).exp() / self.df(&c, d)
    }
    pub fn rolled(&self, new_asof: Date) -> MarketData {
        let mut out = self.clone();
        out.asof = new_asof;
        out
    }
    pub fn apply(&self, b: &Bump) -> MarketData {
        let (kind, name) = match b.factor.split_once(':') {
            Some((k, n)) => (k, n.to_string()),
            None => (b.factor.as_str(), String::new()),
        };
        let mut out = self.clone();
        match kind {
            "SPOT" => {
                let x = self.spots[&name];
                out.spots.insert(name, if b.relative { x * (1.0 + b.size) } else { x + b.size });
            }
            "VOL" => {
                out.vols.insert(name.clone(), self.vols[&name] + b.size);
            }
            "CURVE" => out.curves.get_mut(&name).unwrap().rate += b.size,
            "DIV" => out.dividends.entry(name).or_default().div_yield += b.size,
            "BORROW" => out.dividends.entry(name).or_default().borrow += b.size,
            "TIME" => out = self.rolled(civil_from_days(days_from_civil(self.asof) + b.size.round() as i64)),
            _ => panic!("unknown risk factor {}", b.factor),
        }
        out
    }
}

#[derive(Clone, Debug)]
pub struct EuropeanOption {
    pub id: String,
    pub underlying: String,
    pub currency: String,
    pub notional: f64,
    pub discount_curve: String,
    pub strike: f64,
    pub expiry: Date,
    pub call: bool,
    pub american: bool,
}

impl EuropeanOption {
    pub fn curve(&self, md: &MarketData) -> String {
        if !self.discount_curve.is_empty() {
            return self.discount_curve.clone();
        }
        if md.curves.contains_key(&self.currency) {
            return self.currency.clone();
        }
        assert!(md.curves.len() == 1, "{}: no discount curve", self.id);
        md.curves.keys().next().unwrap().clone()
    }
    fn intrinsic(&self, s: f64) -> f64 {
        if self.call { (s - self.strike).max(0.0) } else { (self.strike - s).max(0.0) }
    }
}

pub trait Engine {
    fn price(&self, o: &EuropeanOption, md: &MarketData) -> f64;
}

pub struct AnalyticEngine;

impl Engine for AnalyticEngine {
    fn price(&self, o: &EuropeanOption, md: &MarketData) -> f64 {
        assert!(!o.american, "the analytic engine prices European exercise only");
        let t = md.t(o.expiry);
        if t < 0.0 {
            return 0.0;
        }
        let right = if o.call { Right::Call } else { Right::Put };
        o.notional
            * black(md.forward(&o.underlying, o.expiry), o.strike, t, md.df(&o.curve(md), o.expiry), md.vols[&o.underlying], right)
    }
}

fn thomas(a: &[f64], b: &[f64], c: &[f64], d: &[f64]) -> Vec<f64> {
    let n = d.len();
    let mut cp = vec![0.0; n];
    let mut dp = vec![0.0; n];
    cp[0] = c[0] / b[0];
    dp[0] = d[0] / b[0];
    for i in 1..n {
        let m = b[i] - a[i] * cp[i - 1];
        cp[i] = c[i] / m;
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m;
    }
    let mut out = vec![0.0; n];
    out[n - 1] = dp[n - 1];
    for i in (0..n - 1).rev() {
        out[i] = dp[i] - cp[i] * out[i + 1];
    }
    out
}

/// Brennan-Schwartz with V >= g: exercise region at low spots (put); the call is the mirror image.
fn projected(a: &[f64], b: &[f64], c: &[f64], d: &[f64], g: &[f64], put: bool) -> Vec<f64> {
    if !put {
        let rev = |x: &[f64]| x.iter().rev().copied().collect::<Vec<f64>>();
        let mut out = projected(&rev(c), &rev(b), &rev(a), &rev(d), &rev(g), true);
        out.reverse();
        return out;
    }
    let n = d.len();
    let mut bp = vec![0.0; n];
    let mut dp = vec![0.0; n];
    bp[n - 1] = b[n - 1];
    dp[n - 1] = d[n - 1];
    for k in (0..n - 1).rev() {
        let f = c[k] / bp[k + 1];
        bp[k] = b[k] - f * a[k + 1];
        dp[k] = d[k] - f * dp[k + 1];
    }
    let mut out = vec![0.0; n];
    out[0] = (dp[0] / bp[0]).max(g[0]);
    for i in 1..n {
        out[i] = ((dp[i] - a[i] * out[i - 1]) / bp[i]).max(g[i]);
    }
    out
}

/// Crank-Nicolson in log-spot on a uniform grid of m + 1 nodes, Rannacher start-up, Thomas or Brennan-Schwartz.
#[allow(clippy::too_many_arguments)]
pub fn fd_vanilla(s0: f64, k: f64, t: f64, r: f64, q: f64, vol: f64, call: bool, american: bool, m: usize, n_t: usize) -> f64 {
    let rannacher = 2;
    let half = 5.0 * vol * t.sqrt();
    let sign = if call { 1.0 } else { -1.0 };
    let x: Vec<f64> = (0..=m).map(|i| s0.ln() - half + 2.0 * half * i as f64 / m as f64).collect();
    let s: Vec<f64> = x.iter().map(|xi| xi.exp()).collect();
    let g: Vec<f64> = s.iter().map(|si| (sign * (si - k)).max(0.0)).collect();
    let mut v = g.clone();
    let (nu, d2) = (r - q - 0.5 * vol * vol, vol * vol);
    let ni = m - 1;
    let (mut lo, mut di, mut up) = (vec![0.0; ni], vec![0.0; ni], vec![0.0; ni]);
    for i in 1..m {
        let (hm, hp) = (x[i] - x[i - 1], x[i + 1] - x[i]);
        lo[i - 1] = d2 / (hm * (hm + hp)) - nu * hp / (hm * (hm + hp));
        di[i - 1] = -d2 / (hm * hp) + nu * (hp - hm) / (hm * hp) - r;
        up[i - 1] = d2 / (hp * (hm + hp)) + nu * hm / (hp * (hm + hp));
    }
    let dt = t / n_t as f64;
    let (mut tau, mut step, mut implicit_half) = (0.0_f64, 0_usize, 2 * rannacher);
    let gi = &g[1..m];
    while step < n_t {
        let (h, theta) = if implicit_half > 0 {
            implicit_half -= 1;
            (0.5 * dt, 1.0)
        } else {
            (dt, 0.5)
        };
        tau += h;
        let mut a = vec![0.0; ni];
        let mut b = vec![0.0; ni];
        let mut c = vec![0.0; ni];
        let mut rhs = vec![0.0; ni];
        for i in 0..ni {
            rhs[i] = v[i + 1] + (1.0 - theta) * h * (lo[i] * v[i] + di[i] * v[i + 1] + up[i] * v[i + 2]);
            a[i] = -theta * h * lo[i];
            b[i] = 1.0 - theta * h * di[i];
            c[i] = -theta * h * up[i];
        }
        let end = |sj: f64| (sign * (sj * (-q * tau).exp() - k * (-r * tau).exp())).max(0.0);
        let (mut e0, mut e1) = (end(s[0]), end(s[m]));
        if american {
            e0 = e0.max(g[0]);
            e1 = e1.max(g[m]);
        }
        rhs[0] -= a[0] * e0;
        rhs[ni - 1] -= c[ni - 1] * e1;
        a[0] = 0.0;
        c[ni - 1] = 0.0;
        let inner = if american { projected(&a, &b, &c, &rhs, gi, !call) } else { thomas(&a, &b, &c, &rhs) };
        v[0] = e0;
        v[m] = e1;
        v[1..m].copy_from_slice(&inner);
        if (tau - (step + 1) as f64 * dt).abs() < 1e-12 * t.max(1.0) {
            step += 1;
        }
    }
    let x0 = s0.ln();
    let i = x.iter().position(|xj| *xj >= x0).unwrap_or(m).clamp(1, m - 1);
    let (x1, x2, x3) = (x[i - 1], x[i], x[i + 1]);
    v[i - 1] * (x0 - x2) * (x0 - x3) / ((x1 - x2) * (x1 - x3))
        + v[i] * (x0 - x1) * (x0 - x3) / ((x2 - x1) * (x2 - x3))
        + v[i + 1] * (x0 - x1) * (x0 - x2) / ((x3 - x1) * (x3 - x2))
}

pub struct PdeEngine {
    pub m: usize,
    pub n_t: usize,
}

impl Engine for PdeEngine {
    fn price(&self, o: &EuropeanOption, md: &MarketData) -> f64 {
        let t = md.t(o.expiry);
        let s = md.spots[&o.underlying];
        if t <= 0.0 {
            return if t == 0.0 { o.notional * o.intrinsic(s) } else { 0.0 };
        }
        let fc = md.funding_curve(&o.underlying);
        let r = -md.df(&fc, o.expiry).ln() / t;
        let q = r - (md.forward(&o.underlying, o.expiry) / s).ln() / t;
        let v = fd_vanilla(s, o.strike, t, r, q, md.vols[&o.underlying], o.call, o.american, self.m, self.n_t);
        o.notional * v * md.df(&o.curve(md), o.expiry) / md.df(&fc, o.expiry)
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
}

/// Desk units as firm_pricing.greeks: delta per unit of spot, gamma per 1 % (Gamma S^2 / 100), vega per volatility
/// point, theta per day, rho per basis point on every curve.
pub fn greeks(o: &EuropeanOption, md: &MarketData, e: &dyn Engine) -> Greeks {
    let h = 0.01;
    let s = md.spots[&o.underlying];
    let base = e.price(o, md);
    let spot = format!("SPOT:{}", o.underlying);
    let vol = format!("VOL:{}", o.underlying);
    let up = e.price(o, &md.apply(&Bump::new(&spot, h, true)));
    let dn = e.price(o, &md.apply(&Bump::new(&spot, -h, true)));
    let (mut cu, mut cd) = (md.clone(), md.clone());
    for c in cu.curves.values_mut() {
        c.rate += 1e-4;
    }
    for c in cd.curves.values_mut() {
        c.rate -= 1e-4;
    }
    Greeks {
        delta: (up - dn) / (2.0 * h * s),
        gamma: (up - 2.0 * base + dn) / ((h * s) * (h * s)) * s * s / 100.0,
        vega: (e.price(o, &md.apply(&Bump::new(&vol, 0.01, false))) - e.price(o, &md.apply(&Bump::new(&vol, -0.01, false)))) / 2.0,
        theta: e.price(o, &md.rolled(civil_from_days(days_from_civil(md.asof) + 1))) - base,
        rho: (e.price(o, &cu) - e.price(o, &cd)) / 2.0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn market() -> MarketData {
        let t0 = Date { y: 2026, m: 9, d: 24 };
        MarketData {
            asof: t0,
            spots: BTreeMap::from([("ABC".to_string(), 100.0)]),
            curves: BTreeMap::from([("USD".to_string(), FlatCurve { rate: 0.05, asof: t0 })]),
            dividends: BTreeMap::from([("ABC".to_string(), Dividends { div_yield: 0.02, borrow: 0.005 })]),
            vols: BTreeMap::from([("ABC".to_string(), 0.2)]),
            funding: BTreeMap::new(),
        }
    }

    fn option(strike: f64, call: bool, american: bool) -> EuropeanOption {
        EuropeanOption {
            id: "o".into(),
            underlying: "ABC".into(),
            currency: "USD".into(),
            notional: 1.0,
            discount_curve: String::new(),
            strike,
            expiry: Date { y: 2027, m: 9, d: 24 },
            call,
            american,
        }
    }

    fn near(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    #[test]
    fn dates_and_forward() {
        assert_eq!(days_from_civil(Date { y: 1970, m: 1, d: 1 }), 0);
        assert_eq!(civil_from_days(days_from_civil(Date { y: 2028, m: 2, d: 29 })), Date { y: 2028, m: 2, d: 29 });
        assert!(near(market().forward("ABC", Date { y: 2027, m: 9, d: 24 }), 102.53151205244288, 1e-12));
    }

    #[test]
    fn engines_match_the_python_library() {
        let md = market();
        let pde = PdeEngine { m: 200, n_t: 200 };
        assert!(near(AnalyticEngine.price(&option(100.0, true, false), &md), 8.93667801992408, 1e-9));
        assert!(near(AnalyticEngine.price(&option(95.0, false, false), &md), 4.437332869541783, 1e-9));
        assert!(near(pde.price(&option(100.0, true, false), &md), 8.934340456890846, 1e-9));
        assert!(near(pde.price(&option(95.0, false, false), &md), 4.436150972443718, 1e-9));
        assert!(near(pde.price(&option(110.0, false, true), &md), 12.78912756690443, 1e-9));
        assert!(near(pde.price(&option(90.0, true, true), &md), 14.743700892073113, 1e-9));
        assert!(near(fd_vanilla(100.0, 100.0, 1.0, 0.05, 0.0, 0.2, false, true, 200, 200), 6.0873536606097804, 1e-9));
    }

    #[test]
    fn greeks_match_the_python_library() {
        let md = market();
        let g = greeks(&option(110.0, false, true), &md, &PdeEngine { m: 200, n_t: 200 });
        assert!(near(g.delta, -0.6386648197036005, 1e-9) && near(g.gamma, 2.2805489998388495, 1e-8));
        assert!(near(g.vega, 0.353233112561127, 1e-9) && near(g.theta, -0.006380588425209055, 1e-9));
        assert!(near(g.rho, -0.004244035535873714, 1e-9));
        let a = greeks(&option(100.0, true, false), &md, &AnalyticEngine);
        assert!(near(a.delta, 0.5744004983176145, 1e-9) && near(a.vega, 0.3793580615602945, 1e-9));
        assert!(near(a.theta, -0.013112603398962364, 1e-9) && near(a.rho, 0.004851008590838646, 1e-9));
        let up = md.apply(&Bump::new("SPOT:ABC", 0.01, true));
        assert!(md.spots["ABC"] == 100.0 && near(up.spots["ABC"], 101.0, 1e-12));
    }
}
