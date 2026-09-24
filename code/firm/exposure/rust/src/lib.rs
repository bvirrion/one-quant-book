//! firm.exposure -- aggregation kernel (build of One Quant Book 6, chapter 17), Rust twin of the
//! netting / collateral / profile step of firm_exposure.py. Values are `[trade][path][time]`.

pub type Matrix = Vec<Vec<f64>>;

#[derive(Clone, Copy, Debug)]
pub struct Csa {
    pub threshold: f64,
    pub mta: f64,
    pub lag: usize,
}

#[derive(Debug)]
pub struct Profiles {
    pub ee: Vec<f64>,
    pub ene: Vec<f64>,
    pub pfe: Vec<f64>,
}

pub fn net(trades: &[Matrix]) -> Matrix {
    let mut v = trades[0].clone();
    for t in &trades[1..] {
        for (row, add) in v.iter_mut().zip(t) {
            for (x, a) in row.iter_mut().zip(add) {
                *x += a;
            }
        }
    }
    v
}

pub fn collateral(v: &Matrix, threshold: f64, mta: f64) -> Matrix {
    v.iter()
        .map(|row| {
            let mut c = vec![0.0; row.len()];
            for k in 1..row.len() {
                let x = row[k];
                let target = if x > threshold {
                    x - threshold
                } else if x < -threshold {
                    x + threshold
                } else {
                    0.0
                };
                c[k] = if (target - c[k - 1]).abs() >= mta { target } else { c[k - 1] };
            }
            c
        })
        .collect()
}

pub fn aggregate(trades: &[Matrix], csa: Option<Csa>, ia: f64, q: f64) -> Profiles {
    let v = net(trades);
    let (np, nt) = (v.len(), v[0].len());
    let e: Matrix = match csa {
        None => v.clone(),
        Some(c) => {
            let col = collateral(&v, c.threshold, c.mta);
            v.iter()
                .zip(&col)
                .map(|(row, cr)| (0..nt).map(|k| row[k] - if k >= c.lag { cr[k - c.lag] } else { 0.0 }).collect())
                .collect()
        }
    };
    let mut out = Profiles { ee: vec![0.0; nt], ene: vec![0.0; nt], pfe: vec![0.0; nt] };
    for k in 0..nt {
        let mut pos: Vec<f64> = e.iter().map(|row| (row[k] - ia).max(0.0)).collect();
        out.ee[k] = pos.iter().sum::<f64>() / np as f64;
        out.ene[k] = e.iter().map(|row| row[k].min(0.0)).sum::<f64>() / np as f64;
        pos.sort_by(|a, b| a.partial_cmp(b).unwrap());
        out.pfe[k] = pos[(q * (np - 1) as f64).floor() as usize];
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture() -> Vec<Matrix> {
        let (paths, steps) = (4usize, 12usize);
        let a: Matrix = (0..paths)
            .map(|p| {
                (0..=steps)
                    .map(|k| 10.0 * (0.5 * k as f64 + p as f64).sin() + 0.8 * k as f64 * ((p % 3) as f64 - 1.0))
                    .collect()
            })
            .collect();
        let b: Matrix = (0..paths)
            .map(|p| (0..=steps).map(|k| 4.0 * (0.3 * k as f64 * (p + 1) as f64).cos()).collect())
            .collect();
        vec![a, b]
    }

    fn check(got: &[f64], want: &[f64]) {
        assert_eq!(got.len(), want.len());
        for (g, w) in got.iter().zip(want) {
            assert!((g - w).abs() < 1e-9, "{g} != {w}");
        }
    }

    #[test]
    fn uncollateralised() {
        let r = aggregate(&fixture(), None, 0.0, 0.75);
        check(&r.ee, &[8.7297210492, 7.5907637456, 5.6902123239, 3.7843257003, 1.8356013215, 0.5669175619, 0.0,
            0.6360078225, 1.5098125690, 2.4449258520, 4.3102173514, 5.7459430907, 6.9298835214]);
        check(&r.pfe, &[12.4147098481, 9.2711613141, 10.1160523077, 5.0759130623, 0.0, 0.0, 0.0, 0.0, 0.0,
            1.4026801419, 5.2689983012, 5.9521302487, 9.0032712453]);
    }

    #[test]
    fn threshold_mta_and_lag() {
        let r = aggregate(&fixture(), Some(Csa { threshold: 2.0, mta: 1.0, lag: 1 }), 0.0, 0.75);
        check(&r.ee, &[8.7297210492, 7.5907637456, 1.0751127413, 0.4863343579, 0.3307720073, 0.8061311759,
            0.6054963792, 0.6986256332, 1.5724303798, 2.5579884072, 3.3451194729, 2.9125051166, 3.4386424443]);
        check(&r.ene, &[0.0, -0.7146003147, -4.5050641168, -3.4844349494, -2.6547181597, -2.8014907644,
            -2.5631337253, -3.4440248131, -2.1206767566, -1.4184974824, -0.7394057471, -0.5185809837,
            -1.7316228823]);
    }

    #[test]
    fn independent_amount() {
        let r = aggregate(&fixture(), Some(Csa { threshold: 0.0, mta: 0.0, lag: 2 }), 1.5, 0.75);
        check(&r.ee, &[7.2297210492, 6.4657637456, 4.5652123239, 0.1864470991, 0.0, 1.7619031832, 2.4957711161,
            1.9628207594, 1.8013833311, 3.8703348909, 4.9274378445, 3.4287434730, 4.2039217668]);
        check(&r.pfe, &[10.9147098481, 7.7711613141, 8.6160523077, 0.0, 0.0, 0.0, 4.2045873756, 0.1887673735,
            0.4158118055, 5.4286348775, 7.5378837372, 4.7462118913, 6.2909179008]);
    }
}
