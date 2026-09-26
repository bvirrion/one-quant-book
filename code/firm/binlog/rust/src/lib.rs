//! firm.binlog (Rust): binary log records and their offline formatting, twin of the C++20 logger and the Python
//! reference. `Logger::log` encodes a statement's identifier, a timestamp and raw arguments; `Logger::bytes` gives the
//! file (header of statements sorted by identifier, then records); `read` and `text` decode and format it.

use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq)]
pub enum Arg {
    I(i64),
    U(u64),
    D(f64),
    C(u8),
    S(String),
}

impl Arg {
    fn code(&self) -> u8 {
        match self {
            Arg::I(_) => b'i',
            Arg::U(_) => b'u',
            Arg::D(_) => b'd',
            Arg::C(_) => b'c',
            Arg::S(_) => b's',
        }
    }
    fn encode(&self, out: &mut Vec<u8>) {
        match self {
            Arg::I(v) => out.extend_from_slice(&v.to_le_bytes()),
            Arg::U(v) => out.extend_from_slice(&v.to_le_bytes()),
            Arg::D(v) => out.extend_from_slice(&v.to_le_bytes()),
            Arg::C(v) => out.push(*v),
            Arg::S(s) => {
                let b = &s.as_bytes()[..s.len().min(16)];
                out.push(b.len() as u8);
                out.extend_from_slice(b);
            }
        }
    }
}

/// FNV-1a over the format, a zero byte and the type codes, folded to 16 bits.
pub fn site_id(fmt: &str, types: &[u8]) -> u16 {
    let mut h: u32 = 2166136261;
    for &b in fmt.as_bytes().iter().chain(std::iter::once(&0u8)).chain(types) {
        h = (h ^ u32::from(b)).wrapping_mul(16777619);
    }
    ((h ^ (h >> 16)) & 0xffff) as u16
}

#[derive(Default)]
pub struct Logger {
    sites: BTreeMap<u16, (String, Vec<u8>)>,
    records: Vec<u8>,
}

impl Logger {
    pub fn log(&mut self, ts: u64, fmt: &str, args: &[Arg]) {
        let types: Vec<u8> = args.iter().map(Arg::code).collect();
        let id = site_id(fmt, &types);
        let e = self.sites.entry(id).or_insert_with(|| (fmt.to_string(), types.clone()));
        assert!(e.0 == fmt && e.1 == types, "two statements hash to {id}");
        let mut payload = Vec::new();
        for a in args {
            a.encode(&mut payload);
        }
        self.records.extend_from_slice(&id.to_le_bytes());
        self.records.extend_from_slice(&(payload.len() as u16).to_le_bytes());
        self.records.extend_from_slice(&0u32.to_le_bytes());
        self.records.extend_from_slice(&ts.to_le_bytes());
        self.records.extend_from_slice(&payload);
    }
    pub fn bytes(&self) -> Vec<u8> {
        let mut h = b"FBINLOG1".to_vec();
        h.extend_from_slice(&(self.sites.len() as u32).to_le_bytes());
        for (id, (fmt, types)) in &self.sites {
            h.extend_from_slice(&id.to_le_bytes());
            h.push(types.len() as u8);
            h.extend_from_slice(types);
            h.extend_from_slice(&(fmt.len() as u16).to_le_bytes());
            h.extend_from_slice(fmt.as_bytes());
        }
        h.extend_from_slice(&self.records);
        h
    }
}

pub type Sites = BTreeMap<u16, (String, Vec<u8>)>;
/// A decoded record: timestamp, statement identifier, arguments.
pub type Record = (u64, u16, Vec<Arg>);

fn u16_at(d: &[u8], p: usize) -> u16 {
    u16::from_le_bytes([d[p], d[p + 1]])
}
fn u64_at(d: &[u8], p: usize) -> u64 {
    u64::from_le_bytes(d[p..p + 8].try_into().unwrap())
}

