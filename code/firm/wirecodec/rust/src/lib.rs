//! firm.wirecodec -- flyweight codecs for the exchange simulator's wire formats (build of One Quant Book 13,
//! chapter 16). `generated.rs` is written by `gen_wirecodec.py` from `code/firm/exchsim/schema.json`; this file only
//! re-exports it and holds the tests against Book 10's golden fixtures.

#[allow(clippy::all)]
mod generated;
pub use generated::*;

/// Calls `f(message)` for each message block of a MoldUDP64 packet; false if the packet is short.
pub fn for_each_block(p: &[u8], mut f: impl FnMut(&[u8])) -> bool {
    if p.len() < MoldHeader::LENGTH {
        return false;
    }
    let c = MoldHeader(p).count();
    if c == 0 || c == 0xFFFF {
        return true;
    }
    let mut i = MoldHeader::LENGTH;
    for _ in 0..c {
        if i + 2 > p.len() {
            return false;
        }
        let len = u16::from_be_bytes([p[i], p[i + 1]]) as usize;
        if i + 2 + len > p.len() {
            return false;
        }
        f(&p[i + 2..i + 2 + len]);
        i += 2 + len;
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    fn golden(name: &str) -> std::path::PathBuf {
        std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../exchsim/data/golden").join(name)
    }

    #[test]
    fn every_golden_message_decodes_to_its_csv() {
        let mut total = 0;
        for (proto, f) in [
            ("feed", csv_feed as fn(&[u8]) -> Option<String>),
            ("in", csv_in),
            ("out", csv_out),
            ("ctl", csv_ctl),
        ] {
            let bin = std::fs::read(golden(&format!("{proto}.bin"))).unwrap();
            for t in 'A'..='Z' {
                let Ok(text) = std::fs::read_to_string(golden(&format!("{proto}_{t}.csv"))) else {
                    continue; // no message of this type in the fixture day
                };
                for line in text.lines().skip(1) {
                    let (off, want) = line.split_once(',').unwrap();
                    let off: usize = off.parse().unwrap();
                    let len = u16::from_be_bytes([bin[off], bin[off + 1]]) as usize;
                    assert_eq!(f(&bin[off + 2..off + 2 + len]).as_deref(), Some(want), "{proto} {t} at {off}");
                    total += 1;
                }
            }
        }
        assert!(total > 4000, "{total} golden messages");
    }

    #[test]
    fn mold_packets_split_into_messages() {
        // recorded file: send_ns u64 | length u32 | MoldUDP64 packet
        let rec = std::fs::read(golden("../fixture_mold.bin")).unwrap();
        let (mut i, mut packets, mut messages, mut next) = (0usize, 0, 0, 1u64);
        while i + 12 <= rec.len() {
            let len = u32::from_be_bytes(rec[i + 8..i + 12].try_into().unwrap()) as usize;
            let p = &rec[i + 12..i + 12 + len];
            assert_eq!(MoldHeader(p).seq(), next, "packets are consecutive on the recording point");
            assert!(for_each_block(p, |m| {
                assert!(csv_feed(m).is_some());
                messages += 1;
            }));
            next += MoldHeader(p).count() as u64 % 0xFFFF;
            packets += 1;
            i += 12 + len;
        }
        assert_eq!(packets, 200);
        assert!(messages >= 200);
    }
}
