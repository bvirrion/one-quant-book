#![allow(dead_code)]
use std::mem::size_of;

#[repr(C)]
struct Wire { seq: u32, ts: u64 }
#[repr(C, packed)]
struct Packed { seq: u32, ts: u64 }
struct Free { a: u8, b: u64, c: u8 }
#[repr(C)]
struct Fixed { a: u8, b: u64, c: u8 }

fn ts_cast(buf: &[u8]) -> u64 {
    let p = buf.as_ptr() as *const Wire;
    unsafe { (*p).ts }
}

fn ts_read(buf: &[u8]) -> u64 {
    u64::from_le_bytes(buf[8..16].try_into().unwrap())
}

fn main() {
    println!("{} {}", size_of::<Wire>(), size_of::<Packed>());
    println!("{} {}", size_of::<Free>(), size_of::<Fixed>());
    let backing = [1_u64, 2, 3, 4];
    let start = backing.as_ptr() as *const u8;
    let bytes = unsafe { std::slice::from_raw_parts(start, 32) };
    println!("{}", ts_read(&bytes[3..]));
    println!("{}", ts_cast(&bytes[3..]));
    let p = Packed { seq: 1, ts: 9 };
    println!("{}", { p.ts } + p.seq as u64);
}
