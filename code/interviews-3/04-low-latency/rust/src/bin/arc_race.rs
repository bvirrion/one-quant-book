use iv33::my_arc::MyArc;
use std::thread;

fn main() {
    for _ in 0..2000 {
        let a = MyArc::new(vec![1_u64; 16]);
        let b = a.clone();
        let t = thread::spawn(move || b.iter().sum::<u64>());
        let here = a.iter().sum::<u64>();
        drop(a);
        assert_eq!(t.join().unwrap() + here, 32);
    }
    println!("ok");
}
