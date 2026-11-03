use std::cell::UnsafeCell;
use std::mem::MaybeUninit;
use std::rc::Rc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;

pub struct Mailbox<T> {
    full: AtomicBool,
    slot: UnsafeCell<MaybeUninit<T>>,
}
unsafe impl<T> Sync for Mailbox<T> {}

impl<T> Mailbox<T> {
    pub fn new() -> Self {
        let slot = UnsafeCell::new(MaybeUninit::uninit());
        Mailbox { full: AtomicBool::new(false), slot }
    }
    pub fn put(&self, v: T) -> bool {
        if self.full.load(Ordering::Acquire) {
            return false;
        }
        unsafe { (*self.slot.get()).write(v) };
        self.full.store(true, Ordering::Release);
        true
    }
    pub fn take(&self) -> Option<T> {
        if !self.full.load(Ordering::Acquire) {
            return None;
        }
        let v = unsafe { (*self.slot.get()).assume_init_read() };
        self.full.store(false, Ordering::Release);
        Some(v)
    }
}

fn main() {
    let shared = Rc::new(5_u64);
    let keep = Rc::clone(&shared);
    let m = Mailbox::new();
    assert!(m.put(shared));
    thread::scope(|s| {
        s.spawn(|| {
            let got = m.take().unwrap();
            for _ in 0..100_000 {
                drop(Rc::clone(&got));
            }
        });
        for _ in 0..100_000 {
            drop(Rc::clone(&keep));
        }
    });
    println!("{}", Rc::strong_count(&keep));
}
