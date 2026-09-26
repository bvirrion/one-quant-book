//! firm.mlinfer -- Rust inference kernels for a flat forest and an int8 multilayer perceptron (Book 12, chapter 26).
//! Loading allocates; `predict` does not (fixed-size stack buffers). Bit-for-bit parity with firm_mlinfer.py on
//! data/vectors.csv.

pub struct Forest {
    pub roots: Vec<i32>,
    pub feature: Vec<i32>,
    pub left: Vec<i32>,
    pub right: Vec<i32>,
    pub threshold: Vec<f64>,
    pub value: Vec<f64>,
}

impl Forest {
    pub fn predict(&self, x: &[f64]) -> f64 {
        let mut s = 0.0;
        for &root in &self.roots {
            let mut n = root;
            while n >= 0 {
                let i = n as usize;
                n = if x[self.feature[i] as usize] <= self.threshold[i] { self.left[i] } else { self.right[i] };
            }
            s += self.value[(-n - 1) as usize];
        }
        s
    }

    pub fn parse(text: &str) -> Forest {
        let mut f = Forest { roots: vec![], feature: vec![], left: vec![], right: vec![], threshold: vec![], value: vec![] };
        for line in text.lines() {
            let mut it = line.split_whitespace();
            match it.next() {
                Some("roots") => f.roots = it.map(|v| v.parse().unwrap()).collect(),
                Some("feature") => f.feature = it.map(|v| v.parse().unwrap()).collect(),
                Some("left") => f.left = it.map(|v| v.parse().unwrap()).collect(),
                Some("right") => f.right = it.map(|v| v.parse().unwrap()).collect(),
                Some("threshold") => f.threshold = it.map(|v| v.parse().unwrap()).collect(),
                Some("value") => f.value = it.map(|v| v.parse().unwrap()).collect(),
                _ => {}
            }
        }
        f
    }
}

pub struct Layer {
    pub out: usize,
    pub inp: usize,
    pub mult: i64,
    pub shift: u32,
    pub prod: f64,
    pub w: Vec<i32>,
    pub b: Vec<i32>,
}

pub struct Mlp {
    pub s_in: f64,
    pub layers: Vec<Layer>,
}

const MAX_WIDTH: usize = 64;

/// round(acc * mult / 2^shift), halves away from zero, clamped to int8.
pub fn requant(acc: i64, mult: i64, shift: u32) -> i64 {
    let p = acc * mult;
    let r = (p.abs() + (1i64 << (shift - 1))) >> shift;
    (if p < 0 { -r } else { r }).clamp(-127, 127)
}

impl Mlp {
    pub fn predict(&self, x: &[f64]) -> f64 {
        let mut a = [0i64; MAX_WIDTH];
        let mut b = [0i64; MAX_WIDTH];
        for (i, ai) in a.iter_mut().enumerate().take(self.layers[0].inp) {
            *ai = ((x[i] / self.s_in).round_ties_even() as i64).clamp(-127, 127);
        }
        for (l, lay) in self.layers.iter().enumerate() {
            for (o, bo) in b.iter_mut().enumerate().take(lay.out) {
                let row = &lay.w[o * lay.inp..(o + 1) * lay.inp];
                let mut acc = lay.b[o] as i64;
                for (w, v) in row.iter().zip(a.iter()) {
                    acc += *w as i64 * *v;
                }
                if l + 1 == self.layers.len() {
                    return acc as f64 * lay.prod;
                }
                *bo = requant(acc, lay.mult, lay.shift).max(0);
            }
            a = b;
        }
        0.0
    }

    pub fn parse(text: &str) -> Mlp {
        let mut m = Mlp { s_in: 1.0, layers: vec![] };
        for line in text.lines() {
            let mut it = line.split_whitespace();
            match it.next() {
                Some("s_in") => m.s_in = it.next().unwrap().parse().unwrap(),
                Some("layer") => {
                    let v: Vec<&str> = it.collect();
                    m.layers.push(Layer {
                        out: v[0].parse().unwrap(),
                        inp: v[1].parse().unwrap(),
                        mult: v[2].parse().unwrap(),
                        shift: v[3].parse().unwrap(),
                        prod: v[4].parse().unwrap(),
                        w: vec![],
                        b: vec![],
                    });
                }
                Some("W") => m.layers.last_mut().unwrap().w = it.map(|v| v.parse().unwrap()).collect(),
                Some("B") => m.layers.last_mut().unwrap().b = it.map(|v| v.parse().unwrap()).collect(),
                _ => {}
            }
        }
        m
    }
}

pub const FOREST: &str = include_str!("../../data/forest.txt");
pub const MLP: &str = include_str!("../../data/mlp.txt");
pub const VECTORS: &str = include_str!("../../data/vectors.csv");

pub fn vectors() -> Vec<Vec<f64>> {
    VECTORS.lines().map(|l| l.split(',').map(|v| v.parse().unwrap()).collect()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parity_with_python() {
        let f = Forest::parse(FOREST);
        let m = Mlp::parse(MLP);
        let rows = vectors();
        assert_eq!(rows.len(), 200);
        for r in &rows {
            assert_eq!(f.predict(&r[..16]), r[16]);
            assert_eq!(m.predict(&r[..16]), r[17]);
        }
    }

    #[test]
    fn requant_rounds_half_away_from_zero() {
        assert_eq!(requant(3, 1, 1), 2);
        assert_eq!(requant(-3, 1, 1), -2);
        assert_eq!(requant(1000, 1 << 20, 10), 127);
    }
}
