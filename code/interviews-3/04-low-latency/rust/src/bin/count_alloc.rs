use std::alloc::{GlobalAlloc, Layout, System};
use std::hint::black_box;
use std::sync::atomic::{AtomicU64, Ordering::Relaxed};
use std::sync::Arc;

struct Counting;
static CALLS: AtomicU64 = AtomicU64::new(0);

unsafe impl GlobalAlloc for Counting {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        CALLS.fetch_add(1, Relaxed);
        System.alloc(l)
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) {
        System.dealloc(p, l)
    }
    unsafe fn realloc(&self, p: *mut u8, l: Layout, n: usize) -> *mut u8 {
        CALLS.fetch_add(1, Relaxed);
        System.realloc(p, l, n)
    }
}
#[global_allocator]
static A: Counting = Counting;

fn show<R>(name: &str, f: impl FnOnce() -> R) {
    let before = CALLS.load(Relaxed);
    black_box(f());
    println!("{name:<16} {}", CALLS.load(Relaxed) - before);
}

fn main() {
    show("Vec::new", Vec::<u64>::new);
    show("with_capacity(8)", || Vec::<u64>::with_capacity(8));
    show("String::new", String::new);
    show("to_string", || 7.to_string());
    show("Box<()>", || Box::new(()));
    show("Box<u64>", || Box::new(1_u64));
    show("1000 pushes", || {
        let mut v = Vec::new();
        for x in 0..1000_u64 {
            v.push(x);
        }
        v
    });
    let mut reused = Vec::with_capacity(1000);
    show("clear and refill", || {
        reused.clear();
        reused.extend(0..1000_u64);
        reused.len()
    });
    let shared = Arc::new(1_u64);
    show("Arc::clone", || Arc::clone(&shared));
}
