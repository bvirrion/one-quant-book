fn imbalance(bids: &[u32], asks: &[u32]) -> usize {
    bids.len() - asks.len()
}

fn main() {
    let bids = vec![10, 20];
    let asks = vec![10, 20, 30];
    println!("{}", imbalance(&bids, &asks));
}
