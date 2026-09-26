//! firm.arena -- Rust twin of `cpp/firm_arena.hpp` (One Quant Book 13, chapter 6): a bump arena, an object pool with
//! a free list of indices, and a counting global allocator for tests that assert zero allocations on a hot path.

use std::alloc::{GlobalAlloc, Layout, System};
use std::cell::Cell;
use std::sync::atomic::{AtomicU64, Ordering};

/// Bump allocator over one pre-faulted block, handing out byte ranges (offsets) rather than raw pointers.
pub struct Arena {
    buf: Vec<u8>,
    used: usize,
}

impl Arena {
    pub fn new(bytes: usize) -> Arena {
        Arena { buf: vec![0u8; bytes], used: 0 } // vec! of zeros writes every page: pre-faulted
    }
    /// Offset of `n` bytes aligned to `align`, or None when full (never grows).
    pub fn allocate(&mut self, n: usize, align: usize) -> Option<usize> {
        let at = (self.used + align - 1) & !(align - 1);
        if at + n > self.buf.len() {
            return None;
        }
        self.used = at + n;
        Some(at)
    }
    pub fn bytes(&mut self, at: usize, n: usize) -> &mut [u8] {
        &mut self.buf[at..at + n]
    }
    pub fn reset(&mut self) {
        self.used = 0;
    }
    pub fn used(&self) -> usize {
        self.used
    }
}

/// Fixed-capacity pool: slots hold values, a stack of free indices replaces the intrusive list.
pub struct Pool<T> {
    slots: Vec<Option<T>>,
    free: Vec<u32>,
}

impl<T> Pool<T> {
    pub fn with_capacity(n: usize) -> Pool<T> {
        let mut slots = Vec::with_capacity(n);
        slots.resize_with(n, || None);
        Pool { slots, free: (0..n as u32).rev().collect() }
    }
    /// Index of the new object, or None when exhausted (never allocates).
    pub fn create(&mut self, v: T) -> Option<u32> {
        let i = self.free.pop()?;
        self.slots[i as usize] = Some(v);
        Some(i)
    }
    pub fn get(&mut self, i: u32) -> Option<&mut T> {
        self.slots[i as usize].as_mut()
    }
    pub fn destroy(&mut self, i: u32) -> Option<T> {
        let v = self.slots[i as usize].take()?;
        self.free.push(i);
        Some(v)
    }
    pub fn live(&self) -> usize {
        self.slots.len() - self.free.len()
    }
}

/// A global allocator that counts allocations, in total and per thread (tests run in parallel threads, so a test
/// reads its own thread's count); install it in a test binary with `#[global_allocator]`.
pub struct CountingAlloc;
pub static ALLOCATIONS: AtomicU64 = AtomicU64::new(0);

thread_local! {
    static LOCAL: Cell<u64> = const { Cell::new(0) };
}

unsafe impl GlobalAlloc for CountingAlloc {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        let _ = LOCAL.try_with(|c| c.set(c.get() + 1)); // no allocation; fails harmlessly during thread teardown
        // SAFETY: forwarded unchanged to the system allocator, whose contract the caller already meets.
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        // SAFETY: `ptr` came from `alloc` above with this layout.
        unsafe { System.dealloc(ptr, layout) }
    }
}

/// Allocations made by the calling thread so far.
pub fn allocations() -> u64 {
    LOCAL.try_with(Cell::get).unwrap_or(0)
}

/// Allocations made by all threads so far.
pub fn allocations_total() -> u64 {
    ALLOCATIONS.load(Ordering::Relaxed)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[global_allocator]
    static A: CountingAlloc = CountingAlloc;

    #[derive(Debug, PartialEq)]
    struct Order {
        id: u64,
        price: i64,
        qty: u32,
    }

    #[test]
    fn arena_and_pool_do_not_allocate_after_construction() {
        let mut arena = Arena::new(1 << 16);
        let mut pool: Pool<Order> = Pool::with_capacity(1024);
        let before = allocations();
        let a = arena.allocate(24, 8).unwrap();
        let b = arena.allocate(3, 1).unwrap();
        let c = arena.allocate(8, 8).unwrap();
        assert_eq!((a, b, c % 8), (0, 24, 0));
        assert!(arena.allocate(1 << 17, 8).is_none());
        arena.reset();
        let mut ids = [0u32; 16];
        for (k, slot) in ids.iter_mut().enumerate() {
            *slot = pool.create(Order { id: k as u64, price: 100, qty: 1 }).unwrap();
        }
        let i3 = ids[3];
        let back = pool.destroy(i3).unwrap();
        assert_eq!(back.id, 3);
        assert_eq!(pool.create(Order { id: 99, price: 1, qty: 1 }), Some(i3));
        assert_eq!(pool.live(), 16);
        assert_eq!(allocations(), before, "heap allocation on the hot path");
    }
}
