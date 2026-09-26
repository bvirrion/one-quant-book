//! firm.pipeline -- Rust twin of `cpp/firm_pipeline.hpp` (One Quant Book 13, chapter 7). Stages implement `Stage<E>`;
//! `Chain<A, B>` composes two stages into one at compile time (monomorphised, inlinable); `DynPipeline` holds
//! `Box<dyn Stage<E>>`, one indirect call per stage.

pub trait Stage<E> {
    /// Process the event; `false` stops it.
    fn on(&mut self, e: &mut E) -> bool;
}

pub struct Chain<A, B>(pub A, pub B);

impl<E, A: Stage<E>, B: Stage<E>> Stage<E> for Chain<A, B> {
    #[inline]
    fn on(&mut self, e: &mut E) -> bool {
        self.0.on(e) && self.1.on(e)
    }
}

/// `chain!(a, b, c)` is `Chain(a, Chain(b, c))`.
#[macro_export]
macro_rules! chain {
    ($a:expr) => { $a };
    ($a:expr, $($rest:expr),+) => { $crate::Chain($a, $crate::chain!($($rest),+)) };
}

pub struct DynPipeline<E> {
    stages: Vec<Box<dyn Stage<E>>>,
}

impl<E> Default for DynPipeline<E> {
    fn default() -> Self {
        DynPipeline { stages: Vec::new() }
    }
}

impl<E> DynPipeline<E> {
    pub fn add(&mut self, s: Box<dyn Stage<E>>) {
        self.stages.push(s);
    }
    pub fn on(&mut self, e: &mut E) -> bool {
        self.stages.iter_mut().all(|s| s.on(e))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Default)]
    struct Ev {
        x: i32,
        trace: i32,
    }
    struct Add(i32);
    struct Mul(i32);
    struct Gate(i32);
    impl Stage<Ev> for Add {
        fn on(&mut self, e: &mut Ev) -> bool {
            e.x += self.0;
            e.trace = e.trace * 10 + 1;
            true
        }
    }
    impl Stage<Ev> for Mul {
        fn on(&mut self, e: &mut Ev) -> bool {
            e.x *= self.0;
            e.trace = e.trace * 10 + 2;
            true
        }
    }
    impl Stage<Ev> for Gate {
        fn on(&mut self, e: &mut Ev) -> bool {
            e.trace = e.trace * 10 + 3;
            e.x <= self.0
        }
    }

    #[test]
    fn static_and_dynamic_agree() {
        let mut p = chain!(Add(1), Mul(3), Gate(10), Add(100));
        let mut d = DynPipeline::default();
        d.add(Box::new(Add(1)));
        d.add(Box::new(Mul(3)));
        d.add(Box::new(Gate(10)));
        d.add(Box::new(Add(100)));
        for x in 0..6 {
            let (mut a, mut b) = (Ev { x, ..Ev::default() }, Ev { x, ..Ev::default() });
            let (ra, rb) = (p.on(&mut a), d.on(&mut b));
            assert_eq!((ra, a.x, a.trace), (rb, b.x, b.trace));
            let pass = (x + 1) * 3 <= 10;
            assert_eq!((ra, a.trace), (pass, if pass { 1231 } else { 123 }));
        }
    }
}
