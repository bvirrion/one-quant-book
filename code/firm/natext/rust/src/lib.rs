//! natext_rs -- the chapter 9 kernels in Rust behind a C ABI, loaded from Python with ctypes (One Quant Book 15, ch. 9).
//! No external crates: the functions are `extern "C"` with `#[no_mangle]`, compiled as a cdylib; the caller passes
//! pointers into numpy arrays it owns, so nothing is copied and nothing crosses ownership.

/// y_0 = x_0; y_t = (1 - alpha) y_{t-1} + alpha x_t over a slice.
pub fn ewma(x: &[f64], alpha: f64, out: &mut [f64]) {
    let mut y = match x.first() {
        Some(v) => *v,
        None => return,
    };
    for (o, v) in out.iter_mut().zip(x) {
        y = (1.0 - alpha) * y + alpha * v;
        *o = y;
    }
    out[0] = x[0];
}

/// For each left time, the index of the last right time at or before it (-1 if none); both slices sorted.
pub fn asof_index(left: &[i64], right: &[i64], out: &mut [i64]) {
    let mut j = 0usize;
    for (o, l) in out.iter_mut().zip(left) {
        while j < right.len() && right[j] <= *l {
            j += 1;
        }
        *o = j as i64 - 1;
    }
}

/// # Safety
/// `x` must point to `n` readable f64 values and `out` to `n` writable f64 values
/// that do not overlap `x`.
#[no_mangle]
pub unsafe extern "C" fn natext_ewma(x: *const f64, n: usize, alpha: f64, out: *mut f64) {
    if n == 0 {
        return;
    }
    let x = std::slice::from_raw_parts(x, n);
    let out = std::slice::from_raw_parts_mut(out, n);
    ewma(x, alpha, out);
}

/// # Safety
/// `left` must point to `nl` and `right` to `nr` readable i64 values, both sorted, and `out` to `nl` writable i64 values.
#[no_mangle]
pub unsafe extern "C" fn natext_asof(left: *const i64, nl: usize, right: *const i64, nr: usize, out: *mut i64) {
    let l = if nl == 0 { &[][..] } else { std::slice::from_raw_parts(left, nl) };
    let r = if nr == 0 { &[][..] } else { std::slice::from_raw_parts(right, nr) };
    let o = if nl == 0 { &mut [][..] } else { std::slice::from_raw_parts_mut(out, nl) };
    asof_index(l, r, o);
}

/// One step of the average, for the per-call benchmark.
#[no_mangle]
pub extern "C" fn natext_ewma_step(y: f64, x: f64, alpha: f64) -> f64 {
    (1.0 - alpha) * y + alpha * x
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ewma_by_hand() {
        let mut y = [0.0; 4];
        ewma(&[10.0, 20.0, 20.0, 0.0], 0.5, &mut y);
        assert_eq!(y, [10.0, 15.0, 17.5, 8.75]);
        assert_eq!(natext_ewma_step(15.0, 20.0, 0.5), 17.5);
    }

    #[test]
    fn asof_by_hand_and_through_the_c_abi() {
        let (l, r) = ([0i64, 5, 10, 11, 30], [5i64, 10, 20]);
        let mut o = [0i64; 5];
        unsafe { natext_asof(l.as_ptr(), 5, r.as_ptr(), 3, o.as_mut_ptr()) };
        assert_eq!(o, [-1, 0, 1, 1, 2]);
    }
}
