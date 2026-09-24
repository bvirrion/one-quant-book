//! firm.aad (Rust twin): algorithmic differentiation of the miniature firm. One Quant Book 4, ch. 28.
//! Reverse mode on a thread-local tape through operator overloading, and forward mode by dual numbers; the same
//! recording rules as firm_aad.py and the C++20 header.
use std::cell::RefCell;
use std::ops::{Add, Div, Mul, Neg, Sub};

#[derive(Clone, Copy)]
struct Node {
    a: i64,
    b: i64,
    da: f64,
    db: f64,
}

thread_local! {
    static TAPE: RefCell<Vec<Node>> = const { RefCell::new(Vec::new()) };
}

fn push(a: i64, da: f64, b: i64, db: f64) -> i64 {
    TAPE.with(|t| {
        let mut t = t.borrow_mut();
        t.push(Node { a, b, da, db });
        t.len() as i64 - 1
    })
}

/// Clear the tape before recording a new function.
pub fn clear() {
    TAPE.with(|t| t.borrow_mut().clear());
}

/// One reverse sweep from `out`; returns the adjoint of every recorded node.
pub fn reverse(out: Var) -> Vec<f64> {
    TAPE.with(|t| {
        let t = t.borrow();
        let mut adj = vec![0.0; t.len()];
        adj[out.idx as usize] = 1.0;
        for i in (0..=out.idx as usize).rev() {
            let w = adj[i];
            if w == 0.0 {
                continue;
            }
            let n = t[i];
            if n.a >= 0 {
                adj[n.a as usize] += w * n.da;
            }
            if n.b >= 0 {
                adj[n.b as usize] += w * n.db;
            }
        }
        adj
    })
}

#[derive(Clone, Copy)]
pub struct Var {
    pub idx: i64,
    pub v: f64,
}

impl Var {
    /// An input variable.
    pub fn new(x: f64) -> Self {
        Var { idx: push(-1, 0.0, -1, 0.0), v: x }
    }
    pub fn exp(self) -> Var {
        let e = self.v.exp();
        Var { idx: push(self.idx, e, -1, 0.0), v: e }
    }
    pub fn ln(self) -> Var {
        Var { idx: push(self.idx, 1.0 / self.v, -1, 0.0), v: self.v.ln() }
    }
    pub fn ncdf(self) -> Var {
        let d = (-0.5 * self.v * self.v).exp() / (2.0 * std::f64::consts::PI).sqrt();
        Var { idx: push(self.idx, d, -1, 0.0), v: ncdf(self.v) }
    }
}

/// Standard normal distribution function from the complementary error function.
pub fn ncdf(x: f64) -> f64 {
    0.5 * erfc(-x / std::f64::consts::SQRT_2)
}

/// erfc by W. J. Cody's rational approximations is not in std; this uses the continued fraction and series
/// with relative accuracy near machine precision, enough for the tests (checked against the Python values).
pub fn erfc(x: f64) -> f64 {
    if x < 0.0 {
        return 2.0 - erfc(-x);
    }
    if x < 2.0 {
        // erf series: 2/sqrt(pi) sum (-1)^n x^(2n+1) / (n! (2n+1))
        let mut term = x;
        let mut sum = x;
        let x2 = x * x;
        for n in 1..200 {
            term *= -x2 / n as f64;
            let add = term / (2 * n + 1) as f64;
            sum += add;
            if add.abs() < 1e-17 * sum.abs() {
                break;
            }
        }
        return 1.0 - 2.0 / std::f64::consts::PI.sqrt() * sum;
    }
    // continued fraction (Lentz) for x >= 2
    let tiny = 1e-300;
    let mut f = x;
    let mut c = x;
    let mut d = 0.0;
    for n in 1..300 {
        let an = n as f64 / 2.0;
        d = x + an * d;
        d = if d.abs() < tiny { tiny } else { d };
        c = x + an / c;
        c = if c.abs() < tiny { tiny } else { c };
        d = 1.0 / d;
        let delta = c * d;
        f *= delta;
        if (delta - 1.0).abs() < 1e-16 {
            break;
        }
    }
    (-x * x).exp() / (f * std::f64::consts::PI.sqrt())
}

impl Add for Var {
    type Output = Var;
    fn add(self, y: Var) -> Var {
        Var { idx: push(self.idx, 1.0, y.idx, 1.0), v: self.v + y.v }
    }
}
impl Sub for Var {
    type Output = Var;
    fn sub(self, y: Var) -> Var {
        Var { idx: push(self.idx, 1.0, y.idx, -1.0), v: self.v - y.v }
    }
}
impl Mul for Var {
    type Output = Var;
    fn mul(self, y: Var) -> Var {
        Var { idx: push(self.idx, y.v, y.idx, self.v), v: self.v * y.v }
    }
}
impl Div for Var {
    type Output = Var;
    fn div(self, y: Var) -> Var {
        Var { idx: push(self.idx, 1.0 / y.v, y.idx, -self.v / (y.v * y.v)), v: self.v / y.v }
    }
}
impl Add<f64> for Var {
    type Output = Var;
    fn add(self, c: f64) -> Var {
        Var { idx: push(self.idx, 1.0, -1, 0.0), v: self.v + c }
    }
}
impl Sub<f64> for Var {
    type Output = Var;
    fn sub(self, c: f64) -> Var {
        Var { idx: push(self.idx, 1.0, -1, 0.0), v: self.v - c }
    }
}
impl Mul<f64> for Var {
    type Output = Var;
    fn mul(self, c: f64) -> Var {
        Var { idx: push(self.idx, c, -1, 0.0), v: self.v * c }
    }
}
impl Div<f64> for Var {
    type Output = Var;
    fn div(self, c: f64) -> Var {
        Var { idx: push(self.idx, 1.0 / c, -1, 0.0), v: self.v / c }
    }
}
impl Neg for Var {
    type Output = Var;
    fn neg(self) -> Var {
        Var { idx: push(self.idx, -1.0, -1, 0.0), v: -self.v }
    }
}

