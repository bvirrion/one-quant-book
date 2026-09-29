fn best_level(levels: &[i64]) -> &i64 {
    let top = levels[0] + 1;
    &top
}

fn main() {
    println!("{}", best_level(&[100]));
}
