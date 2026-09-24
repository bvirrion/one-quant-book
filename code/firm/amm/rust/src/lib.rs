//! firm.amm -- constant-product and stableswap swaps in integer arithmetic (build of Chapter 20, One
//! Quant Book 3), Rust twin of the corresponding parts of firm_amm.py. u128 throughout: balances must
//! stay below about 10^16 base units (six-decimal tokens up to ten billion) so that products fit.

/// Output of a constant-product swap, fee on the input, floor division.
pub fn cp_amount_out(amount_in: u128, reserve_in: u128, reserve_out: u128, fee_bps: u128) -> u128 {
    let a = amount_in * (10_000 - fee_bps);
    a * reserve_out / (reserve_in * 10_000 + a)
}

/// Stableswap invariant D for balances xp and amplification A (Newton, integer).
pub fn ss_get_d(xp: &[u128], amp: u128) -> Option<u128> {
    let n = xp.len() as u128;
    let s: u128 = xp.iter().sum();
    if s == 0 {
        return Some(0);
    }
    let (mut d, ann) = (s, amp * n);
    for _ in 0..255 {
        let mut d_p = d;
        for &x in xp {
            d_p = d_p * d / (x * n);
        }
        let d_prev = d;
        d = (ann * s + d_p * n) * d / ((ann - 1) * d + (n + 1) * d_p);
        if d.abs_diff(d_prev) <= 1 {
            return Some(d);
        }
    }
    None
}

/// New balance of coin j when coin i's balance is set to x, keeping D.
pub fn ss_get_y(i: usize, j: usize, x: u128, xp: &[u128], amp: u128) -> Option<u128> {
    let n = xp.len() as u128;
    let d = ss_get_d(xp, amp)?;
    let ann = amp * n;
    let (mut c, mut s) = (d, 0u128);
    for (k, &bal) in xp.iter().enumerate() {
        if k == j {
            continue;
        }
        let xk = if k == i { x } else { bal };
        s += xk;
        c = c * d / (xk * n);
    }
    c = c * d / (ann * n);
    let b = s + d / ann;
    let mut y = d;
    for _ in 0..255 {
        let y_prev = y;
        y = (y * y + c) / (2 * y + b - d);
        if y.abs_diff(y_prev) <= 1 {
            return Some(y);
        }
    }
    None
}

/// Stableswap output of coin j for dx of coin i, fee on the output.
pub fn ss_amount_out(i: usize, j: usize, dx: u128, xp: &[u128], amp: u128, fee_bps: u128) -> Option<u128> {
    let dy = xp[j] - ss_get_y(i, j, xp[i] + dx, xp, amp)? - 1;
    Some(dy - dy * fee_bps / 10_000)
}

#[cfg(test)]
mod tests {
    use super::*;
    const E6: u128 = 1_000_000;

    #[test]
    fn constant_product_matches_formula_and_grows_k() {
        let out = cp_amount_out(10 * E6, 1_000 * E6, 3_000_000 * E6, 30);
        assert_eq!(out, 10 * E6 * 9_970 * 3_000_000 * E6 / (1_000 * E6 * 10_000 + 10 * E6 * 9_970));
        assert!((1_010 * E6) * (3_000_000 * E6 - out) > 1_000 * E6 * 3_000_000 * E6);
    }

    #[test]
    fn stableswap_balanced_and_low_slippage() {
        let xp = [1_000_000 * E6, 1_000_000 * E6];
        assert_eq!(ss_get_d(&xp, 100), Some(2_000_000 * E6));
        let y = ss_get_y(0, 1, xp[0] + 1_000 * E6, &xp, 100).unwrap();
        assert!(xp[1] - y < 1_000 * E6 && xp[1] - y > 999 * E6);
        let cp = cp_amount_out(100_000 * E6, xp[0], xp[1], 0);
        assert!(ss_amount_out(0, 1, 100_000 * E6, &xp, 100, 0).unwrap() > cp);
    }

    #[test]
    fn same_numbers_as_python() {
        // firm_amm.py gives 90_069_485_445 for this swap (see tests/test_firm_amm.py::test_twin_numbers)
        let xp = [1_000_000 * E6, 1_200_000 * E6];
        assert_eq!(ss_amount_out(0, 1, 90_000 * E6, &xp, 85, 4), Some(90_069_485_445));
    }
}
