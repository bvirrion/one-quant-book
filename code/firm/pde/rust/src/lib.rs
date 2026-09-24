//! firm.pde (Rust twin): the one-dimensional finite-difference kernel of the miniature firm. One Quant Book 4, ch. 27.
//! u_tau = a u_xx + b u_x - c u, theta scheme with Rannacher start-up and zero-gamma (linear) boundaries; the same
//! operations in the same order as firm_pde.py and the C++20 header.

/// Coefficients of L at the interior nodes: (L u)_i = lo u_{i-1} + di u_i + up u_{i+1}.
pub struct Tridiag {
    pub lo: Vec<f64>,
    pub di: Vec<f64>,
    pub up: Vec<f64>,
}

pub fn operator_1d(x: &[f64], a: f64, b: f64, c: f64) -> Tridiag {
    let m = x.len() - 2;
    let mut l = Tridiag { lo: vec![0.0; m], di: vec![0.0; m], up: vec![0.0; m] };
    for k in 0..m {
        let hm = x[k + 1] - x[k];
        let hp = x[k + 2] - x[k + 1];
        let lo = 2.0 * a / (hm * (hm + hp));
        let up = 2.0 * a / (hp * (hm + hp));
        l.lo[k] = lo + (-b * hp) / (hm * (hm + hp));
        l.up[k] = up + b * hm / (hp * (hm + hp));
        l.di[k] = (-lo - up - c) + b * (hp - hm) / (hm * hp);
    }
    l
}

/// Thomas algorithm for a tridiagonal system.
pub fn thomas(lo: &[f64], di: &[f64], up: &[f64], rhs: &[f64]) -> Vec<f64> {
    let n = di.len();
    let mut cp = vec![0.0; n];
    let mut dp = vec![0.0; n];
    cp[0] = up[0] / di[0];
    dp[0] = rhs[0] / di[0];
    for i in 1..n {
        let m = di[i] - lo[i] * cp[i - 1];
        cp[i] = if i < n - 1 { up[i] / m } else { 0.0 };
        dp[i] = (rhs[i] - lo[i] * dp[i - 1]) / m;
    }
    let mut out = vec![0.0; n];
    out[n - 1] = dp[n - 1];
    for i in (0..n - 1).rev() {
        out[i] = dp[i] - cp[i] * out[i + 1];
    }
    out
}

/// One theta step with linear extrapolation at both ends.
pub fn theta_step(x: &[f64], u: &[f64], l: &Tridiag, dt: f64, theta: f64) -> Vec<f64> {
    let m = x.len() - 2;
    let n = x.len() - 1;
    let mut rhs = vec![0.0; m];
    let mut alo = vec![0.0; m];
    let mut adi = vec![0.0; m];
    let mut aup = vec![0.0; m];
    for k in 0..m {
        rhs[k] = u[k + 1] + (1.0 - theta) * dt * (l.lo[k] * u[k] + l.di[k] * u[k + 1] + l.up[k] * u[k + 2]);
        alo[k] = -theta * dt * l.lo[k];
        adi[k] = 1.0 - theta * dt * l.di[k];
        aup[k] = -theta * dt * l.up[k];
    }
    let (l0, l1) = (x[1] - x[0], x[2] - x[1]);
    let (r0, r1) = (x[n] - x[n - 1], x[n - 1] - x[n - 2]);
    adi[0] += alo[0] * (1.0 + l0 / l1);
    aup[0] += alo[0] * (-l0 / l1);
    adi[m - 1] += aup[m - 1] * (1.0 + r0 / r1);
    alo[m - 1] += aup[m - 1] * (-r0 / r1);
    let inner = thomas(&alo, &adi, &aup, &rhs);
    let mut out = vec![0.0; n + 1];
    out[1..=m].copy_from_slice(&inner);
    out[0] = out[1] - (out[2] - out[1]) * l0 / l1;
    out[n] = out[n - 1] + (out[n - 1] - out[n - 2]) * r0 / r1;
    out
}

/// March from the payoff to tau; `rannacher` implicit half steps replace the first rannacher / 2 steps.
#[allow(clippy::too_many_arguments)]
pub fn solve_1d(x: &[f64], payoff: Vec<f64>, a: f64, b: f64, c: f64, tau: f64, n_steps: usize, theta: f64,
                rannacher: usize) -> Vec<f64> {
    let l = operator_1d(x, a, b, c);
    let dt = tau / n_steps as f64;
    let mut u = payoff;
    for _ in 0..rannacher {
        u = theta_step(x, &u, &l, dt / 2.0, 1.0);
    }
    for _ in 0..n_steps - rannacher / 2 {
        u = theta_step(x, &u, &l, dt, theta);
    }
    u
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn crank_nicolson_call_matches_python_and_black_scholes() {
        let (k, r, sigma, t) = (100.0_f64, 0.03, 0.2, 0.25);
        let (lo, hi) = (4.105170185988092_f64, 5.105170185988092_f64);
        let n = 400;
        let step = (hi - lo) / n as f64;
        let mut x: Vec<f64> = (0..=n).map(|i| i as f64 * step + lo).collect();
        x[n] = hi;
        let pay: Vec<f64> = x.iter().map(|v| (v.exp() - k).max(0.0)).collect();
        let (a, b) = (0.5 * sigma * sigma, r - 0.5 * sigma * sigma);
        let cn = solve_1d(&x, pay.clone(), a, b, r, t, 25, 0.5, 0);
        let cn4 = solve_1d(&x, pay, a, b, r, t, 25, 0.5, 4);
        assert!((cn[200] - 4.375764376609226).abs() < 1e-11 && (cn[180] - 2.155015812022793).abs() < 1e-11);
        assert!((cn4[200] - 4.3567077082780585).abs() < 1e-11 && (cn4[180] - 2.154527540626845).abs() < 1e-11);
        assert!((cn4[200] - 4.3576193334575635).abs() < 1e-3);
        assert!(cn[201] - 2.0 * cn[200] + cn[199] < 0.0 && cn4[201] - 2.0 * cn4[200] + cn4[199] > 0.0);
    }
}
