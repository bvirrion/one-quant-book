use std::marker::PhantomData;
use std::ops::Deref;
use std::ptr::NonNull;
use std::sync::atomic::{fence, AtomicUsize, Ordering};

struct Inner<T> {
    count: AtomicUsize,
    value: T,
}
pub struct MyArc<T> {
    ptr: NonNull<Inner<T>>,
    owns: PhantomData<Inner<T>>,
}
unsafe impl<T: Send + Sync> Send for MyArc<T> {}
unsafe impl<T: Send + Sync> Sync for MyArc<T> {}

impl<T> MyArc<T> {
    pub fn new(value: T) -> Self {
        let b = Box::new(Inner { count: AtomicUsize::new(1), value });
        MyArc { ptr: NonNull::from(Box::leak(b)), owns: PhantomData }
    }
}
impl<T> Deref for MyArc<T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &self.ptr.as_ref().value }
    }
}
impl<T> Clone for MyArc<T> {
    fn clone(&self) -> Self {
        unsafe { self.ptr.as_ref() }.count.fetch_add(1, Ordering::Relaxed);
        MyArc { ptr: self.ptr, owns: PhantomData }
    }
}
impl<T> Drop for MyArc<T> {
    fn drop(&mut self) {
        if unsafe { self.ptr.as_ref() }.count.fetch_sub(1, Ordering::Release) != 1 {
            return;
        }
        fence(Ordering::Acquire);
        drop(unsafe { Box::from_raw(self.ptr.as_ptr()) });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicUsize;

    static DROPS: AtomicUsize = AtomicUsize::new(0);
    struct Tracked(u64);
    impl Drop for Tracked {
        fn drop(&mut self) {
            DROPS.fetch_add(1, Ordering::Relaxed);
        }
    }

    #[test]
    fn dropped_once_after_all_handles_go() {
        let a = MyArc::new(Tracked(7));
        let handles: Vec<_> = (0..4)
            .map(|_| {
                let h = a.clone();
                std::thread::spawn(move || {
                    let inner = h.clone();
                    assert_eq!(inner.0, 7);
                })
            })
            .collect();
        for h in handles {
            h.join().unwrap();
        }
        assert_eq!(DROPS.load(Ordering::Relaxed), 0);
        drop(a);
        assert_eq!(DROPS.load(Ordering::Relaxed), 1);
    }
}