/// Forward mode: a value and one tangent.
#[derive(Clone, Copy)]
pub struct Dual {
    pub v: f64,
    pub d: f64,
}

impl Dual {
    pub fn exp(self) -> Dual {
        let e = self.v.exp();
        Dual { v: e, d: e * self.d }
    }
    pub fn ln(self) -> Dual {
        Dual { v: self.v.ln(), d: self.d / self.v }
    }
    pub fn ncdf(self) -> Dual {
        let p = (-0.5 * self.v * self.v).exp() / (2.0 * std::f64::consts::PI).sqrt();
        Dual { v: ncdf(self.v), d: p * self.d }
    }
}
impl Add for Dual {
    type Output = Dual;
    fn add(self, y: Dual) -> Dual {
        Dual { v: self.v + y.v, d: self.d + y.d }
    }
}
impl Sub<f64> for Dual {
    type Output = Dual;
    fn sub(self, c: f64) -> Dual {
        Dual { v: self.v - c, d: self.d }
    }
}
impl Mul<f64> for Dual {
    type Output = Dual;
    fn mul(self, c: f64) -> Dual {
        Dual { v: self.v * c, d: self.d * c }
    }
}
impl Div for Dual {
    type Output = Dual;
    fn div(self, y: Dual) -> Dual {
        Dual { v: self.v / y.v, d: (self.d * y.v - self.v * y.d) / (y.v * y.v) }
    }
}
impl Div<f64> for Dual {
    type Output = Dual;
    fn div(self, c: f64) -> Dual {
        Dual { v: self.v / c, d: self.d / c }
    }
}
impl Neg for Dual {
    type Output = Dual;
    fn neg(self) -> Dual {
        Dual { v: -self.v, d: -self.d }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn f_var(z: &[Var]) -> Var {
        let d: Vec<Var> = z.iter().enumerate().map(|(i, zi)| (-(*zi * (0.075 * (i + 1) as f64))).exp()).collect();
        let mut tot = d[0] * 1.0;
        for i in 1..z.len() {
            let w = 1.0 + (i % 7) as f64;
            tot = tot + d[i] * w;
            tot = tot + (((d[i - 1] / d[i]).ln() - 0.002) / 0.05).ncdf() * w;
        }
        tot
    }

    fn f_plain(z: &[f64]) -> f64 {
        let d: Vec<f64> = z.iter().enumerate().map(|(i, zi)| (-(zi * (0.075 * (i + 1) as f64))).exp()).collect();
        let mut tot = d[0];
        for i in 1..z.len() {
            let w = 1.0 + (i % 7) as f64;
            tot += d[i] * w + ncdf(((d[i - 1] / d[i]).ln() - 0.002) / 0.05) * w;
        }
        tot
    }

    #[test]
    fn reverse_mode_matches_python_and_bumps() {
        let n = 400;
        let z: Vec<f64> = (0..n).map(|i| 0.03 + 0.0001 * i as f64).collect();
        clear();
        let zv: Vec<Var> = z.iter().map(|&x| Var::new(x)).collect();
        let y = f_var(&zv);
        let adj = reverse(y);
        let g = |k: usize| adj[zv[k].idx as usize];
        assert!((y.v - 1643.8656977694293).abs() < 1e-9);
        assert!((g(0) + 1.2716414715908044).abs() < 1e-9);
        assert!((g(17) + 15.944508608229377).abs() < 1e-9);
        assert!((g(399) - 233.82677751949).abs() < 1e-8);
        for k in [0usize, 17, 200, 399] {
            let mut up = z.clone();
            let mut dn = z.clone();
            up[k] += 1e-6;
            dn[k] -= 1e-6;
            let fd = (f_plain(&up) - f_plain(&dn)) / 2e-6;
            assert!((fd - g(k)).abs() < 1e-5 * (1.0 + g(k).abs()));
        }
        assert!((ncdf(1.0) - 0.8413447460685429).abs() < 1e-15 && (ncdf(-3.0) - 0.0013498980316301).abs() < 1e-16);
        for k in [3usize, 250] {
            let zd: Vec<Dual> = z.iter().enumerate().map(|(i, &x)| Dual { v: x, d: if i == k { 1.0 } else { 0.0 } }).collect();
            let d: Vec<Dual> = zd.iter().enumerate().map(|(i, zi)| (-(*zi * (0.075 * (i + 1) as f64))).exp()).collect();
            let mut tot = d[0] * 1.0;
            for i in 1..n {
                let w = 1.0 + (i % 7) as f64;
                tot = tot + d[i] * w + (((d[i - 1] / d[i]).ln() - 0.002) / 0.05).ncdf() * w;
            }
            assert!((tot.d - g(k)).abs() < 1e-9 * (1.0 + g(k).abs()));
        }
    }
}
