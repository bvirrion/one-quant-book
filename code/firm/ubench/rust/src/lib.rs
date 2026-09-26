//! firm.ubench -- microbenchmark harness, Rust twin of `cpp/firm_ubench.hpp` (One Quant Book 13, chapter 2).
//! x86-64 only: the time-stamp counter is read with `_rdtsc` / `__rdtscp` behind fences.

use std::arch::x86_64::{__rdtscp, _mm_lfence, _rdtsc};
use std::hint::black_box;

/// Serialised start of a timed region: earlier instructions finish before the read.
#[inline(always)]
pub fn tsc_start() -> u64 {
    // SAFETY: lfence and rdtsc are available on every x86-64 processor.
    unsafe {
        _mm_lfence();
        _rdtsc()
    }
}

/// Serialised end of a timed region: the read waits for the region, later work waits for it.
#[inline(always)]
pub fn rdtscp() -> u64 {
    let mut aux = 0u32;
    // SAFETY: rdtscp exists on every x86-64 processor this crate targets (checked in the tests).
    unsafe {
        let t = __rdtscp(&mut aux);
        _mm_lfence();
        t
    }
}

#[repr(C)]
struct Timespec {
    tv_sec: i64,
    tv_nsec: i64,
}

extern "C" {
    fn clock_gettime(clock: i32, tp: *mut Timespec) -> i32;
}

const CLOCK_MONOTONIC_RAW: i32 = 4;

/// CLOCK_MONOTONIC_RAW in nanoseconds: the kernel's clock without time-synchronisation slewing.
pub fn raw_ns() -> f64 {
    let mut ts = Timespec { tv_sec: 0, tv_nsec: 0 };
    // SAFETY: `ts` is a valid, writable timespec with the C layout of x86-64 Linux.
    unsafe { clock_gettime(CLOCK_MONOTONIC_RAW, &mut ts) };
    ts.tv_sec as f64 * 1e9 + ts.tv_nsec as f64
}

/// Ticks per nanosecond, calibrated against CLOCK_MONOTONIC_RAW (std's `Instant` is CLOCK_MONOTONIC, which time
/// synchronisation slews).
#[derive(Clone, Copy, Debug)]
pub struct Clock {
    pub ticks_per_ns: f64,
}

impl Clock {
    pub fn calibrate(ms: u64) -> Clock {
        let w0 = raw_ns();
        let t0 = tsc_start();
        while raw_ns() - w0 < ms as f64 * 1e6 {}
        let t1 = rdtscp();
        let w1 = raw_ns();
        Clock { ticks_per_ns: (t1 - t0) as f64 / (w1 - w0) }
    }
    pub fn ns(&self, ticks: u64) -> f64 {
        ticks as f64 / self.ticks_per_ns
    }
}

/// Per-call cost of `f` in ticks: `warm` untimed calls, then `reps` timed ones.
pub fn run<F: FnMut()>(mut f: F, reps: usize, warm: usize) -> Vec<u64> {
    for _ in 0..warm {
        f();
    }
    (0..reps)
        .map(|_| {
            let a = tsc_start();
            f();
            rdtscp() - a
        })
        .collect()
}

/// Median cost of an empty timed region, in ticks.
pub fn overhead(reps: usize) -> u64 {
    let mut v = run(|| black_box(()), reps, 100);
    v.sort_unstable();
    v[reps / 2]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn calibration_is_plausible() {
        let c = Clock::calibrate(20);
        assert!(c.ticks_per_ns > 0.5 && c.ticks_per_ns < 6.0);
    }

    #[test]
    fn counter_is_monotonic_and_work_costs_more_than_nothing() {
        let mut prev = rdtscp();
        for _ in 0..100_000 {
            let t = rdtscp();
            assert!(t >= prev);
            prev = t;
        }
        let mut s = 1u64;
        let mut v = run(
            || {
                for _ in 0..1000 {
                    s = black_box(s.wrapping_mul(3).wrapping_add(1));
                }
            },
            2000,
            100,
        );
        v.sort_unstable();
        assert!(v[1000] > overhead(10_000));
    }
}
