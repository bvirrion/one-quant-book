//! firm_tickstore -- read the tick store's flat files in place through a memory map (One Quant Book 15, ch. 4).
//! Rust twin of cpp/firm_tickstore.hpp; no external crates: mmap and munmap are declared from the C library.
//! Layout: header (b"OQTS", u16 version, u16 record size, u32 schema length, schema JSON, padding to 64 bytes),
//! then fixed-width little-endian records (version 1: 56 bytes; version 2: 64 bytes, three fields appended).

use std::collections::BTreeMap;
use std::ffi::c_void;
use std::fs::File;
use std::os::unix::io::AsRawFd;

const PROT_READ: i32 = 1;
const MAP_PRIVATE: i32 = 2;

extern "C" {
    fn mmap(addr: *mut c_void, len: usize, prot: i32, flags: i32, fd: i32, offset: i64) -> *mut c_void;
    fn munmap(addr: *mut c_void, len: usize) -> i32;
}

pub struct FlatFile {
    _file: File,
    base: *const u8,
    len: usize,
    start: usize,
    record: usize,
    pub version: u16,
    pub n: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Event {
    pub recv: u64,
    pub kind: u8,
    pub locate: u16,
    pub seq: u64,
    pub qty: u64,
}

fn rd<const N: usize>(s: &[u8], at: usize) -> [u8; N] {
    s[at..at + N].try_into().expect("in bounds")
}

impl FlatFile {
    pub fn open(path: &str) -> std::io::Result<FlatFile> {
        let file = File::open(path)?;
        let len = file.metadata()?.len() as usize;
        let bad = |m: &str| std::io::Error::new(std::io::ErrorKind::InvalidData, m.to_string());
        if len < 12 {
            return Err(bad("too short"));
        }
        // SAFETY: a read-only private mapping of a file we keep open; checked against MAP_FAILED (-1).
        let p = unsafe { mmap(std::ptr::null_mut(), len, PROT_READ, MAP_PRIVATE, file.as_raw_fd(), 0) };
        if p as isize == -1 {
            return Err(std::io::Error::last_os_error());
        }
        let mut f = FlatFile { _file: file, base: p as *const u8, len, start: 0, record: 0, version: 0, n: 0 };
        let head = f.bytes();
        if &head[0..4] != b"OQTS" {
            return Err(bad("not a flat file"));
        }
        let version = u16::from_le_bytes(rd(head, 4));
        let record = u16::from_le_bytes(rd(head, 6)) as usize;
        if !matches!((version, record), (1, 56) | (2, 64)) {
            return Err(bad("unknown version"));
        }
        let start = (12 + u32::from_le_bytes(rd(head, 8)) as usize).div_ceil(64) * 64;
        (f.version, f.record, f.start, f.n) = (version, record, start, (len - start) / record);
        Ok(f)
    }

    fn bytes(&self) -> &[u8] {
        // SAFETY: base points to len mapped, readable bytes for the lifetime of self.
        unsafe { std::slice::from_raw_parts(self.base, self.len) }
    }

    pub fn get(&self, i: usize) -> Event {
        let r = &self.bytes()[self.start + i * self.record..self.start + (i + 1) * self.record];
        Event {
            recv: u64::from_le_bytes(rd(r, 0)),
            kind: r[8],
            locate: u16::from_le_bytes(rd(r, 10)),
            seq: u64::from_le_bytes(rd(r, 12)),
            qty: u64::from_le_bytes(rd(r, 48)),
        }
    }

    /// Per instrument: (records, quantity executed by 'E' events, last sequence number).
    pub fn summarise(&self) -> BTreeMap<u16, (u64, u64, u64)> {
        let mut out: BTreeMap<u16, (u64, u64, u64)> = BTreeMap::new();
        for i in 0..self.n {
            let e = self.get(i);
            let s = out.entry(e.locate).or_insert((0, 0, 0));
            s.0 += 1;
            if e.kind == b'E' {
                s.1 += e.qty;
            }
            s.2 = s.2.max(e.seq);
        }
        out
    }
}

impl Drop for FlatFile {
    fn drop(&mut self) {
        // SAFETY: unmaps exactly the mapping created in open.
        unsafe {
            munmap(self.base as *mut c_void, self.len);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixture_summaries_match_python() {
        let dir = concat!(env!("CARGO_MANIFEST_DIR"), "/../data/");
        let expected = std::fs::read_to_string(format!("{dir}fixture_expected.txt")).unwrap();
        let mut rows = 0;
        for line in expected.lines() {
            let f: Vec<&str> = line.split_whitespace().collect();
            let file = FlatFile::open(&format!("{dir}{}", f[0])).unwrap();
            let got = file.summarise()[&f[1].parse::<u16>().unwrap()];
            let want: (u64, u64, u64) = (f[2].parse().unwrap(), f[3].parse().unwrap(), f[4].parse().unwrap());
            assert_eq!(got, want, "{line}");
            rows += 1;
        }
        assert!(rows >= 4);
    }

    #[test]
    fn both_versions_hold_the_same_events() {
        let dir = concat!(env!("CARGO_MANIFEST_DIR"), "/../data/");
        let (a, b) = (FlatFile::open(&format!("{dir}fixture_v1.flat")).unwrap(),
                      FlatFile::open(&format!("{dir}fixture_v2.flat")).unwrap());
        assert_eq!((a.version, b.version, a.n), (1, 2, b.n));
        assert!((0..a.n).all(|i| a.get(i) == b.get(i)));
    }
}
