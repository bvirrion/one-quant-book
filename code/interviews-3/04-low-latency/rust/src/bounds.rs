#[no_mangle]
pub fn sum_a(v: &[u64]) -> u64 {
    let mut s = 0;
    for i in 0..v.len() { s += v[i]; }
    s
}
#[no_mangle]
pub fn sum_b(v: &[u64], n: usize) -> u64 {
    let mut s = 0;
    for i in 0..n { s += v[i]; }
    s
}
#[no_mangle]
pub fn sum_c(v: &[u64], n: usize) -> u64 {
    let v = &v[..n];
    let mut s = 0;
    for i in 0..n { s += v[i]; }
    s
}
#[no_mangle]
pub fn sum_d(v: &[u64], n: usize) -> u64 {
    assert!(v.len() >= n);
    let mut s = 0;
    for i in 0..n { s += v[i]; }
    s
}
#[no_mangle]
pub fn diff_e(v: &[u64]) -> u64 {
    let mut s = 0;
    for i in 1..v.len() { s += v[i] ^ v[i - 1]; }
    s
}
#[no_mangle]
pub fn pick_f(v: &[u64], i: usize) -> u64 { v[i & 7] }
#[no_mangle]
pub fn pick_g(v: &[u64; 8], i: usize) -> u64 { v[i & 7] }
