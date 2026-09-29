fn main() {
    let mut qty = vec![10, 20];
    let a = &mut qty[0];
    let b = &mut qty[1];
    *a += *b;
}
