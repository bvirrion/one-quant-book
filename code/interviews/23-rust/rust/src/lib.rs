//! Book 18, chapter 23: the Rust coding answers.

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;

/// Push a new level and return the old best: copy the value out, then mutate.
pub fn push_level(levels: &mut Vec<i64>, new_level: i64) -> Option<i64> {
    let best = levels.first().copied();
    levels.push(new_level);
    best
}

/// Update two different elements of one slice mutably at once by splitting the borrow.
pub fn move_qty(qty: &mut [i64], from: usize, to: usize, amount: i64) {
    assert!(from != to, "from and to must differ");
    let (lo, hi) = qty.split_at_mut(from.max(to));
    let (a, b) = if from < to {
        (&mut lo[from], &mut hi[0])
    } else {
        (&mut hi[0], &mut lo[to])
    };
    *a -= amount;
    *b += amount;
}

/// Total volume per symbol with the entry API: one lookup per trade.
pub fn volume_by_symbol<'a>(trades: &[(&'a str, u64)]) -> HashMap<&'a str, u64> {
    let mut out = HashMap::new();
    for &(sym, v) in trades {
        *out.entry(sym).or_insert(0) += v;
    }
    out
}

/// A zero-copy parser of '|'-separated fields that borrow from the buffer.
pub struct Fields<'a> {
    buf: &'a [u8],
    pos: usize,
}

impl<'a> Fields<'a> {
    pub fn new(buf: &'a [u8]) -> Self {
        Fields { buf, pos: 0 }
    }
}

impl<'a> Iterator for Fields<'a> {
    type Item = &'a [u8];
    fn next(&mut self) -> Option<&'a [u8]> {
        if self.pos > self.buf.len() {
            return None;
        }
        let rest = &self.buf[self.pos..];
        let end = rest.iter().position(|&c| c == b'|').unwrap_or(rest.len());
        self.pos += end + 1;
        Some(&rest[..end])
    }
}

/// A strategy interface used both statically (generics) and dynamically (trait objects).
pub trait Strategy {
    fn signal(&self, price: i64) -> i64;
}

pub struct Threshold(pub i64);

impl Strategy for Threshold {
    fn signal(&self, price: i64) -> i64 {
        if price > self.0 {
            -1
        } else {
            1
        }
    }
}

pub fn run_static<S: Strategy>(s: &S, prices: &[i64]) -> i64 {
    prices.iter().map(|&p| s.signal(p)).sum()
}

pub fn run_dynamic(s: &dyn Strategy, prices: &[i64]) -> i64 {
    prices.iter().map(|&p| s.signal(p)).sum()
}

/// Sum of the first n prices without per-element bounds checks: n is checked once.
pub fn sum_first(prices: &[i64], n: usize) -> i64 {
    assert!(n <= prices.len());
    let mut s = 0;
    for i in 0..n {
        // SAFETY: i < n <= prices.len(), checked by the assert above.
        s += unsafe { *prices.get_unchecked(i) };
    }
    s
}

/// A counter shared by threads: fetch_add loses no increment; Relaxed suffices for a count.
pub fn count_in_threads(threads: usize, per_thread: u64) -> u64 {
    let c = Arc::new(AtomicU64::new(0));
    let handles: Vec<_> = (0..threads)
        .map(|_| {
            let c = Arc::clone(&c);
            thread::spawn(move || {
                for _ in 0..per_thread {
                    c.fetch_add(1, Ordering::Relaxed);
                }
            })
        })
        .collect();
    for h in handles {
        h.join().expect("thread panicked");
    }
    c.load(Ordering::Relaxed)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn push_level_returns_old_best() {
        let mut v = vec![101, 100];
        assert_eq!(push_level(&mut v, 99), Some(101));
        assert_eq!(v, vec![101, 100, 99]);
        let mut e: Vec<i64> = vec![];
        assert_eq!(push_level(&mut e, 5), None);
    }

    #[test]
    fn split_borrow() {
        let mut q = vec![10, 20, 30];
        move_qty(&mut q, 2, 0, 5);
        assert_eq!(q, vec![15, 20, 25]);
        move_qty(&mut q, 0, 1, 15);
        assert_eq!(q, vec![0, 35, 25]);
    }

    #[test]
    fn entry_api() {
        let m = volume_by_symbol(&[("A", 5), ("B", 9), ("A", 7)]);
        assert_eq!(m["A"], 12);
        assert_eq!(m["B"], 9);
    }

    #[test]
    fn parser_borrows() {
        let msg = b"NEW|ABC|101.5|300".to_vec();
        let f: Vec<&[u8]> = Fields::new(&msg).collect();
        assert_eq!(
            f,
            vec![&b"NEW"[..], &b"ABC"[..], &b"101.5"[..], &b"300"[..]]
        );
        assert_eq!(Fields::new(b"").count(), 1);
        assert_eq!(Fields::new(b"a||b").count(), 3);
    }

    #[test]
    fn static_and_dynamic_agree() {
        let s = Threshold(100);
        let p = [99, 101, 100, 150];
        assert_eq!(run_static(&s, &p), run_dynamic(&s, &p));
        assert_eq!(run_static(&s, &p), 0);
    }

    #[test]
    fn unchecked_sum() {
        assert_eq!(sum_first(&[1, 2, 3, 4], 3), 6);
    }

    #[test]
    #[should_panic]
    fn unchecked_sum_rejects_bad_n() {
        sum_first(&[1, 2], 3);
    }

    #[test]
    fn atomic_counter() {
        assert_eq!(count_in_threads(4, 100_000), 400_000);
    }
}
