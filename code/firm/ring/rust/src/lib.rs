//! firm.ring -- Rust twin of `cpp/firm_ring.hpp` (One Quant Book 13, chapter 12): the same SPSC byte layout (a C++
//! process and a Rust process can share one ring), and a sequence lock for last-value data.
//!
//! Layout: header line (magic u64 "FIRMRING", version u32, slot_size u32, capacity u64), write sequence at 64, read
//! sequence at 128, slots from 192; a slot is u32 length then payload. Little-endian.

use std::sync::atomic::{fence, AtomicU64, Ordering};

pub const MAGIC: u64 = u64::from_le_bytes(*b"FIRMRING");
pub const VERSION: u32 = 1;
pub const HEADER: usize = 192;

pub fn region_size(capacity: usize, slot_size: usize) -> usize {
    HEADER + capacity * slot_size
}

/// A region of memory owned by the process (shared memory would map the same layout). It is stored as atomic words:
/// they are 8-byte aligned, and, since an atomic has interior mutability, a producer may write a slot's bytes through
/// a shared reference while the release/acquire pair on the sequences orders those writes against the reader's.
pub struct Region {
    words: Box<[AtomicU64]>,
}

impl Region {
    pub fn new(bytes: usize) -> Region {
        Region { words: (0..bytes.div_ceil(8)).map(|_| AtomicU64::new(0)).collect() }
    }
    pub fn from_bytes(b: &[u8]) -> Region {
        let mut r = Region::new(b.len());
        r.bytes_mut()[..b.len()].copy_from_slice(b);
        r
    }
    pub fn bytes(&self) -> &[u8] {
        // SAFETY: the words viewed as bytes, same lifetime and length; callers read them only while no thread writes.
        unsafe { std::slice::from_raw_parts(self.words.as_ptr() as *const u8, self.words.len() * 8) }
    }
    pub fn bytes_mut(&mut self) -> &mut [u8] {
        // SAFETY: as above, uniquely borrowed.
        unsafe { std::slice::from_raw_parts_mut(self.words.as_mut_ptr() as *mut u8, self.words.len() * 8) }
    }
    fn atomic(&self, off: usize) -> &AtomicU64 {
        assert!(off.is_multiple_of(8) && off + 8 <= self.words.len() * 8);
        &self.words[off / 8]
    }
    fn raw(&self) -> *mut u8 {
        // A pointer to the whole slice (so its provenance covers every slot); the storage is interior-mutable.
        self.words.as_ptr().cast::<u8>().cast_mut()
    }
}

pub fn format(r: &mut Region, capacity: usize, slot_size: usize) {
    assert!(capacity.is_power_of_two() && slot_size >= 8 && slot_size.is_multiple_of(8));
    let b = r.bytes_mut();
    b.fill(0);
    b[0..8].copy_from_slice(&MAGIC.to_le_bytes());
    b[8..12].copy_from_slice(&VERSION.to_le_bytes());
    b[12..16].copy_from_slice(&(slot_size as u32).to_le_bytes());
    b[16..24].copy_from_slice(&(capacity as u64).to_le_bytes());
}

/// Single-producer single-consumer ring over a region. One handle per thread (`Spsc` is Send, not Sync).
pub struct Spsc<'a> {
    r: &'a Region,
    cap: u64,
    slot: usize,
    read_cache: u64,
    write_cache: u64,
}

