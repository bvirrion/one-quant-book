fn main() {
    let px = 100;
    let px = px * 2;
    {
        let px = px + 1;
        println!("{px}");
    }
    println!("{px}");
}
