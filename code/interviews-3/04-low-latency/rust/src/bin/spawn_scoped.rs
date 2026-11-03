use std::thread;

fn main() {
    let prices = vec![100_u64, 101, 99];
    let total = thread::scope(|s| {
        s.spawn(|| prices.iter().sum::<u64>()).join().unwrap()
    });
    println!("{} {}", total, prices.len());
}
