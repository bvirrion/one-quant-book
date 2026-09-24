//! firm.mcengine (Rust twin): the Monte Carlo engine of the miniature firm. One Quant Book 4, ch. 2, 4, 26.
//! Stage 1: SplitMix64 reference generator, Box-Muller normals, Brownian paths by increments and by
//! dyadic Brownian-bridge construction, bridge crossing probability. Same stream as the Python and
//! C++20 twins from the same seed.

/// Vigna's SplitMix64.
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
    /// Top 53 bits, centred in their cell: uniform on the open interval (0, 1).
    pub fn uniform(&mut self) -> f64 {
        ((self.next_u64() >> 11) as f64 + 0.5) * (1.0 / (1u64 << 53) as f64)
    }
}

/// Standard normals by Box-Muller, cosine first.
pub struct NormalStream {
    gen: SplitMix64,
    spare: Option<f64>,
}

impl NormalStream {
    pub fn new(seed: u64) -> Self {
        Self { gen: SplitMix64::new(seed), spare: None }
    }
    pub fn next_normal(&mut self) -> f64 {
        if let Some(z) = self.spare.take() {
            return z;
        }
        let u1 = self.gen.uniform();
        let u2 = self.gen.uniform();
        let r = (-2.0 * u1.ln()).sqrt();
        let a = 2.0 * std::f64::consts::PI * u2;
        self.spare = Some(r * a.sin());
        r * a.cos()
    }
}

/// W_0 = 0 and n_steps Gaussian increments of variance T / n_steps.
pub fn brownian_path(n_steps: usize, t: f64, z: &mut NormalStream) -> Vec<f64> {
    let s = (t / n_steps as f64).sqrt();
    let mut w = vec![0.0; n_steps + 1];
    for k in 0..n_steps {
        w[k + 1] = w[k] + s * z.next_normal();
    }
    w
}

/// 2^levels steps built coarse to fine: W_T, then midpoints from N((W_l + W_r)/2, h/4).
pub fn bridge_path(levels: u32, t: f64, z: &mut NormalStream) -> Vec<f64> {
    let n = 1usize << levels;
    let dt = t / n as f64;
    let mut w = vec![0.0; n + 1];
    w[n] = t.sqrt() * z.next_normal();
    let mut step = n;
    while step > 1 {
        let half = step / 2;
        let sd = (half as f64 * dt / 2.0).sqrt();
        let mut i = half;
        while i < n {
            w[i] = 0.5 * (w[i - half] + w[i + half]) + sd * z.next_normal();
            i += step;
        }
        step = half;
    }
    w
}

/// Probability that a Brownian bridge from x0 to x1 with variance var touches the barrier.
pub fn bridge_crossing_probability(x0: f64, x1: f64, barrier: f64, var: f64) -> f64 {
    let prod = (x0 - barrier) * (x1 - barrier);
    if prod > 0.0 {
        (-2.0 * prod / var).exp()
    } else {
        1.0
    }
}

// ---- Stage 2 (chapter 4): SDE stepping ----------------------------------------------------------

/// Scheme for the square-root process.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum SqrtScheme {
    Plain,
    FullTruncation,
}

/// Exact Ornstein-Uhlenbeck transition on n_steps equal steps of [0, T].
pub fn ou_exact_path(x0: f64, kappa: f64, xbar: f64, sigma: f64, t: f64, n_steps: usize, z: &mut NormalStream) -> Vec<f64> {
    let dt = t / n_steps as f64;
    let a = (-kappa * dt).exp();
    let sd = sigma * ((1.0 - a * a) / (2.0 * kappa)).sqrt();
    let mut x = vec![x0; n_steps + 1];
    for k in 0..n_steps {
        x[k + 1] = xbar + (x[k] - xbar) * a + sd * z.next_normal();
    }
    x
}

/// Euler steps of the square-root process; plain gives NaN after a negative value, full truncation
/// uses max(v, 0) in drift and diffusion and reports max(v, 0).
#[allow(clippy::too_many_arguments)]
pub fn sqrt_euler_path(v0: f64, kappa: f64, vbar: f64, eta: f64, t: f64, n_steps: usize, z: &mut NormalStream, scheme: SqrtScheme) -> Vec<f64> {
    let dt = t / n_steps as f64;
    let sdt = dt.sqrt();
    let mut v = vec![v0; n_steps + 1];
    for k in 0..n_steps {
        let vk = if scheme == SqrtScheme::Plain { v[k] } else { v[k].max(0.0) };
        v[k + 1] = v[k] + kappa * (vbar - vk) * dt + eta * vk.sqrt() * sdt * z.next_normal();
    }
    if scheme == SqrtScheme::FullTruncation {
        for x in v.iter_mut() {
            *x = x.max(0.0);
        }
    }
    v
}

