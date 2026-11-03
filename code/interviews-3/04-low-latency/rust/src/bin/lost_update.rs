use std::sync::atomic::{AtomicU64, Ordering::Relaxed};
use std::thread;

static COUNT: AtomicU64 = AtomicU64::new(0);

fn main() {
    thread::scope(|s| {
        for _ in 0..4 {
            s.spawn(|| {
                for _ in 0..1_000_000 {
                    let v = COUNT.load(Relaxed);
                    COUNT.store(v + 1, Relaxed);
                }
            });
        }
    });
    println!("{}", COUNT.load(Relaxed));
}
