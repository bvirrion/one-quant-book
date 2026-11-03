use std::ops::Deref;
use std::ptr::NonNull;
use std::sync::atomic::{AtomicUsize, Ordering::Relaxed};

struct Inner<T> {
    count: AtomicUsize,
    value: T,
}
pub struct MyArc<T>(NonNull<Inner<T>>);
unsafe impl<T: Send + Sync> Send for MyArc<T> {}
unsafe impl<T: Send + Sync> Sync for MyArc<T> {}

impl<T> MyArc<T> {
    pub fn new(value: T) -> Self {
        let inner = Box::new(Inner { count: AtomicUsize::new(1), value });
        MyArc(NonNull::from(Box::leak(inner)))
    }
}
impl<T> Deref for MyArc<T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &self.0.as_ref().value }
    }
}
impl<T> Clone for MyArc<T> {
    fn clone(&self) -> Self {
        unsafe { self.0.as_ref() }.count.fetch_add(1, Relaxed);
        MyArc(self.0)
    }
}
impl<T> Drop for MyArc<T> {
    fn drop(&mut self) {
        if unsafe { self.0.as_ref() }.count.fetch_sub(1, Relaxed) == 1 {
            drop(unsafe { Box::from_raw(self.0.as_ptr()) });
        }
    }
}