/// 2 kappa vbar / eta^2.
pub fn feller_ratio(kappa: f64, vbar: f64, eta: f64) -> f64 {
    2.0 * kappa * vbar / (eta * eta)
}

// ---- Stage 3 (chapter 26): counter-based streams and scrambled Sobol points ----------------

/// Philox4x64-10 (Salmon, Moraes, Dror and Shaw 2011): a bijection of a 256-bit counter under a 128-bit key.
pub fn philox4x64(mut c: [u64; 4], mut k: [u64; 2]) -> [u64; 4] {
    const M0: u64 = 0xD2E7_470E_E14C_6C93;
    const M1: u64 = 0xCA5A_8263_9512_1157;
    const W0: u64 = 0x9E37_79B9_7F4A_7C15;
    const W1: u64 = 0xBB67_AE85_84CA_A73B;
    for _ in 0..10 {
        let p0 = (M0 as u128) * (c[0] as u128);
        let p1 = (M1 as u128) * (c[2] as u128);
        c = [((p1 >> 64) as u64) ^ c[1] ^ k[0], p1 as u64, ((p0 >> 64) as u64) ^ c[3] ^ k[1], p0 as u64];
        k = [k[0].wrapping_add(W0), k[1].wrapping_add(W1)];
    }
    c
}

/// First eight Sobol dimensions (Joe and Kuo, new-joe-kuo-6.21201): s, a, m_1..m_s.
const JOE_KUO: [(u32, u32, [u32; 5]); 7] = [
    (1, 0, [1, 0, 0, 0, 0]),
    (2, 1, [1, 3, 0, 0, 0]),
    (3, 1, [1, 3, 1, 0, 0]),
    (3, 2, [1, 1, 1, 0, 0]),
    (4, 1, [1, 1, 3, 3, 0]),
    (4, 4, [1, 3, 5, 13, 0]),
    (5, 2, [1, 1, 5, 5, 17]),
];

pub fn sobol_directions(dim: usize) -> [u32; 32] {
    let mut v = [0u32; 32];
    if dim == 0 {
        for (k, x) in v.iter_mut().enumerate() {
            *x = 1u32 << (31 - k);
        }
        return v;
    }
    let (s, a, m) = JOE_KUO[dim - 1];
    let s = s as usize;
    for k in 0..s {
        v[k] = m[k] << (31 - k);
    }
    for i in s..32 {
        let mut x = v[i - s] ^ (v[i - s] >> s);
        for k in 1..s {
            if (a >> (s - 1 - k)) & 1 == 1 {
                x ^= v[i - k];
            }
        }
        v[i] = x;
    }
    v
}

/// Point i (Gray-code order) of dimension dim, as a 32-bit integer.
pub fn sobol_point(i: u32, dim: usize) -> u32 {
    let v = sobol_directions(dim);
    let mut g = i ^ (i >> 1);
    let mut x = 0u32;
    let mut b = 0;
    while g != 0 {
        if g & 1 == 1 {
            x ^= v[b];
        }
        g >>= 1;
        b += 1;
    }
    x
}

