use std::mem::size_of;
use std::num::NonZeroU64;

fn main() {
    println!("{}", size_of::<u64>());
    println!("{}", size_of::<Option<u64>>());
    println!("{}", size_of::<Option<NonZeroU64>>());
    println!("{}", size_of::<Box<u64>>());
    println!("{}", size_of::<Option<Box<u64>>>());
    println!("{}", size_of::<&[u8]>());
    println!("{}", size_of::<Option<&[u8]>>());
    println!("{}", size_of::<Vec<u8>>());
    println!("{}", size_of::<Option<Vec<u8>>>());
    println!("{}", size_of::<Option<bool>>());
}
