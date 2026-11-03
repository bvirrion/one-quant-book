use std::thread;

fn main() {
    let prices = vec![100_u64, 101, 99];
    let worker = thread::spawn(move || prices.iter().sum::<u64>());
    println!("{}", worker.join().unwrap());
}