/// Decodes a file into its statements and its records (timestamp, identifier, arguments).
pub fn read(d: &[u8]) -> Result<(Sites, Vec<Record>), String> {
    if d.len() < 12 || &d[..8] != b"FBINLOG1" {
        return Err("not a binlog file".into());
    }
    let n = u32::from_le_bytes(d[8..12].try_into().unwrap());
    let (mut p, mut sites) = (12usize, Sites::new());
    for _ in 0..n {
        let id = u16_at(d, p);
        let nt = d[p + 2] as usize;
        let types = d[p + 3..p + 3 + nt].to_vec();
        p += 3 + nt;
        let nf = u16_at(d, p) as usize;
        sites.insert(id, (String::from_utf8(d[p + 2..p + 2 + nf].to_vec()).unwrap(), types));
        p += 2 + nf;
    }
    let mut recs = Vec::new();
    while p + 16 <= d.len() {
        let (id, n, ts) = (u16_at(d, p), u16_at(d, p + 2) as usize, u64_at(d, p + 8));
        let types = &sites.get(&id).ok_or("unknown statement")?.1;
        let mut q = p + 16;
        let mut args = Vec::new();
        for &c in types {
            match c {
                b'i' => args.push(Arg::I(u64_at(d, q) as i64)),
                b'u' => args.push(Arg::U(u64_at(d, q))),
                b'd' => args.push(Arg::D(f64::from_bits(u64_at(d, q)))),
                b'c' => args.push(Arg::C(d[q])),
                _ => {
                    let k = d[q] as usize;
                    args.push(Arg::S(String::from_utf8(d[q + 1..q + 1 + k].to_vec()).unwrap()));
                    q += 1 + k;
                    continue;
                }
            }
            q += if c == b'c' { 1 } else { 8 };
        }
        if q != p + 16 + n {
            return Err(format!("record at {p}: bad payload length"));
        }
        recs.push((ts, id, args));
        p = q;
    }
    Ok((sites, recs))
}

fn show(a: &Arg) -> String {
    match a {
        Arg::I(v) => v.to_string(),
        Arg::U(v) => v.to_string(),
        // the Python reference's str(float): at least one decimal
        Arg::D(v) => {
            let s = format!("{v}");
            if s.contains('.') || s.contains('e') {
                s
            } else {
                s + ".0"
            }
        }
        Arg::C(c) => (*c as char).to_string(),
        Arg::S(s) => s.clone(),
    }
}

/// "ts formatted-message" per record: each {} replaced by the next argument.
pub fn text(sites: &Sites, recs: &[Record]) -> Vec<String> {
    recs.iter()
        .map(|(ts, id, args)| {
            let mut parts = sites[id].0.split("{}");
            let mut s = parts.next().unwrap_or("").to_string();
            for (a, rest) in args.iter().zip(parts) {
                s += &show(a);
                s += rest;
            }
            format!("{ts} {s}")
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample() -> Logger {
        let mut l = Logger::default();
        l.log(1_000, "engine start v{}", &[Arg::U(1)]);
        for k in 0..5i64 {
            let t = 34_200_000_000_000 + 1_000 * k as u64;
            let side = if k % 2 == 1 { b'S' } else { b'B' };
            let kind = if k > 1 { b'R' } else { b'N' };
            l.log(t, "{} {} at {} x {}", &[Arg::C(side), Arg::C(kind), Arg::I(999_900 + 100 * k), Arg::U(100 * (k as u64 + 1))]);
            l.log(t + 10, "fill {} of {} at {}, position {}", &[Arg::U(40 + k as u64), Arg::I(100), Arg::I(999_900 - 100 * k), Arg::I((k - 2) * 100)]);
            l.log(t + 20, "{} half-spread {} ticks, skew {}", &[Arg::S("SIM1".into()), Arg::D(2.5 + k as f64 / 4.0), Arg::I(-k)]);
        }
        l.log(34_200_000_009_000, "pulled", &[]);
        l
    }

    #[test]
    fn writes_the_fixture_bytes_and_formats_them() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../data");
        let want = std::fs::read(dir.join("sample.blog")).unwrap();
        assert_eq!(sample().bytes(), want);
        let (sites, recs) = read(&want).unwrap();
        let txt = std::fs::read_to_string(dir.join("sample.txt")).unwrap();
        assert_eq!(text(&sites, &recs), txt.lines().collect::<Vec<_>>());
    }
}
