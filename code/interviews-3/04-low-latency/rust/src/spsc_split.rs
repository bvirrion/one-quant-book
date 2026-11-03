use std::cell::UnsafeCell;
use std::marker::PhantomData;
use std::mem::MaybeUninit;
use std::ops::Deref;
use std::sync::atomic::{AtomicUsize, Ordering::{Acquire, Relaxed, Release}};
use std::sync::Arc;

struct Shared<T> {
    head: AtomicUsize,
    tail: AtomicUsize,
    slots: Box<[UnsafeCell<MaybeUninit<T>>]>,
}
// Each slot is touched by one side at a time, and T itself moves between threads.
unsafe impl<T: Send> Sync for Shared<T> {}

pub struct Producer<T>(Arc<Shared<T>>);
pub struct Consumer<T>(Arc<Shared<T>>);
pub struct Peek<'a, T>(&'a mut Consumer<T>, PhantomData<&'a T>);

pub fn channel<T>(capacity: usize) -> (Producer<T>, Consumer<T>) {
    assert!(capacity.is_power_of_two());
    let slots = (0..capacity)
        .map(|_| UnsafeCell::new(MaybeUninit::uninit()))
        .collect();
    let (head, tail) = (AtomicUsize::new(0), AtomicUsize::new(0));
    let s = Arc::new(Shared { head, tail, slots });
    (Producer(Arc::clone(&s)), Consumer(s))
}

impl<T> Producer<T> {
    pub fn push(&mut self, v: T) -> Result<(), T> {
        let s = &self.0;
        let t = s.tail.load(Relaxed);
        if t.wrapping_sub(s.head.load(Acquire)) == s.slots.len() {
            return Err(v);
        }
        unsafe { (*s.slots[t & (s.slots.len() - 1)].get()).write(v) };
        s.tail.store(t.wrapping_add(1), Release);
        Ok(())
    }
}
impl<T> Consumer<T> {
    pub fn pop(&mut self) -> Option<T> {
        let s = &self.0;
        let h = s.head.load(Relaxed);
        if h == s.tail.load(Acquire) {
            return None;
        }
        let v = unsafe { (*s.slots[h & (s.slots.len() - 1)].get()).assume_init_read() };
        s.head.store(h.wrapping_add(1), Release);
        Some(v)
    }
    pub fn peek(&mut self) -> Option<Peek<'_, T>> {
        let s = &self.0;
        if s.head.load(Relaxed) == s.tail.load(Acquire) {
            return None;
        }
        Some(Peek(self, PhantomData))
    }
}
impl<T> Deref for Peek<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        let s = &self.0 .0;
        let h = s.head.load(Relaxed);
        unsafe { (*s.slots[h & (s.slots.len() - 1)].get()).assume_init_ref() }
    }
}
impl<T> Drop for Peek<'_, T> {
    fn drop(&mut self) {
        drop(self.0.pop()); // the value leaves the ring only when the borrow ends
    }
}
impl<T> Drop for Shared<T> {
    fn drop(&mut self) {
        let (mut h, t) = (*self.head.get_mut(), *self.tail.get_mut());
        while h != t {
            unsafe { self.slots[h & (self.slots.len() - 1)].get_mut().assume_init_drop() };
            h = h.wrapping_add(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicUsize;

    #[test]
    fn keeps_order_across_threads() {
        let (mut p, mut c) = channel::<u64>(8);
        let n = 100_000;
        let producer = std::thread::spawn(move || {
            for i in 0..n {
                while p.push(i).is_err() {}
            }
        });
        let mut expect = 0;
        while expect < n {
            if let Some(v) = c.pop() {
                assert_eq!(v, expect);
                expect += 1;
            }
        }
        producer.join().unwrap();
    }

    #[test]
    fn full_and_empty_are_reported() {
        let (mut p, mut c) = channel::<u32>(2);
        assert_eq!(c.pop(), None);
        assert!(p.push(1).is_ok() && p.push(2).is_ok());
        assert_eq!(p.push(3), Err(3));
        assert_eq!(c.pop(), Some(1));
    }

    #[test]
    fn peek_consumes_when_the_borrow_ends() {
        let (mut p, mut c) = channel::<String>(4);
        p.push("a".to_string()).unwrap();
        p.push("b".to_string()).unwrap();
        assert_eq!(&**c.peek().unwrap(), "a");
        assert_eq!(c.pop().as_deref(), Some("b"));
    }

    static DROPS: AtomicUsize = AtomicUsize::new(0);
    struct Tracked;
    impl Drop for Tracked {
        fn drop(&mut self) {
            DROPS.fetch_add(1, Relaxed);
        }
    }

    #[test]
    fn unread_items_are_dropped_exactly_once() {
        let (mut p, mut c) = channel::<Tracked>(4);
        for _ in 0..3 {
            assert!(p.push(Tracked).is_ok());
        }
        drop(c.pop());
        assert_eq!(DROPS.load(Relaxed), 1);
        drop(p);
        drop(c);
        assert_eq!(DROPS.load(Relaxed), 3);
    }
}
