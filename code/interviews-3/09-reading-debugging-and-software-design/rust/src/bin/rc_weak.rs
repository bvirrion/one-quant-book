use std::cell::RefCell;
use std::rc::{Rc, Weak};

struct Node {
    name: &'static str,
    next: RefCell<Weak<Node>>,
}

impl Drop for Node {
    fn drop(&mut self) {
        println!("drop {}", self.name);
    }
}

fn main() {
    let a = Rc::new(Node { name: "a", next: RefCell::new(Weak::new()) });
    let b = Rc::new(Node { name: "b", next: RefCell::new(Rc::downgrade(&a)) });
    *a.next.borrow_mut() = Rc::downgrade(&b);
    println!("{} {}", Rc::strong_count(&a), Rc::strong_count(&b));
    println!("{}", b.next.borrow().upgrade().map_or("gone", |n| n.name));
}
