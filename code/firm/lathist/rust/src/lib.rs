//! firm.lathist -- log-linear latency histogram, Rust twin of `firm_lathist.py` and `cpp/firm_lathist.hpp`
//! (One Quant Book 13, chapter 5). Same layout, same fixture, same quantiles.

pub fn index_of(v: u64, sub_bits: u32) -> usize {
    if v < (1u64 << sub_bits) {
        return v as usize;
    }
    let shift = (64 - v.leading_zeros()) - sub_bits;
    let half = 1u64 << (sub_bits - 1);
    let mant = v >> shift;
    ((1u64 << sub_bits) + u64::from(shift - 1) * half + (mant - half)) as usize
}

pub fn bucket_high(i: usize, sub_bits: u32) -> u64 {
    let full = 1u64 << sub_bits;
    let half = full >> 1;
    let i = i as u64;
    if i < full {
        return i;
    }
    let shift = (i - full) / half + 1;
    let mant = (i - full) % half + half;
    ((mant + 1) << shift) - 1
}

pub struct LatHist {
    sub_bits: u32,
    counts: Vec<u64>,
    count: u64,
    min: u64,
    max: u64,
    total: f64,
}

impl LatHist {
    pub fn new(sub_bits: u32) -> LatHist {
        LatHist {
            sub_bits,
            counts: vec![0; index_of(u64::MAX, sub_bits) + 1],
            count: 0,
            min: u64::MAX,
            max: 0,
            total: 0.0,
        }
    }
    pub fn record(&mut self, v: u64) {
        self.counts[index_of(v, self.sub_bits)] += 1;
        self.count += 1;
        self.total += v as f64;
        self.min = self.min.min(v);
        self.max = self.max.max(v);
    }
    /// Tene's correction for coordinated omission.
    pub fn record_corrected(&mut self, v: u64, interval: u64) {
        self.record(v);
        if interval == 0 {
            return;
        }
        let mut missing = v.saturating_sub(interval);
        while missing > interval {
            self.record(missing);
            missing -= interval;
        }
    }
    pub fn quantile(&self, p: f64) -> u64 {
        if self.count == 0 {
            return 0;
        }
        let rank = ((p * self.count as f64) as u64 + 1).min(self.count);
        let mut seen = 0u64;
        for (i, &c) in self.counts.iter().enumerate() {
            seen += c;
            if seen >= rank {
                return bucket_high(i, self.sub_bits).min(self.max);
            }
        }
        self.max
    }
    pub fn count(&self) -> u64 {
        self.count
    }
    pub fn counts(&self) -> &[u64] {
        &self.counts
    }
    pub fn mean(&self) -> f64 {
        if self.count == 0 {
            0.0
        } else {
            self.total / self.count as f64
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn rows(name: &str) -> Vec<Vec<String>> {
        let text = fs::read_to_string(format!("../data/{name}")).expect("fixture");
        text.lines()
            .skip(1)
            .map(|l| l.split(',').map(str::to_string).collect())
            .collect()
    }

    #[test]
    fn reproduces_the_fixture() {
        let mut h = LatHist::new(8);
        for r in rows("fixture_values.csv") {
            h.record(r[0].parse().unwrap());
        }
        let want = rows("fixture_buckets.csv");
        assert_eq!(h.counts().iter().filter(|&&c| c != 0).count(), want.len());
        for r in want {
            assert_eq!(
                h.counts()[r[0].parse::<usize>().unwrap()],
                r[1].parse::<u64>().unwrap()
            );
        }
        for r in rows("fixture_quantiles.csv") {
            assert_eq!(
                h.quantile(r[0].parse().unwrap()),
                r[1].parse::<u64>().unwrap()
            );
        }
    }

    #[test]
    fn corrects_coordinated_omission() {
        let mut h = LatHist::new(8);
        h.record_corrected(10_000, 1_000);
        assert_eq!(h.count(), 9);
    }
}
