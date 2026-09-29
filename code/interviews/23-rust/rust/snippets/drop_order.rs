struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

struct Pair {
    _first: Noisy,
    _second: Noisy,
}

fn main() {
    let _a = Noisy("a");
    let _p = Pair { _first: Noisy("first"), _second: Noisy("second") };
    let _b = Noisy("b");
    let _ = Noisy("ignored");
    println!("end of main");
}
