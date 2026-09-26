//! firm.memkit -- Rust twin of `cpp/firm_memkit.hpp` (One Quant Book 13, chapter 3): a value alone on its cache
//! line, and the pointer-chase probe over a byte buffer (indices instead of raw addresses, so the ring is safe Rust).

pub const LINE: usize = 64;

/// A value alone on its 64-byte cache line.
#[repr(C, align(64))]
#[derive(Default, Debug)]
pub struct CachePadded<T> {
    pub value: T,
}

/// `n` slots of `stride` bytes laid out as one cycle: slot i stores the index of the next slot.
pub fn chase_ring(n: usize, stride: usize, random: bool, seed: u64) -> Vec<u8> {
    assert!(stride >= 8);
    let mut order: Vec<usize> = (0..n).collect();
    if random {
        let mut s = seed;
        for i in (1..n).rev() {
            s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407); // LCG step
            order.swap(i, (s >> 33) as usize % (i + 1));
        }
    }
    let mut buf = vec![0u8; n * stride];
    for i in 0..n {
        let next = order[(i + 1) % n] as u64;
        buf[order[i] * stride..order[i] * stride + 8].copy_from_slice(&next.to_le_bytes());
    }
    buf
}

/// Follow the ring for `steps` dependent loads from slot 0; returns the slot reached.
pub fn chase(buf: &[u8], stride: usize, steps: usize) -> usize {
    let mut i = 0usize;
    for _ in 0..steps {
        let o = i * stride;
        i = u64::from_le_bytes(buf[o..o + 8].try_into().expect("8 bytes")) as usize;
    }
    i
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicU64;

    #[test]
    fn padded_layout() {
        assert_eq!(std::mem::size_of::<CachePadded<AtomicU64>>(), LINE);
        assert_eq!(std::mem::align_of::<CachePadded<u8>>(), LINE);
        let two: [CachePadded<u64>; 2] = Default::default();
        let d = &two[1].value as *const u64 as usize - &two[0].value as *const u64 as usize;
        assert_eq!(d, LINE);
    }

    #[test]
    fn ring_is_one_cycle() {
        for random in [false, true] {
            let buf = chase_ring(1000, 64, random, 7);
            for k in 1..=1000 {
                assert_eq!(chase(&buf, 64, k) == 0, k == 1000);
            }
        }
    }
}
