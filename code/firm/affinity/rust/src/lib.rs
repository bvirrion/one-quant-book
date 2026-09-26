//! firm.affinity -- pin threads by role (One Quant Book 13, chapter 9). The standard library has no CPU affinity, so
//! the crate declares the three C functions it needs; each `unsafe` call states why it is sound.

use std::collections::BTreeMap;
use std::fs;

const SET_WORDS: usize = 16; // cpu_set_t is 1024 bits on x86-64 Linux

#[repr(C)]
struct CpuSet {
    bits: [u64; SET_WORDS],
}

extern "C" {
    fn sched_setaffinity(pid: i32, size: usize, mask: *const CpuSet) -> i32;
    fn sched_getaffinity(pid: i32, size: usize, mask: *mut CpuSet) -> i32;
    fn sched_getcpu() -> i32;
}

/// Roles to CPUs from a plan file: "role cpu" per line, '#' for comments.
pub fn read_plan(text: &str) -> BTreeMap<String, usize> {
    text.lines()
        .filter(|l| !l.trim().is_empty() && !l.starts_with('#'))
        .filter_map(|l| {
            let mut it = l.split_whitespace();
            Some((it.next()?.to_string(), it.next()?.parse().ok()?))
        })
        .collect()
}

pub fn read_plan_file(path: &str) -> std::io::Result<BTreeMap<String, usize>> {
    Ok(read_plan(&fs::read_to_string(path)?))
}

/// Pin the calling thread to `cpu`. Err if the CPU is out of range or the kernel refuses.
pub fn pin_current(cpu: usize) -> Result<(), String> {
    if cpu >= SET_WORDS * 64 {
        return Err(format!("cpu {cpu} out of range"));
    }
    let mut set = CpuSet { bits: [0; SET_WORDS] };
    set.bits[cpu / 64] |= 1u64 << (cpu % 64);
    // SAFETY: `set` is a live, properly sized cpu_set_t; pid 0 means the calling thread.
    let rc = unsafe { sched_setaffinity(0, std::mem::size_of::<CpuSet>(), &set) };
    if rc == 0 { Ok(()) } else { Err(format!("sched_setaffinity({cpu}) failed")) }
}

pub fn current_cpu() -> usize {
    // SAFETY: sched_getcpu takes no arguments and only returns a value.
    unsafe { sched_getcpu() as usize }
}

/// The CPUs this thread may run on.
pub fn allowed() -> Vec<usize> {
    let mut set = CpuSet { bits: [0; SET_WORDS] };
    // SAFETY: `set` is writable and has the size passed; pid 0 means the calling thread.
    unsafe { sched_getaffinity(0, std::mem::size_of::<CpuSet>(), &mut set) };
    (0..SET_WORDS * 64).filter(|&c| set.bits[c / 64] >> (c % 64) & 1 == 1).collect()
}

/// Pin the calling thread as `role`; returns its CPU once verified.
pub fn apply(plan: &BTreeMap<String, usize>, role: &str) -> Result<usize, String> {
    let &cpu = plan.get(role).ok_or(format!("role {role} not in plan"))?;
    pin_current(cpu)?;
    if current_cpu() == cpu { Ok(cpu) } else { Err(format!("{role} not on cpu {cpu}")) }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn plan_and_pinning() {
        let plan = read_plan_file("../data/plan_example.txt").unwrap();
        assert_eq!(plan.len(), 4);
        assert_eq!(plan["strategy"], 2);
        let target = allowed()[0];
        let mut p = BTreeMap::new();
        p.insert("feed".to_string(), target);
        let got = std::thread::spawn(move || apply(&p, "feed")).join().unwrap();
        assert_eq!(got, Ok(target));
        assert!(apply(&plan, "nosuch").is_err());
    }
}
