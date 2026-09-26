//! Chapter 9 of One Quant Book 13: Rust on the hot path. Bounds checks and when the compiler removes them, the same
//! message handler with and without allocation, and a data race the compiler refuses.
//!
//! Sharing a book mutably with another thread does not compile:
//! ```compile_fail
//! let mut book = vec![0u64; 4];
//! let t = std::thread::spawn(|| book[0] += 1); // `book` borrowed mutably by a thread that may outlive it
//! book[1] += 1;
//! t.join().unwrap();
//! ```

use std::collections::HashMap;

/// Indexing by a loop counter bounded by the slice's own length: the compiler proves every index valid and removes
/// the checks. Exported with a C name so that its assembly can be printed.
///
/// # Safety
/// `v` must point to `n` initialised `u32` values.
#[no_mangle]
#[allow(clippy::needless_range_loop)] // the indexed loop is the point of the example
pub unsafe extern "C" fn sum_counted(v: *const u32, n: usize) -> u64 {
    // SAFETY: guaranteed by the caller, per this function's contract.
    let v = unsafe { std::slice::from_raw_parts(v, n) };
    let mut s = 0u64;
    for i in 0..v.len() {
        s += u64::from(v[i]);
    }
    s
}

/// One indexed read with an index the compiler knows nothing about: a comparison and a branch to the panic handler.
///
/// # Safety
/// `v` must point to `n` initialised `u32` values.
#[no_mangle]
pub unsafe extern "C" fn get_checked(v: *const u32, n: usize, i: usize) -> u32 {
    // SAFETY: guaranteed by the caller, per this function's contract.
    let v = unsafe { std::slice::from_raw_parts(v, n) };
    v[i]
}

/// Indexing by values from another slice: each index is checked, and a bad one panics instead of reading memory.
pub fn sum_gather(v: &[u32], idx: &[usize]) -> u64 {
    idx.iter().map(|&i| u64::from(v[i])).sum()
}

/// The same gather with the check removed; sound only if every index is below `v.len()`, which the caller promises.
///
/// # Safety
/// Every element of `idx` must be less than `v.len()`.
pub unsafe fn sum_gather_unchecked(v: &[u32], idx: &[usize]) -> u64 {
    // SAFETY: guaranteed by the caller, per this function's contract.
    idx.iter()
        .map(|&i| u64::from(unsafe { *v.get_unchecked(i) }))
        .sum()
}

/// A sound abstraction over the unchecked gather: it validates the indices once, then gathers without checks.
pub struct CheckedIndex<'a> {
    idx: &'a [usize],
}

impl<'a> CheckedIndex<'a> {
    pub fn new(idx: &'a [usize], len: usize) -> Option<CheckedIndex<'a>> {
        idx.iter().all(|&i| i < len).then_some(CheckedIndex { idx })
    }
    pub fn sum(&self, v: &[u32], len: usize) -> Option<u64> {
        // The indices were checked against `len`; refuse a slice of another length rather than trust it.
        // SAFETY: every index < len == v.len().
        (v.len() == len).then(|| unsafe { sum_gather_unchecked(v, self.idx) })
    }
}

#[derive(Clone, Copy)]
pub struct Fill {
    pub price: i64,
    pub qty: u32,
}

pub type Callback = Box<dyn Fn(&[Fill]) -> usize>;

/// The first-draft handler of chapter 6, in Rust.
#[derive(Default)]
pub struct NaiveHandler {
    pub state: HashMap<String, u32>,
    pub on_done: Option<Callback>,
}

impl NaiveHandler {
    pub fn handle(&mut self, symbol: &str, client_id: &str, fills: &[Fill]) -> usize {
        let sym = symbol.to_string(); // a String always allocates (no inline buffer)
        let cid = client_id.to_string();
        let mut fs = Vec::new(); // the first push reserves room for four fills
        for f in fills {
            fs.push(*f);
        }
        *self.state.entry(cid).or_insert(0) += fills.len() as u32;
        let copy = fs.clone();
        self.on_done = Some(Box::new(move |_| copy.len() + sym.len()));
        self.on_done.as_ref().map_or(0, |f| f(&fs))
    }
}

/// The same work with storage fixed in advance.
pub struct FixedHandler {
    ids: [[u8; 24]; 64],
    counts: [u32; 64],
    n: usize,
}

impl Default for FixedHandler {
    fn default() -> Self {
        FixedHandler {
            ids: [[0; 24]; 64],
            counts: [0; 64],
            n: 0,
        }
    }
}

impl FixedHandler {
    pub fn handle(&mut self, symbol: &str, client_id: &str, fills: &[Fill]) -> usize {
        let mut key = [0u8; 24];
        let b = client_id.as_bytes();
        key[..b.len().min(24)].copy_from_slice(&b[..b.len().min(24)]);
        let slot = match self.ids[..self.n].iter().position(|k| *k == key) {
            Some(i) => i,
            None if self.n < 64 => {
                self.ids[self.n] = key;
                self.n += 1;
                self.n - 1
            }
            None => return 0, // full: refuse
        };
        self.counts[slot] += fills.len() as u32;
        fills.len().min(8) + symbol.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use firm_arena::{allocations, CountingAlloc};

    #[global_allocator]
    static A: CountingAlloc = CountingAlloc;

    #[test]
    fn bounds_checks_and_soundness() {
        let v: Vec<u32> = (0..100).collect();
        // SAFETY: a pointer to v.len() elements of v.
        assert_eq!(unsafe { sum_counted(v.as_ptr(), v.len()) }, 4950);
        let idx = [3usize, 7, 99];
        assert_eq!(sum_gather(&v, &idx), 109);
        let ci = CheckedIndex::new(&idx, v.len()).unwrap();
        assert_eq!(ci.sum(&v, v.len()), Some(109));
        assert!(CheckedIndex::new(&[100], v.len()).is_none());
        assert!(std::panic::catch_unwind(|| sum_gather(&[1, 2], &[5])).is_err());
    }

    #[test]
    fn allocations_per_message() {
        let f = [
            Fill { price: 100, qty: 1 },
            Fill { price: 101, qty: 2 },
            Fill { price: 102, qty: 3 },
        ];
        let mut naive = NaiveHandler::default();
        let mut fixed = FixedHandler::default();
        naive.handle("ESZ6", "CLIENT-ORDER-0000001-A", &f);
        fixed.handle("ESZ6", "CLIENT-ORDER-0000001-A", &f);
        let a0 = allocations();
        naive.handle("ESZ6", "CLIENT-ORDER-0000002-A", &f);
        let n = allocations() - a0;
        let a1 = allocations();
        fixed.handle("ESZ6", "CLIENT-ORDER-0000002-A", &f);
        let x = allocations() - a1;
        assert_eq!((n, x), (5, 0), "naive {n}, fixed {x}");
    }
}