pub fn mix64(mut z: u64) -> u64 {
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// Owen (nested uniform) scrambling: digit l is flipped by the hashed bit of tree node (dim, l, top l digits).
pub fn owen_scramble(x: u32, dim: usize, seed: u64) -> u32 {
    let mut y = x;
    for lev in 0..32u64 {
        let prefix = if lev == 0 { 0 } else { (x as u64) >> (32 - lev) };
        let node = ((dim as u64) << 40) ^ (lev << 32) ^ prefix;
        let bit = mix64(seed ^ mix64(node)) >> 63;
        y ^= (bit << (31 - lev)) as u32;
    }
    y
}

#[cfg(test)]
mod tests {
    use super::*;

    fn near(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    #[test]
    fn splitmix_test_vector() {
        let mut g = SplitMix64::new(1_234_567);
        let want = [
            6_457_827_717_110_365_317u64,
            3_203_168_211_198_807_973,
            9_817_491_932_198_370_423,
            4_593_380_528_125_082_431,
            16_408_922_859_458_223_821,
        ];
        for w in want {
            assert_eq!(g.next_u64(), w);
        }
    }

    #[test]
    fn reference_stream_matches_python() {
        let mut s = NormalStream::new(42);
        for w in [0.414_719_750_431_530_37, 0.652_681_222_151_942_8, -0.891_886_213_627_756_8, 1.326_833_562_814_106] {
            assert!(near(s.next_normal(), w, 1e-15));
        }
        let mut z = NormalStream::new(7);
        let p = brownian_path(4, 1.0, &mut z);
        assert!(near(p[4], 0.442_696_616_019_979_56, 1e-14));
    }

    #[test]
    fn variances() {
        let mut z = NormalStream::new(11);
        let n = 40_000;
        let (mut s2, mut b2, mut m2) = (0.0, 0.0, 0.0);
        for _ in 0..n {
            let p = brownian_path(8, 2.0, &mut z);
            s2 += p[8] * p[8];
            let b = bridge_path(3, 2.0, &mut z);
            b2 += b[8] * b[8];
            m2 += b[4] * b[4];
        }
        let n = n as f64;
        assert!(near(s2 / n, 2.0, 0.06) && near(b2 / n, 2.0, 0.06) && near(m2 / n, 1.0, 0.03));
    }

    #[test]
    fn crossing() {
        assert_eq!(bridge_crossing_probability(0.5, -0.1, 0.0, 1.0), 1.0);
        assert!(near(bridge_crossing_probability(0.3, 0.2, 0.0, 1.0), (-0.12f64).exp(), 1e-15));
    }

    #[test]
    fn stage2_schemes() {
        let mut z = NormalStream::new(21);
        let n = 20_000;
        let (mut m, mut m2) = (0.0, 0.0);
        for _ in 0..n {
            let x = ou_exact_path(0.5, 2.0, 0.1, 0.4, 5.0, 10, &mut z);
            let e = *x.last().unwrap();
            m += e;
            m2 += e * e;
        }
        let nf = n as f64;
        m /= nf;
        assert!(near(m, 0.1, 0.01) && near(m2 / nf - m * m, 0.04, 0.003));
        let (mut neg_plain, mut neg_ft) = (0, 0);
        for _ in 0..2000 {
            let p = sqrt_euler_path(0.04, 2.0, 0.04, 0.6, 1.0, 252, &mut z, SqrtScheme::Plain);
            if p.iter().any(|v| v.is_nan() || *v < 0.0) {
                neg_plain += 1;
            }
            let f = sqrt_euler_path(0.04, 2.0, 0.04, 0.6, 1.0, 252, &mut z, SqrtScheme::FullTruncation);
            neg_ft += f.iter().filter(|v| v.is_nan() || **v < 0.0).count();
        }
        assert!(neg_plain > 100 && neg_ft == 0);
        assert!(near(feller_ratio(2.0, 0.04, 0.6), 0.16 / 0.36, 1e-15));
    }

    #[test]
    fn stage3_philox_and_sobol() {
        assert_eq!(philox4x64([1, 0, 0, 0], [7, 0]),
                   [0xdf40_34b8_29e9_fba4, 0x4b9d_10cd_f8e6_4087, 0x6b8b_857e_506a_ac98, 0x67c7_c945_b1ba_6e52]);
        assert_eq!(philox4x64([0, 0, 0, 0], [2600, 0]),
                   [0x6574_e96a_9536_cfeb, 0x5453_56bd_c874_1804, 0x712f_1a3a_7274_032e, 0x5b41_a2f7_8985_5f11]);
        let want = [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.75, 0.25, 0.25], [0.25, 0.75, 0.75], [0.375, 0.375, 0.625],
                    [0.875, 0.875, 0.125], [0.625, 0.125, 0.875], [0.125, 0.625, 0.375], [0.1875, 0.3125, 0.9375],
                    [0.6875, 0.8125, 0.4375]];
        for (i, row) in want.iter().enumerate() {
            for (d, w) in row.iter().enumerate() {
                assert_eq!(sobol_point(i as u32, d) as f64 / 4_294_967_296.0, *w);
            }
        }
        let mut sum = 0u64;
        for i in 0..16u32 {
            for d in 0..8 {
                sum += owen_scramble(sobol_point(i, d), d, 2600) as u64;
            }
        }
        assert_eq!(sum, 275_744_286_821);
        assert_eq!(owen_scramble(sobol_point(5, 3), 3, 2600), 1_066_785_506);
        assert_eq!(owen_scramble(sobol_point(15, 7), 7, 2600), 4_087_102_229);
    }
}
