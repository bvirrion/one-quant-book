//! firm.fpkit (Rust twin): summation, Welford, log-sum-exp and the Thomas solver, performing the same floating-point
//! operations in the same order as the Python and C++20 twins, so the results agree bit for bit. Rust never fuses a
//! multiply and an add unless asked (`f64::mul_add`). One Quant Book 4, chapter 25.

/// Vigna's SplitMix64, the stream the three twins share.
pub struct SplitMix64 {
    state: u64,
}

impl SplitMix64 {
    pub fn new(seed: u64) -> Self {
        Self { state: seed }
    }
    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    pub fn uniform(&mut self) -> f64 {
        ((self.next_u64() >> 11) as f64 + 0.5) * (1.0 / 9_007_199_254_740_992.0)
    }
}

pub fn naive_sum(x: &[f64]) -> f64 {
    let mut s = 0.0;
    for &v in x {
        s += v;
    }
    s
}

fn pairwise_rec(x: &[f64], block: usize) -> f64 {
    if x.len() <= block {
        let mut s = 0.0;
        for &v in x {
            s += v;
        }
        return s;
    }
    let mid = x.len() / 2;
    pairwise_rec(&x[..mid], block) + pairwise_rec(&x[mid..], block)
}

pub fn pairwise_sum(x: &[f64]) -> f64 {
    if x.is_empty() {
        0.0
    } else {
        pairwise_rec(x, 8)
    }
}

pub fn neumaier_sum(x: &[f64]) -> f64 {
    let (mut s, mut c) = (0.0f64, 0.0f64);
    for &v in x {
        let t = s + v;
        if s.abs() >= v.abs() {
            c += (s - t) + v;
        } else {
            c += (v - t) + s;
        }
        s = t;
    }
    s + c
}

/// (n, mean, variance with divisor n - 1)
pub fn welford(x: &[f64]) -> (usize, f64, f64) {
    let (mut n, mut mean, mut m2) = (0usize, 0.0f64, 0.0f64);
    for &v in x {
        n += 1;
        let d = v - mean;
        mean += d / n as f64;
        m2 += d * (v - mean);
    }
    (n, mean, if n > 1 { m2 / (n - 1) as f64 } else { f64::NAN })
}

pub fn logsumexp(x: &[f64]) -> f64 {
    let m = x.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    if m.is_infinite() {
        return m;
    }
    let mut s = 0.0;
    for &v in x {
        s += (v - m).exp();
    }
    m + s.ln()
}

pub fn thomas(a: &[f64], b: &[f64], c: &[f64], d: &[f64]) -> Vec<f64> {
    let n = b.len();
    let (mut cp, mut dp, mut x) = (vec![0.0; n], vec![0.0; n], vec![0.0; n]);
    cp[0] = c[0] / b[0];
    dp[0] = d[0] / b[0];
    for i in 1..n {
        let m = b[i] - a[i] * cp[i - 1];
        cp[i] = if i < n - 1 { c[i] / m } else { 0.0 };
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m;
    }
    x[n - 1] = dp[n - 1];
    for i in (0..n - 1).rev() {
        x[i] = dp[i] - cp[i] * x[i + 1];
    }
    x
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bit_identical_with_python_and_cpp() {
        let pow10 = [1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0, 10000000.0, 100000000.0];
        let mut g = SplitMix64::new(2025);
        let pnl: Vec<f64> = (0..10000).map(|i| (g.uniform() - 0.5) * pow10[i % 9]).collect();
        let mut g = SplitMix64::new(7);
        let prices: Vec<f64> = (0..10000).map(|_| 10000.0 + g.uniform()).collect();
        let mut g = SplitMix64::new(11);
        let expo: Vec<f64> = (0..1000).map(|_| 1000.0 * (g.uniform() - 0.5)).collect();
        let mut g = SplitMix64::new(13);
        let b: Vec<f64> = (0..100).map(|_| 2.5 + g.uniform()).collect();
        let d: Vec<f64> = (0..100).map(|_| g.uniform()).collect();
        let a = vec![-1.0; 100];
        let c = vec![-1.0; 100];
        assert_eq!(naive_sum(&pnl).to_bits(), 0xc1ba_1fb2_4e53_3d44);
        assert_eq!(pairwise_sum(&pnl).to_bits(), 0xc1ba_1fb2_4e53_3d64);
        assert_eq!(neumaier_sum(&pnl).to_bits(), 0xc1ba_1fb2_4e53_3d69);
        let (_, mean, var) = welford(&prices);
        assert_eq!(mean.to_bits(), 0x40c3_883f_d528_0542);
        assert_eq!(var.to_bits(), 0x3fb4_f510_2e31_2730);
        assert_eq!(logsumexp(&expo).to_bits(), 0x407f_4af5_3ba8_f1fb);
        let x = thomas(&a, &b, &c, &d);
        assert_eq!(x[0].to_bits(), 0x3fca_6da4_3e35_0286);
        assert_eq!(x[99].to_bits(), 0x3fd6_9c02_e417_2c65);
    }

    #[test]
    fn fused_multiply_add_rounds_once() {
        let (p, q, r) = (0.1f64, 10.0f64, -1.0f64);
        assert_eq!(p * q + r, 0.0);
        assert_eq!(p.mul_add(q, r), 2f64.powi(-54));
    }
}
