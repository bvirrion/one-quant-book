//! ns per message to decode a recorded line with the generated Rust flyweights (median of 21 passes).
use std::time::Instant;

fn main() {
    let path = std::env::args().nth(1).expect("usage: ll_wire_bench lineA.bin");
    let rec = std::fs::read(path).expect("read the recorded line");
    let pk = ll_wire::packets(&rec);
    let mut t = Vec::new();
    let mut total = (0, 0);
    for _ in 0..23 {
        let a = Instant::now();
        total = std::hint::black_box(ll_wire::decode(&pk));
        t.push(a.elapsed().as_nanos() as f64 / total.1 as f64);
    }
    t.sort_by(|a, b| a.partial_cmp(b).unwrap());
    println!("decode,rust,{:.2}", t[t.len() / 2]);
    eprintln!("{} messages, checksum {}", total.1, total.0);
}
