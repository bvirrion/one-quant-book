//! firm.nicring -- a network card's receive descriptor ring, Rust twin of `firm_nicring.py` and
//! `cpp/firm_nicring.hpp` (One Quant Book 14, chapter 3). Same rules, same fixture, same counters and hashes.

pub struct Ring {
    size: u32,
    refill: u32,
    head: u32,
    tail: u32,
    pending: u32,
    owner: Vec<u8>,
    seq: Vec<u64>,
    len: Vec<u32>,
    pub rx: u64,
    pub drops: u64,
    pub processed: u64,
    pub doorbells: u64,
    pub max_owned: u64,
    pub hash: u64,
}

impl Ring {
    pub fn new(size: u32, refill: u32) -> Ring {
        assert!(size.is_power_of_two() && (1..=size).contains(&refill), "ring size or refill");
        let n = size as usize;
        Ring {
            size,
            refill,
            head: 0,
            tail: 0,
            pending: 0,
            owner: vec![0; n],
            seq: vec![0; n],
            len: vec![0; n],
            rx: 0,
            drops: 0,
            processed: 0,
            doorbells: 0,
            max_owned: 0,
            hash: 0xCBF2_9CE4_8422_2325,
        }
    }

    /// The card receives a packet; false if the next descriptor is still the host's (dropped).
    pub fn nic_rx(&mut self, seq: u64, length: u32) -> bool {
        let i = self.head as usize;
        if self.owner[i] == 1 {
            self.drops += 1;
            return false;
        }
        self.seq[i] = seq;
        self.len[i] = length;
        self.owner[i] = 1;
        self.head = (self.head + 1) & (self.size - 1);
        self.rx += 1;
        true
    }

    /// The host processes up to `budget` descriptors, handing them back in batches of `refill`.
    pub fn poll(&mut self, budget: u32) -> u32 {
        let mut n = 0;
        while n < budget && self.rx > self.processed {
            let i = self.tail as usize;
            self.mix(self.seq[i]);
            self.mix(u64::from(self.len[i]));
            self.tail = (self.tail + 1) & (self.size - 1);
            self.processed += 1;
            self.pending += 1;
            n += 1;
            if self.pending >= self.refill {
                self.give_back();
            }
        }
        n
    }

    pub fn note_owned(&mut self) {
        let held = self.rx - self.processed + u64::from(self.pending);
        self.max_owned = self.max_owned.max(held);
    }

    fn mix(&mut self, mut x: u64) {
        for _ in 0..8 {
            self.hash = (self.hash ^ (x & 0xFF)).wrapping_mul(0x0100_0000_01B3);
            x >>= 8;
        }
    }

    fn give_back(&mut self) {
        let start = self.tail.wrapping_sub(self.pending) & (self.size - 1);
        for k in 0..self.pending {
            self.owner[((start + k) & (self.size - 1)) as usize] = 0;
        }
        self.pending = 0;
        self.doorbells += 1;
    }
}

#[cfg(test)]
mod tests {
    use super::Ring;
    use std::fs;

    #[test]
    fn reproduces_the_fixture() {
        let events = fs::read_to_string("../data/events.txt").expect("events");
        let expected = fs::read_to_string("../data/expected.txt").expect("expected");
        let mut n = 0;
        for line in expected.lines().filter(|l| !l.starts_with('#') && !l.is_empty()) {
            let f: Vec<&str> = line.split_whitespace().collect();
            let size: u32 = f[0].parse().unwrap();
            let refill: u32 = f[1].parse().unwrap();
            let mut r = Ring::new(size, refill);
            for e in events.lines() {
                let p: Vec<&str> = e.split_whitespace().collect();
                if p[0] == "N" {
                    r.nic_rx(p[1].parse().unwrap(), p[2].parse().unwrap());
                } else {
                    r.poll(p[1].parse().unwrap());
                }
                r.note_owned();
            }
            let got = [r.rx, r.drops, r.processed, r.doorbells, r.max_owned];
            let want: Vec<u64> = f[2..7].iter().map(|x| x.parse().unwrap()).collect();
            assert_eq!(got.to_vec(), want, "size {size} refill {refill}");
            assert_eq!(format!("{:016x}", r.hash), f[7]);
            n += 1;
        }
        assert_eq!(n, 4);
    }

    #[test]
    fn a_full_ring_drops() {
        let mut r = Ring::new(4, 4);
        for s in 0..6 {
            r.nic_rx(s, 64);
        }
        assert_eq!((r.rx, r.drops), (4, 2));
        assert_eq!(r.poll(3), 3);
        assert!(!r.nic_rx(6, 64)); // processed but not yet handed back
        assert_eq!(r.poll(1), 1);
        assert!(r.nic_rx(6, 64)); // a batch of four handed back
    }
}
