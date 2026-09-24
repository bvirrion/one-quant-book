//! firm.fdpricer (Rust twin): American put by Crank-Nicolson in log-spot on a uniform grid, Rannacher
//! start-up and the Brennan-Schwartz algorithm; the same arithmetic as firm_fdpricer.py (grid="uniform",
//! smoothing=False).

/// Uniform log-spot grid of m + 1 nodes, `width` standard deviations either side of ln s0.
pub fn uniform_grid(s0: f64, vol: f64, t: f64, m: usize, width: f64) -> Vec<f64> {
    let half = width * vol * t.sqrt();
    (0..=m).map(|i| s0.ln() - half + (2.0 * half) * i as f64 / m as f64).collect()
}

/// Tridiagonal solve with V >= g: eliminate from the top, project on the way up.
pub fn brennan_schwartz(a: &[f64], b: &[f64], c: &[f64], d: &[f64], g: &[f64]) -> Vec<f64> {
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

/// American put value at s0.
#[allow(clippy::too_many_arguments)]
pub fn american_put(s0: f64, k: f64, t: f64, r: f64, q: f64, vol: f64, m: usize, n_t: usize, rannacher: i32) -> f64 {
    let x = uniform_grid(s0, vol, t, m, 5.0);
    let n = x.len();
    let s: Vec<f64> = x.iter().map(|xi| xi.exp()).collect();
    let g: Vec<f64> = s.iter().map(|si| (k - si).max(0.0)).collect();
    let mut v = g.clone();
    let nu = r - q - 0.5 * vol * vol;
    let d2 = vol * vol;
    let (mut lo, mut di, mut up) = (Vec::new(), Vec::new(), Vec::new());
    for i in 1..n - 1 {
        let (hm, hp) = (x[i] - x[i - 1], x[i + 1] - x[i]);
        lo.push(d2 / (hm * (hm + hp)) - nu * hp / (hm * (hm + hp)));
        di.push(-d2 / (hm * hp) + nu * (hp - hm) / (hm * hp) - r);
        up.push(d2 / (hp * (hm + hp)) + nu * hm / (hp * (hm + hp)));
    }
    let dt = t / n_t as f64;
    let (mut tau, mut step, mut implicit_half) = (0.0_f64, 0_usize, 2 * rannacher);
    let ni = n - 2;
    let gi = &g[1..n - 1];
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
        let (vl, vu) = (k - s[0], 0.0);
        rhs[0] -= a[0] * vl;
        rhs[ni - 1] -= c[ni - 1] * vu;
        a[0] = 0.0;
        c[ni - 1] = 0.0;
        let inner = brennan_schwartz(&a, &b, &c, &rhs, gi);
        v[0] = vl;
        v[n - 1] = vu;
        v[1..(ni + 1)].copy_from_slice(&inner);
        for i in 0..n {
            v[i] = v[i].max(g[i]);
        }
        if (tau - (step + 1) as f64 * dt).abs() < 1e-12 * t.max(1.0) {
            step += 1;
        }
    }
    let x0 = s0.ln();
    let i = x.partition_point(|xi| *xi < x0).clamp(1, n - 2);
    let (x1, x2, x3) = (x[i - 1], x[i], x[i + 1]);
    v[i - 1] * (x0 - x2) * (x0 - x3) / ((x1 - x2) * (x1 - x3))
        + v[i] * (x0 - x1) * (x0 - x3) / ((x2 - x1) * (x2 - x3))
        + v[i + 1] * (x0 - x1) * (x0 - x2) / ((x3 - x1) * (x3 - x2))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn matches_the_python_engine() {
        assert!((american_put(100.0, 100.0, 1.0, 0.05, 0.0, 0.2, 200, 200, 2) - 6.08735366060978).abs() < 1e-9);
        assert!((american_put(90.0, 100.0, 0.5, 0.03, 0.01, 0.3, 160, 100, 2) - 13.389843531304049).abs() < 1e-9);
        assert!((american_put(100.0, 100.0, 1.0, 0.05, 0.0, 0.2, 200, 200, 0) - 6.087606072487043).abs() < 1e-9);
    }

    #[test]
    fn converges_as_the_grid_is_refined() {
        let reference = 6.0903534672;
        let coarse = american_put(100.0, 100.0, 1.0, 0.05, 0.0, 0.2, 100, 100, 2);
        let fine = american_put(100.0, 100.0, 1.0, 0.05, 0.0, 0.2, 400, 400, 2);
        assert!((fine - reference).abs() < (coarse - reference).abs());
    }
}
