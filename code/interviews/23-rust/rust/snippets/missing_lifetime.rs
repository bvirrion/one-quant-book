fn best(a: &str, b: &str) -> &str {
    if a > b { a } else { b }
}

fn main() {
    println!("{}", best("x", "y"));
}
