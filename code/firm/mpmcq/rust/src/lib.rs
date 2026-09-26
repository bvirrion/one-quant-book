//! firm.mpmcq -- bounded MPMC queue, Rust twin of `cpp/firm_mpmcq.hpp` (One Quant Book 13, chapter 11): cells with
//! sequence numbers, one compare-and-swap per operation, no allocation after construction.

use std::cell::UnsafeCell;
use std::mem::MaybeUninit;
use std::sync::atomic::{AtomicUsize, Ordering};

struct Cell<T> {
    seq: AtomicUsize,
    value: UnsafeCell<MaybeUninit<T>>,
}

#[repr(align(64))]
struct Padded(AtomicUsize);

pub struct Queue<T> {
    mask: usize,
    cells: Box<[Cell<T>]>,
    tail: Padded,
    head: Padded,
}

// SAFETY: a cell's value is written only by the producer that claimed its position and read only by the consumer
// that claimed the same position, and the release/acquire pair on `seq` orders the write before the read.
unsafe impl<T: Send> Sync for Queue<T> {}
unsafe impl<T: Send> Send for Queue<T> {}

impl<T: Copy> Queue<T> {
    pub fn new(capacity: usize) -> Queue<T> {
        assert!(capacity >= 2 && capacity.is_power_of_two(), "capacity must be a power of two");
        let cells = (0..capacity)
            .map(|i| Cell { seq: AtomicUsize::new(i), value: UnsafeCell::new(MaybeUninit::uninit()) })
            .collect();
        Queue { mask: capacity - 1, cells, tail: Padded(AtomicUsize::new(0)), head: Padded(AtomicUsize::new(0)) }
    }

    pub fn try_push(&self, v: T) -> bool {
        let mut pos = self.tail.0.load(Ordering::Relaxed);
        loop {
            let c = &self.cells[pos & self.mask];
            let diff = c.seq.load(Ordering::Acquire) as isize - pos as isize;
            if diff == 0 {
                match self.tail.0.compare_exchange_weak(pos, pos + 1, Ordering::Relaxed, Ordering::Relaxed) {
                    Ok(_) => {
                        // SAFETY: this producer owns position `pos` until it publishes it below.
                        unsafe { (*c.value.get()).write(v) };
                        c.seq.store(pos + 1, Ordering::Release);
                        return true;
                    }
                    Err(now) => pos = now,
                }
            } else if diff < 0 {
                return false;
            } else {
                pos = self.tail.0.load(Ordering::Relaxed);
            }
        }
    }

    pub fn try_pop(&self) -> Option<T> {
        let mut pos = self.head.0.load(Ordering::Relaxed);
        loop {
            let c = &self.cells[pos & self.mask];
            let diff = c.seq.load(Ordering::Acquire) as isize - (pos + 1) as isize;
            if diff == 0 {
                match self.head.0.compare_exchange_weak(pos, pos + 1, Ordering::Relaxed, Ordering::Relaxed) {
                    Ok(_) => {
                        // SAFETY: the producer of `pos` initialised the value before its release store we acquired.
                        let v = unsafe { (*c.value.get()).assume_init() };
                        c.seq.store(pos + self.mask + 1, Ordering::Release);
                        return Some(v);
                    }
                    Err(now) => pos = now,
                }
            } else if diff < 0 {
                return None;
            } else {
                pos = self.head.0.load(Ordering::Relaxed);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicU8;
    use std::sync::Arc;

    #[test]
    fn fifo_full_empty() {
        let q = Queue::new(4);
        for i in 0..4 {
            assert!(q.try_push(i));
        }
        assert!(!q.try_push(9));
        for i in 0..4 {
            assert_eq!(q.try_pop(), Some(i));
        }
        assert_eq!(q.try_pop(), None);
    }

    #[test]
    fn every_item_exactly_once() {
        const P: usize = 2;
        const PER: usize = 150_000;
        let q = Arc::new(Queue::<u32>::new(1024));
        let seen: Arc<Vec<AtomicU8>> = Arc::new((0..P * PER).map(|_| AtomicU8::new(0)).collect());
        let done = Arc::new(AtomicUsize::new(0));
        let mut hs = Vec::new();
        for p in 0..P {
            let q = q.clone();
            hs.push(std::thread::spawn(move || {
                for i in 0..PER {
                    while !q.try_push((p * PER + i) as u32) {
                        std::thread::yield_now();
                    }
                }
            }));
        }
        for _ in 0..2 {
            let (q, seen, done) = (q.clone(), seen.clone(), done.clone());
            hs.push(std::thread::spawn(move || {
                while done.load(Ordering::Relaxed) < P * PER {
                    match q.try_pop() {
                        Some(v) => {
                            seen[v as usize].fetch_add(1, Ordering::Relaxed);
                            done.fetch_add(1, Ordering::Relaxed);
                        }
                        None => std::thread::yield_now(),
                    }
                }
            }));
        }
        for h in hs {
            h.join().unwrap();
        }
        assert!(seen.iter().all(|x| x.load(Ordering::Relaxed) == 1));
    }
}
