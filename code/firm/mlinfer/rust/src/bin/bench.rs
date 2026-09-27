//! Latency of the Rust kernels, one call at a time (run by bench_infer.py; not a test).
use firm_mlinfer::{vectors, Forest, Mlp, FOREST, MLP};
use std::hint::black_box;
use std::time::Instant;

fn pct(v: &mut [f64], q: f64) -> f64 {
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    v[((v.len() as f64 - 1.0) * q).round() as usize]
}

fn main() {
    let f = Forest::parse(FOREST);
    let m = Mlp::parse(MLP);
    let rows = vectors();
    for (name, which) in [("rust forest", 0), ("rust int8 mlp", 1)] {
        let mut t = Vec::with_capacity(200_000);
        for k in 0..200_000 {
            let x = &rows[k % rows.len()][..16];
            let t0 = Instant::now();
            let y = if which == 0 { f.predict(black_box(x)) } else { m.predict(black_box(x)) };
            black_box(y);
            t.push(t0.elapsed().as_nanos() as f64);
        }
        let med = pct(&mut t, 0.5);
        let p99 = pct(&mut t, 0.99);
        let p999 = pct(&mut t, 0.999);
        println!("{name},{med},{p99},{p999}");
    }
}
