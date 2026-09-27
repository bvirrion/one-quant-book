//! Chapter 9 benchmark: ns per message decoding Book 1's sample with the Rust twin of the feed decoder, and ns per
//! element for the counted loop, the checked gather and the unchecked gather. Prints `impl,ns`.
use std::hint::black_box;
use std::time::Instant;

fn best<F: FnMut()>(mut f: F, reps: usize) -> f64 {
    (0..reps)
        .map(|_| {
            let t = Instant::now();
            f();
            t.elapsed().as_nanos() as f64
        })
        .fold(f64::INFINITY, f64::min)
}

fn main() {
    let data = std::fs::read("code/firm/feed/data/sample.itch").expect("sample");
    let n_msgs = firm_feed::decode(&data).count();
    let passes = 300;
    let dec = best(
        || {
            let mut acc = 0u64;
            for _ in 0..passes {
                for m in firm_feed::decode(&data).flatten() {
                    acc = (acc ^ m.reference).wrapping_mul(1_099_511_628_211);
                }
            }
            black_box(acc);
        },
        5,
    ) / (passes * n_msgs) as f64;
    let v: Vec<u32> = (0..1u32 << 16).collect();
    let idx: Vec<usize> = (0..v.len()).map(|i| (i * 7919) % v.len()).collect();
    let n = v.len() as f64;
    let counted = best(
        || {
            // SAFETY: a pointer to v.len() elements of v.
            black_box(unsafe { ll_rust::sum_counted(v.as_ptr(), v.len()) });
        },
        50,
    ) / n;
    let gather = best(
        || {
            black_box(ll_rust::sum_gather(&v, &idx));
        },
        50,
    ) / n;
    // SAFETY: every index is (i * 7919) % len < len.
    let unchecked = best(
        || {
            black_box(unsafe { ll_rust::sum_gather_unchecked(&v, &idx) });
        },
        50,
    ) / n;
    println!("impl,ns");
    println!("rust decode,{dec:.3}\nrust counted loop,{counted:.4}\nrust gather checked,{gather:.4}\nrust gather unchecked,{unchecked:.4}");
}
