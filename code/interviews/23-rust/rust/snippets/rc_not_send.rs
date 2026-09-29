use std::rc::Rc;
use std::thread;

fn main() {
    let book = Rc::new(vec![100, 101]);
    let h = thread::spawn(move || book.len());
    println!("{}", h.join().unwrap());
}
