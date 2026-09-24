//! firm.riskengine aggregation kernel (Rust twin of firm_riskengine.py): P&L of every node of the risk
//! hierarchy, historical VaR and ES (k-th largest loss, k = ceil((1 - a) n)), Euler contributions of ES.
use std::collections::BTreeMap;

pub type Matrix = Vec<Vec<f64>>; // pnl[scenario][trade]
pub type Path = Vec<String>;

pub fn nodes(paths: &[Path]) -> Vec<Path> {
    let mut out: Vec<Path> = paths.iter().flat_map(|p| (1..=p.len()).map(move |i| p[..i].to_vec())).collect();
    out.sort_by(|a, b| a.len().cmp(&b.len()).then_with(|| a.cmp(b)));
    out.dedup();
    out
}

pub fn aggregate(pnl: &Matrix, paths: &[Path]) -> BTreeMap<Path, Vec<f64>> {
    nodes(paths)
        .into_iter()
        .map(|n| {
            let cols: Vec<usize> = (0..paths.len()).filter(|&j| paths[j].starts_with(&n)).collect();
            let v = pnl.iter().map(|row| cols.iter().map(|&j| row[j]).sum()).collect();
            (n, v)
        })
        .collect()
}

fn tail_count(n: usize, level: f64) -> usize {
    (((1.0 - level) * n as f64 - 1e-9).ceil() as usize).max(1)
}

/// (VaR, ES) as positive losses at one level.
pub fn var_es(pnl: &[f64], level: f64) -> (f64, f64) {
    let mut loss: Vec<f64> = pnl.iter().map(|x| -x).collect();
    loss.sort_by(|a, b| b.partial_cmp(a).unwrap());
    let k = tail_count(loss.len(), level);
    (loss[k - 1], loss[..k].iter().sum::<f64>() / k as f64)
}

/// Each child's average loss in the parent's k worst scenarios (stable order on ties).
pub fn euler_es(parent: &[f64], children: &BTreeMap<Path, Vec<f64>>, level: f64) -> BTreeMap<Path, f64> {
    let mut idx: Vec<usize> = (0..parent.len()).collect();
    idx.sort_by(|&a, &b| parent[a].partial_cmp(&parent[b]).unwrap());
    let k = tail_count(parent.len(), level);
    children
        .iter()
        .map(|(c, v)| (c.clone(), -idx[..k].iter().map(|&i| v[i]).sum::<f64>() / k as f64))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn p(xs: &[&str]) -> Path {
        xs.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn fixture() {
        let pnl: Matrix = (0..40)
            .map(|i| {
                (0..5)
                    .map(|j| {
                        10.0 * (0.7 * i as f64 + j as f64).sin() + 3.0 * (1.3 * i as f64 * (j + 1) as f64).cos()
                    })
                    .collect()
            })
            .collect();
        let paths = vec![p(&["F", "A", "x"]), p(&["F", "A", "y"]), p(&["F", "B", "x"]), p(&["F", "B", "x"]),
                         p(&["F", "B", "z"])];
        let agg = aggregate(&pnl, &paths);
        assert_eq!(agg.len(), 7);
        let want = [
            (p(&["F"]), 14.86618942343704, 14.291194493251536),
            (p(&["F", "A"]), 17.809578986609523, 17.830288721860203),
            (p(&["F", "B"]), 26.518767856515673, 23.789625576197057),
            (p(&["F", "A", "x"]), 10.903557269026098, 10.322188844817205),
            (p(&["F", "B", "z"]), 11.674073958581577, 10.951052984889861),
        ];
        for (n, v, e) in want.iter() {
            assert!((var_es(&agg[n], 0.95).0 - v).abs() < 1e-9);
            assert!((var_es(&agg[n], 0.90).1 - e).abs() < 1e-9);
        }
        let children: BTreeMap<Path, Vec<f64>> =
            [p(&["F", "A"]), p(&["F", "B"])].into_iter().map(|n| (n.clone(), agg[&n].clone())).collect();
        let e = euler_es(&agg[&p(&["F"])], &children, 0.90);
        assert!((e[&p(&["F", "A"])] - 1.114894308826234).abs() < 1e-9);
        assert!((e[&p(&["F", "B"])] - 13.176300184425303).abs() < 1e-9);
    }
}
