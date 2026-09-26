//! firm.fixengine -- the FIX tag=value codec in Rust (build of One Quant Book 13, chapter 15): the twin of the C++
//! `View`, `Builder` and `frame`, held to the same published example and to every message of the golden
//! conversation. The session layer lives in the C++ engine and the Python reference.

use firm_simdscan::{parse_uint, positions};

pub const SOH: u8 = 1;

#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum Error {
    Framing,
    Tag,
    Order,
    BodyLength,
    Checksum,
}

pub fn checksum(b: &[u8]) -> u32 {
    b.iter().map(|&x| x as u32).sum::<u32>() % 256
}

/// A parsed message: (tag, value range) pairs into the caller's buffer.
pub struct View<'a> {
    buf: &'a [u8],
    fields: Vec<(u32, usize, usize)>,
}

impl<'a> View<'a> {
    pub fn parse(buf: &'a [u8]) -> Result<Self, Error> {
        let n = buf.len();
        if n < 5 || &buf[..2] != b"8=" || buf[n - 1] != SOH {
            return Err(Error::Framing);
        }
        let mut soh = Vec::with_capacity(64);
        positions(buf, SOH, &mut soh);
        let mut fields = Vec::with_capacity(soh.len());
        let mut start = 0usize;
        for &end in &soh {
            let end = end as usize;
            let (tag, used) = parse_uint(&buf[start..end]).ok_or(Error::Tag)?;
            if buf.get(start + used) != Some(&b'=') {
                return Err(Error::Tag);
            }
            fields.push((tag as u32, start + used + 1, end));
            start = end + 1;
        }
        let tags: Vec<u32> = fields.iter().take(3).map(|f| f.0).collect();
        if fields.len() < 4 || tags != [8, 9, 35] || fields.last().map(|f| f.0) != Some(10) {
            return Err(Error::Order);
        }
        // found by chapter 25's fuzzer: a CheckSum (or a header tag) inside the body
        if fields[3..fields.len() - 1].iter().any(|f| (8..=10).contains(&f.0)) {
            return Err(Error::Order);
        }
        let body_start = fields[1].2 + 1;
        let body_end = fields[fields.len() - 1].1 - 3;
        let declared = parse_uint(&buf[fields[1].1..fields[1].2]).map(|x| x.0);
        if declared != Some((body_end - body_start) as u64) {
            return Err(Error::BodyLength);
        }
        let ck = &buf[fields[fields.len() - 1].1..fields[fields.len() - 1].2];
        if ck.len() != 3 || parse_uint(ck).map(|x| x.0) != Some(checksum(&buf[..body_end]) as u64) {
            return Err(Error::Checksum);
        }
        Ok(View { buf, fields })
    }

    pub fn get(&self, tag: u32) -> Option<&'a [u8]> {
        self.fields.iter().find(|f| f.0 == tag).map(|f| &self.buf[f.1..f.2])
    }

    pub fn len(&self) -> usize {
        self.fields.len()
    }

    pub fn is_empty(&self) -> bool {
        self.fields.is_empty()
    }
}

/// Length of the first complete message at the start of `buf`: Ok(0) if more bytes are needed.
pub fn frame(buf: &[u8]) -> Result<usize, Error> {
    if buf.len() < 2 {
        return Ok(0);
    }
    if &buf[..2] != b"8=" {
        return Err(Error::Framing);
    }
    let Some(a) = buf.iter().position(|&c| c == SOH) else { return Ok(0) };
    if buf.len() < a + 3 {
        return Ok(0);
    }
    if &buf[a + 1..a + 3] != b"9=" {
        return Err(Error::Framing);
    }
    let Some(b) = buf[a + 1..].iter().position(|&c| c == SOH).map(|p| p + a + 1) else { return Ok(0) };
    let body = parse_uint(&buf[a + 3..b]).ok_or(Error::Framing)?.0 as usize;
    let total = b + 1 + body + 7;
    Ok(if buf.len() >= total { total } else { 0 })
}

/// Builds a message: header fields, then the body, then 9 and 10 computed.
pub fn encode(begin: &str, fields: &[(u32, &[u8])]) -> Vec<u8> {
    let mut body = Vec::with_capacity(256);
    for (t, v) in fields {
        body.extend_from_slice(t.to_string().as_bytes());
        body.push(b'=');
        body.extend_from_slice(v);
        body.push(SOH);
    }
    let mut m = format!("8={begin}\x019={}\x01", body.len()).into_bytes();
    m.extend_from_slice(&body);
    let c = checksum(&m);
    m.extend_from_slice(format!("10={c:03}\x01").as_bytes());
    m
}

#[cfg(test)]
mod tests {
    use super::*;

    fn data(name: &str) -> String {
        std::fs::read_to_string(format!("{}/../data/{name}", env!("CARGO_MANIFEST_DIR"))).unwrap()
    }

    fn soh(s: &str) -> Vec<u8> {
        s.trim().bytes().map(|c| if c == b'|' { SOH } else { c }).collect()
    }

    #[test]
    fn published_example() {
        let ex = soh(&data("wikipedia_example.fix"));
        let v = View::parse(&ex).unwrap();
        assert_eq!(v.get(9), Some(&b"65"[..]));
        assert_eq!(v.get(10), Some(&b"062"[..]));
        let mut bad = ex.clone();
        let i = ex.windows(6).position(|w| w == b"SERVER").unwrap();
        bad[i] = b'X';
        assert_eq!(View::parse(&bad).err(), Some(Error::Checksum));
    }

    #[test]
    fn every_golden_message_parses_and_rebuilds() {
        let trace = data("expected_trace.txt");
        let mut n = 0;
        for line in trace.lines() {
            let mut it = line.splitn(3, ' ');
            let (_, dir, rest) = (it.next(), it.next().unwrap(), it.next().unwrap_or(""));
            if dir != "in" && dir != "out" {
                continue;
            }
            let m = soh(rest);
            let v = View::parse(&m).unwrap();
            let fields: Vec<(u32, &[u8])> = v.fields[2..v.len() - 1].iter().map(|f| (f.0, &m[f.1..f.2])).collect();
            assert_eq!(encode("FIX.4.4", &fields), m);
            assert_eq!(frame(&m), Ok(m.len()));
            assert_eq!(frame(&m[..m.len() - 1]), Ok(0));
            n += 1;
        }
        assert_eq!(n, 19);
    }
}
