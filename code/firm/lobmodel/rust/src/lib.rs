//! firm.lobmodel -- the Rust serving path of the chapter 29 order-book model (Book 12): firm.mlinfer's flat forest
//! behind one call that takes the ten features in FEATURES order. Bit-for-bit parity with firm_lobmodel.py on
//! data/vectors.csv.

use firm_mlinfer::Forest;

pub const FEATURES: usize = 10;
pub const FOREST: &str = include_str!("../../data/forest.txt");
pub const VECTORS: &str = include_str!("../../data/vectors.csv");

pub struct Model {
    forest: Forest,
}

impl Model {
    pub fn load() -> Model {
        Model { forest: Forest::parse(FOREST) }
    }

    pub fn predict(&self, x: &[f64; FEATURES]) -> f64 {
        self.forest.predict(x)
    }
}

pub fn vectors() -> Vec<([f64; FEATURES], f64)> {
    VECTORS
        .lines()
        .map(|l| {
            let v: Vec<f64> = l.split(',').map(|c| c.parse().unwrap()).collect();
            let mut x = [0.0; FEATURES];
            x.copy_from_slice(&v[..FEATURES]);
            (x, v[FEATURES])
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parity_with_python() {
        let m = Model::load();
        let rows = vectors();
        assert_eq!(rows.len(), 200);
        for (x, want) in &rows {
            assert_eq!(m.predict(x), *want);
        }
    }
}