impl<'a> Spsc<'a> {
    pub fn attach(r: &'a Region) -> Spsc<'a> {
        let b = r.bytes();
        assert_eq!(u64::from_le_bytes(b[0..8].try_into().unwrap()), MAGIC, "not a firm ring");
        let slot = u32::from_le_bytes(b[12..16].try_into().unwrap()) as usize;
        let cap = u64::from_le_bytes(b[16..24].try_into().unwrap());
        let (read_cache, write_cache) = (r.atomic(128).load(Ordering::Acquire), r.atomic(64).load(Ordering::Acquire));
        Spsc { r, cap, slot, read_cache, write_cache }
    }

    pub fn try_write(&mut self, msg: &[u8]) -> bool {
        if msg.len() > self.slot - 4 {
            return false;
        }
        let w = self.r.atomic(64).load(Ordering::Relaxed);
        if w - self.read_cache == self.cap {
            self.read_cache = self.r.atomic(128).load(Ordering::Acquire);
            if w - self.read_cache == self.cap {
                return false;
            }
        }
        let at = HEADER + ((w & (self.cap - 1)) as usize) * self.slot;
        // SAFETY: the producer owns slot w until the release store below; the consumer does not read it before.
        unsafe {
            let p = self.r.raw().add(at);
            std::ptr::copy_nonoverlapping((msg.len() as u32).to_le_bytes().as_ptr(), p, 4);
            std::ptr::copy_nonoverlapping(msg.as_ptr(), p.add(4), msg.len());
        }
        self.r.atomic(64).store(w + 1, Ordering::Release);
        true
    }

    /// Length read into `out`, or None when empty.
    pub fn try_read(&mut self, out: &mut [u8]) -> Option<usize> {
        let rd = self.r.atomic(128).load(Ordering::Relaxed);
        if rd == self.write_cache {
            self.write_cache = self.r.atomic(64).load(Ordering::Acquire);
            if rd == self.write_cache {
                return None;
            }
        }
        let at = HEADER + ((rd & (self.cap - 1)) as usize) * self.slot;
        let mut len = [0u8; 4];
        // SAFETY: slot rd was published by the producer's release store, which our acquire load observed.
        unsafe {
            let p = self.r.raw().add(at);
            std::ptr::copy_nonoverlapping(p, len.as_mut_ptr(), 4);
            let n = (u32::from_le_bytes(len) as usize).min(out.len());
            std::ptr::copy_nonoverlapping(p.add(4), out.as_mut_ptr(), n);
            self.r.atomic(128).store(rd + 1, Ordering::Release);
            Some(n)
        }
    }
}

/// Last-value publication of two words (for example the best bid and ask).
#[derive(Default)]
pub struct SeqLock2 {
    seq: AtomicU64,
    w: [AtomicU64; 2],
}

impl SeqLock2 {
    pub fn store(&self, a: u64, b: u64) {
        let s = self.seq.load(Ordering::Relaxed);
        self.seq.store(s + 1, Ordering::Relaxed);
        fence(Ordering::Release);
        self.w[0].store(a, Ordering::Relaxed);
        self.w[1].store(b, Ordering::Relaxed);
        self.seq.store(s + 2, Ordering::Release);
    }
    pub fn load(&self) -> (u64, u64) {
        loop {
            let s1 = self.seq.load(Ordering::Acquire);
            if s1 & 1 == 1 {
                continue;
            }
            let (a, b) = (self.w[0].load(Ordering::Relaxed), self.w[1].load(Ordering::Relaxed));
            fence(Ordering::Acquire);
            if self.seq.load(Ordering::Relaxed) == s1 {
                return (a, b);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicBool;
    use std::sync::Arc;

    #[test]
    fn layout_matches_the_fixture() {
        let fixture = std::fs::read("../data/ring_image.bin").unwrap();
        let mut r = Region::new(region_size(8, 64));
        format(&mut r, 8, 64);
        {
            let mut p = Spsc::attach(&r);
            for k in 0..5 {
                assert!(p.try_write(format!("msg-{k}").as_bytes()));
            }
        }
        let mut c = Spsc::attach(&r);
        let mut buf = [0u8; 64];
        for _ in 0..2 {
            assert_eq!(c.try_read(&mut buf), Some(5));
        }
        assert_eq!(&r.bytes()[..fixture.len()], &fixture[..]);
        let f = Region::from_bytes(&fixture);
        let mut t = Spsc::attach(&f);
        for k in 2..5 {
            assert_eq!(t.try_read(&mut buf), Some(5));
            assert_eq!(&buf[..5], format!("msg-{k}").as_bytes());
        }
        assert_eq!(t.try_read(&mut buf), None);
    }

    #[test]
    fn spsc_in_order_across_threads() {
        let mut r = Region::new(region_size(1024, 64));
        format(&mut r, 1024, 64);
        let r = Arc::new(r);
        let rp = r.clone();
        let h = std::thread::spawn(move || {
            let mut p = Spsc::attach(&rp);
            for i in 0u64..200_000 {
                while !p.try_write(&i.to_le_bytes()) {}
            }
        });
        let mut c = Spsc::attach(&r);
        let mut b = [0u8; 8];
        for i in 0u64..200_000 {
            while c.try_read(&mut b).is_none() {}
            assert_eq!(u64::from_le_bytes(b), i);
        }
        h.join().unwrap();
    }

    #[test]
    fn seqlock_never_torn() {
        let s = Arc::new(SeqLock2::default());
        s.store(0, 1);
        let stop = Arc::new(AtomicBool::new(false));
        let (sw, st) = (s.clone(), stop.clone());
        let w = std::thread::spawn(move || {
            let mut i = 0u64;
            while !st.load(Ordering::Relaxed) {
                sw.store(i, i + 1);
                i += 1;
            }
        });
        for _ in 0..200_000 {
            let (a, b) = s.load();
            assert_eq!(b, a + 1);
        }
        stop.store(true, Ordering::Relaxed);
        w.join().unwrap();
    }
}
