//! firm.hawkes (Rust twin): exponential-kernel Hawkes process. One Quant Book 4, chapter 7.
//! Thinning simulation, O(n) log-likelihood and compensator; same results as the Python and C++20
//! twins on the same event list.

/// Parameters of lambda_t = mu + sum alpha exp(-beta (t - t_i)).
#[derive(Clone, Copy)]
pub struct Params {
    pub mu: f64,
    pub alpha: f64,
    pub beta: f64,
}

impl Params {
    pub fn branching(&self) -> f64 {
        self.alpha / self.beta
    }
    pub fn mean_intensity(&self) -> f64 {
        self.mu / (1.0 - self.branching())
    }
}

/// SplitMix64 uniforms on (0, 1).
pub struct Rng(u64);

impl Rng {
    pub fn new(seed: u64) -> Self {
        Rng(seed)
    }
    pub fn uniform(&mut self) -> f64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^= z >> 31;
        ((z >> 11) as f64 + 0.5) * (1.0 / (1u64 << 53) as f64)
    }
    pub fn exponential(&mut self, rate: f64) -> f64 {
        -self.uniform().ln() / rate
    }
}

/// Ogata's thinning.
pub fn simulate_thinning(p: &Params, t_end: f64, rng: &mut Rng) -> Vec<f64> {
    let mut out = Vec::new();
    let (mut t, mut excite) = (0.0, 0.0);
    loop {
        let bound = p.mu + excite;
        let w = rng.exponential(bound);
        t += w;
        if t > t_end {
            break;
        }
        excite *= (-p.beta * w).exp();
        if rng.uniform() * bound <= p.mu + excite {
            out.push(t);
            excite += p.alpha;
        }
    }
    out
}

/// sum log lambda(t_i) - int_0^T lambda dt, O(n).
pub fn loglik(p: &Params, times: &[f64], t_end: f64) -> f64 {
    let (mut total, mut a, mut integral) = (0.0, 0.0, p.mu * t_end);
    for i in 0..times.len() {
        if i > 0 {
            a = (-p.beta * (times[i] - times[i - 1])).exp() * (1.0 + a);
        }
        total += (p.mu + p.alpha * a).ln();
        integral += p.alpha / p.beta * (1.0 - (-p.beta * (t_end - times[i])).exp());
    }
    total - integral
}

/// Lambda(t_i).
pub fn compensator(p: &Params, times: &[f64]) -> Vec<f64> {
    let mut out = vec![0.0; times.len()];
    let mut a = 0.0;
    for i in 0..times.len() {
        if i > 0 {
            a = (-p.beta * (times[i] - times[i - 1])).exp() * (1.0 + a);
        }
        out[i] = p.mu * times[i] + p.alpha / p.beta * (i as f64 - a);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: Params = Params { mu: 0.1, alpha: 0.7, beta: 1.0 };

    #[test]
    fn matches_python_reference() {
        let t = [0.5, 1.2, 1.3, 4.0, 4.1, 4.15, 9.0];
        assert!((loglik(&P, &t, 10.0) - (-12.207_123_982_546_31)).abs() < 1e-12);
        let c = compensator(&P, &t);
        assert!((c[1] - 0.472_390_287_346_013_3).abs() < 1e-13 && (c[6] - 5.083_844_743_294_921).abs() < 1e-13);
    }

    #[test]
    fn long_simulation() {
        let mut rng = Rng::new(7);
        let t_end = 200_000.0;
        let t = simulate_thinning(&P, t_end, &mut rng);
        let expected = P.mean_intensity() * t_end;
        assert!((t.len() as f64 / expected - 1.0).abs() < 0.05);
        let c = compensator(&P, &t);
        assert!((c[c.len() - 1] / t.len() as f64 - 1.0).abs() < 0.02);
        let poisson = Params { mu: P.mean_intensity(), alpha: 0.0, beta: 1.0 };
        assert!(loglik(&P, &t, t_end) > loglik(&poisson, &t, t_end));
    }
}
