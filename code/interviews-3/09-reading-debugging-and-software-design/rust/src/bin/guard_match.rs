use std::sync::Mutex;

fn main() {
    let queue = Mutex::new(vec![1, 2, 3]);
    match queue.lock().unwrap().pop() {
        Some(x) => {
            queue.lock().unwrap().push(x * 2);
            println!("requeued {x}");
        }
        None => println!("empty"),
    }
    println!("done");
}
