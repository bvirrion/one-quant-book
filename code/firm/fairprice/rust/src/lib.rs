//! firm.fairprice -- the fair-price filter (One Quant Book 11, chapter 2), Rust twin of firm_fairprice.FairFilter.
//! Same operation order as the Python reference; checked on data/fixture_*.csv.

pub struct FairFilter {
    q: f64,
    r: Vec<f64>,
    x: f64,
    p: f64,
    t: Option<f64>,
}

impl FairFilter {
    pub fn new(q: f64, r: Vec<f64>) -> Self {
        FairFilter { q, r, x: f64::NAN, p: 1e6, t: None }
    }

    /// Propagate the variance to time t, then update with observation y from source src; returns the estimate.
    pub fn update(&mut self, t: f64, src: usize, y: f64) -> f64 {
        match self.t {
            None => {
                self.t = Some(t);
                self.x = y;
                self.p = self.r[src];
            }
            Some(t0) => {
                self.p += self.q * (t - t0);
                self.t = Some(t);
                let k = self.p / (self.p + self.r[src]);
                self.x += k * (y - self.x);
                self.p *= 1.0 - k;
            }
        }
        self.x
    }

    pub fn estimate(&self) -> f64 {
        self.x
    }

    pub fn variance(&self) -> f64 {
        self.p
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn read(name: &str) -> Vec<Vec<f64>> {
        let path = format!("{}/../data/{}", env!("CARGO_MANIFEST_DIR"), name);
        fs::read_to_string(path)
            .unwrap()
            .lines()
            .skip(1)
            .map(|l| l.split(',').map(|c| c.parse().unwrap()).collect())
            .collect()
    }

    #[test]
    fn replays_the_fixture_like_python() {
        let par = read("fixture_params.csv");
        let ev = read("fixture_events.csv");
        let exp = read("fixture_expected.csv");
        assert!(ev.len() == exp.len() && ev.len() > 1000);
        let mut f = FairFilter::new(par[0][0], vec![par[0][1], par[0][2], par[0][3]]);
        for (e, x) in ev.iter().zip(exp.iter()) {
            let est = f.update(e[0], e[1] as usize, e[2]);
            assert!((est - x[0]).abs() < 1e-9 && (f.variance() - x[1]).abs() < 1e-12);
        }
    }

    #[test]
    fn a_noisier_source_moves_the_estimate_less() {
        let mut a = FairFilter::new(0.1, vec![0.1, 10.0]);
        let mut b = FairFilter::new(0.1, vec![0.1, 10.0]);
        a.update(0.0, 0, 100.0);
        b.update(0.0, 0, 100.0);
        assert!(a.update(1.0, 0, 101.0) - 100.0 > b.update(1.0, 1, 101.0) - 100.0);
    }
}
