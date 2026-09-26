//! firm.feedhandler -- the feed handler in Rust (build of One Quant Book 13, chapter 18), the twin of the Python
//! reference and the C++20 header: same arbitration, gap handling, retransmission, snapshot recovery, normalised
//! events (compared by their FNV-1a hash) and staleness intervals on the shared fixtures.

use std::cmp::Reverse;
use std::collections::{BTreeMap, BinaryHeap};

fn be(b: &[u8], o: usize, n: usize) -> u64 {
    b[o..o + n].iter().fold(0u64, |v, &x| (v << 8) | x as u64)
}

/// Packets of a recorded file: (send_ns, packet).
pub fn recorded(f: &[u8]) -> Vec<(u64, &[u8])> {
    let (mut out, mut i) = (Vec::new(), 0);
    while i + 12 <= f.len() {
        let n = be(f, i + 8, 4) as usize;
        out.push((be(f, i, 8), &f[i + 12..i + 12 + n]));
        i += 12 + n;
    }
    out
}

/// (first sequence number, messages) of a MoldUDP64 packet.
pub fn blocks(p: &[u8]) -> (u64, Vec<&[u8]>) {
    let (seq, c) = (be(p, 10, 8), be(p, 18, 2) as usize);
    let mut msgs = Vec::new();
    if c != 0 && c != 0xFFFF {
        let mut i = 20;
        for _ in 0..c {
            let n = be(p, i, 2) as usize;
            msgs.push(&p[i + 2..i + 2 + n]);
            i += 2 + n;
        }
    }
    (seq, msgs)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct Event {
    pub kind: u8,
    pub side: u8,
    pub locate: u16,
    pub seq: u64,
    pub ts: u64,
    pub r#ref: u64,
    pub ref2: u64,
    pub price: u32,
    pub qty: u64,
}

pub fn normalise(m: &[u8], seq: u64) -> Event {
    let mut e = Event { kind: m[0], locate: be(m, 1, 2) as u16, ts: be(m, 5, 6), seq, ..Default::default() };
    match m[0] {
        b'A' => (e.r#ref, e.side, e.qty, e.price) = (be(m, 11, 8), m[19], be(m, 20, 4), be(m, 32, 4) as u32),
        b'E' => (e.r#ref, e.qty, e.ref2) = (be(m, 11, 8), be(m, 19, 4), be(m, 23, 8)),
        b'X' => (e.r#ref, e.qty) = (be(m, 11, 8), be(m, 19, 4)),
        b'D' => e.r#ref = be(m, 11, 8),
        b'P' => (e.side, e.qty, e.price, e.ref2) = (m[19], be(m, 20, 4), be(m, 32, 4) as u32, be(m, 36, 8)),
        b'U' => (e.r#ref, e.ref2, e.qty, e.price) = (be(m, 11, 8), be(m, 19, 8), be(m, 27, 4), be(m, 31, 4) as u32),
        b'C' => (e.r#ref, e.qty, e.ref2, e.price) = (be(m, 11, 8), be(m, 19, 4), be(m, 23, 8), be(m, 32, 4) as u32),
        b'Q' => (e.qty, e.price, e.ref2) = (be(m, 11, 8), be(m, 27, 4) as u32, be(m, 31, 8)),
        b'G' | b'W' => e.ref2 = be(m, 11, 8),
        _ => {}
    }
    e
}

pub fn fnv1a(e: &Event, mut h: u64) -> u64 {
    let mut b = Vec::with_capacity(48);
    b.extend_from_slice(&[e.kind, e.side]);
    b.extend_from_slice(&e.locate.to_le_bytes());
    for v in [e.seq, e.ts, e.r#ref, e.ref2] {
        b.extend_from_slice(&v.to_le_bytes());
    }
    b.extend_from_slice(&e.price.to_le_bytes());
    b.extend_from_slice(&e.qty.to_le_bytes());
    for x in b {
        h = (h ^ x as u64).wrapping_mul(0x100000001B3);
    }
    h
}

/// The simulator's retransmission service over the lossless stream.
pub struct RetxServer<'a> {
    pub clean: Vec<(u64, &'a [u8])>,
    pub window: u64,
    pub max_count: u64,
}

impl<'a> RetxServer<'a> {
    pub fn request(&self, t: u64, seq: u64, count: u64) -> Option<Vec<&'a [u8]>> {
        let mut published = 0;
        for &(pt, p) in &self.clean {
            if pt > t {
                break;
            }
            let (s, m) = blocks(p);
            if !m.is_empty() {
                published = published.max(s + m.len() as u64 - 1);
            }
        }
        if seq + self.window <= published || count == 0 {
            return None;
        }
        let count = count.min(self.max_count);
        Some(
            self.clean
                .iter()
                .filter(|(pt, p)| {
                    let (s, m) = blocks(p);
                    *pt <= t && s < seq + count && s + m.len() as u64 > seq
                })
                .map(|(_, p)| *p)
                .collect(),
        )
    }
}

#[derive(Default, Debug)]
pub struct Counters {
    pub packets: u64,
    pub messages: u64,
    pub duplicates: u64,
    pub gaps: u64,
    pub filled_by_line: u64,
    pub retransmissions: u64,
    pub snapshots: u64,
}

/// A queued input: (time, priority, input order, sub order, index into the packet store).
type Item = Reverse<(u64, u8, u64, u64, usize)>;

#[derive(PartialEq, Eq, Clone, Copy)]
enum Mode {
    Live,
    AwaitLine,
    AwaitRetx,
    AwaitSnapshot,
}

pub struct Handler<'a> {
    retx: Option<&'a RetxServer<'a>>,
    timeout: u64,
    rtt: u64,
    next: u64,
    mode: Mode,
    since: u64,
    deadline: u64,
    pending: BTreeMap<u64, &'a [u8]>,
    snap: Vec<&'a [u8]>,
    pub events: Vec<Event>,
    pub hash: u64,
    pub stale: Vec<(u64, u64)>,
    pub c: Counters,
}

impl<'a> Handler<'a> {
    pub fn new(retx: Option<&'a RetxServer<'a>>) -> Self {
        Handler {
            retx,
            timeout: 500_000,
            rtt: 200_000,
            next: 1,
            mode: Mode::Live,
            since: 0,
            deadline: 0,
            pending: BTreeMap::new(),
            snap: Vec::new(),
            events: Vec::new(),
            hash: 0xCBF29CE484222325,
            stale: Vec::new(),
            c: Counters::default(),
        }
    }

    fn publish(&mut self, e: Event) {
        self.hash = fnv1a(&e, self.hash);
        self.events.push(e);
    }

    fn drain(&mut self, t: u64) {
        while let Some(m) = self.pending.remove(&self.next) {
            self.publish(normalise(m, self.next));
            self.c.messages += 1;
            self.next += 1;
        }
        if self.mode != Mode::Live && self.pending.is_empty() {
            if self.mode == Mode::AwaitLine {
                self.c.filled_by_line += 1;
            }
            self.stale.push((self.since, t));
            self.mode = Mode::Live;
        }
    }

    fn incremental(&mut self, t: u64, p: &'a [u8]) {
        self.c.packets += 1;
        let (seq, msgs) = blocks(p);
        if !msgs.is_empty() && seq + msgs.len() as u64 <= self.next {
            self.c.duplicates += 1;
            return;
        }
        for (k, m) in msgs.into_iter().enumerate() {
            let s = seq + k as u64;
            if s < self.next {
                continue;
            }
            if s == self.next && self.mode == Mode::Live {
                self.publish(normalise(m, s));
                self.c.messages += 1;
                self.next += 1;
            } else {
                self.pending.entry(s).or_insert(m);
            }
        }
        if !self.pending.is_empty() && self.mode == Mode::Live {
            (self.mode, self.since, self.deadline) = (Mode::AwaitLine, t, t + self.timeout);
            self.c.gaps += 1;
        }
        self.drain(t);
    }

    fn apply_snapshot(&mut self, t: u64) {
        let upto = be(self.snap[0], 11, 8);
        if upto + 1 < self.next {
            self.snap.clear();
            return;
        }
        for m in std::mem::take(&mut self.snap) {
            self.publish(normalise(m, upto));
        }
        self.next = upto + 1;
        self.pending = self.pending.split_off(&(upto + 1));
        self.drain(t);
        if !self.pending.is_empty() && self.mode != Mode::Live {
            (self.mode, self.deadline) = (Mode::AwaitLine, t + self.timeout);
        }
    }

    fn timeout(&mut self, t0: u64, store: &mut Vec<&'a [u8]>, q: &mut BinaryHeap<Item>) {
        let first_held = *self.pending.keys().next().unwrap();
        match self.retx.and_then(|r| r.request(t0, self.next, first_held - self.next)) {
            None => {
                self.c.snapshots += 1;
                self.mode = Mode::AwaitSnapshot;
            }
            Some(reply) => {
                self.c.retransmissions += 1;
                self.mode = Mode::AwaitRetx;
                let (n, k) = (self.events.len() as u64, reply.len() as u64);
                for (sub, p) in reply.into_iter().enumerate() {
                    store.push(p);
                    q.push(Reverse((t0 + self.rtt, 2, n, sub as u64, store.len() - 1)));
                }
                q.push(Reverse((t0 + self.rtt, 2, n, k, usize::MAX))); // after the answer: ask for the rest
            }
        }
    }

    /// Lines A and B and the snapshot channel, as recorded.
    pub fn run(&mut self, a: &[(u64, &'a [u8])], b: &[(u64, &'a [u8])], s: &[(u64, &'a [u8])]) {
        // (t, priority, input order, sub order, kind: 0 line, 1 snapshot, 2 retransmission), packet
        let mut merged: Vec<(u64, u8, &'a [u8])> = a.iter().map(|&(t, p)| (t, 0, p)).collect();
        merged.extend(b.iter().map(|&(t, p)| (t, 1, p)));
        merged.extend(s.iter().map(|&(t, p)| (t, 2, p)));
        merged.sort_by_key(|&(t, src, _)| (t, src));
        let mut q: BinaryHeap<Item> = BinaryHeap::new();
        let mut store: Vec<&'a [u8]> = Vec::new();
        for (n, &(t, src, p)) in merged.iter().enumerate() {
            store.push(p);
            q.push(Reverse((t, if src == 2 { 1 } else { 0 }, n as u64, 0, store.len() - 1)));
        }
        while let Some(Reverse((t, pri, _, _, idx))) = q.pop() {
            if self.mode == Mode::AwaitLine && t >= self.deadline {
                let t0 = self.deadline;
                self.timeout(t0, &mut store, &mut q);
            }
            if idx == usize::MAX {
                if self.mode == Mode::AwaitRetx && !self.pending.is_empty() {
                    self.timeout(t, &mut store, &mut q);
                }
                continue;
            }
            let p = store[idx];
            if pri == 1 {
                if self.mode == Mode::AwaitSnapshot {
                    for m in blocks(p).1 {
                        if m[0] == b'G' {
                            self.snap = vec![m];
                        } else if !self.snap.is_empty() {
                            self.snap.push(m);
                            if m[0] == b'W' {
                                self.apply_snapshot(t);
                            }
                        }
                    }
                }
            } else {
                self.incremental(t, p);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixture_runs_match_the_reference() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../data");
        let read = |n: &str| std::fs::read(dir.join(n)).unwrap();
        let (fa, fb, fc, fs) = (read("lineA.bin"), read("lineB.bin"), read("clean.bin"), read("snapshot.bin"));
        let (a, b, clean, snap) = (recorded(&fa), recorded(&fb), recorded(&fc), recorded(&fs));
        let server = RetxServer { clean: clean.clone(), window: 100_000, max_count: 1000 };
        let expected = std::fs::read_to_string(dir.join("expected.txt")).unwrap();
        for (run, want) in ["clean", "retx", "snapshot"].iter().zip(expected.lines().skip(1)) {
            let mut h = Handler::new(if *run == "retx" { Some(&server) } else { None });
            if *run == "clean" {
                h.run(&clean, &[], &[]);
            } else {
                h.run(&a, &b, &snap);
            }
            let stale: u64 = h.stale.iter().map(|(s, e)| e - s).sum();
            let got = format!(
                "{run} {} {:016x} {} {} {} {} {} {} {} {}",
                h.events.len(),
                h.hash,
                h.stale.len(),
                stale,
                h.c.packets,
                h.c.duplicates,
                h.c.gaps,
                h.c.filled_by_line,
                h.c.retransmissions,
                h.c.snapshots
            );
            assert_eq!(got, want);
        }
    }
}
