//! Chapter 16: the Rust decode loop over a recorded line -- packets, message blocks, and the generated flyweights.

use firm_wirecodec::{for_each_block, FeedA, FeedD, FeedE, FeedP, FeedX};

/// The packets of a recorded file (send_ns u64 | length u32 | packet).
pub fn packets(rec: &[u8]) -> Vec<&[u8]> {
    let mut out = Vec::new();
    let mut i = 0;
    while i + 12 <= rec.len() {
        let n = u32::from_be_bytes([rec[i + 8], rec[i + 9], rec[i + 10], rec[i + 11]]) as usize;
        out.push(&rec[i + 12..i + 12 + n]);
        i += 12 + n;
    }
    out
}

/// Sum of the shares and prices of the order messages of every packet, and the number of messages seen.
pub fn decode(packets: &[&[u8]]) -> (u64, u64) {
    let (mut sum, mut n) = (0u64, 0u64);
    for p in packets {
        for_each_block(p, |m| {
            n += 1;
            sum += match (m[0], m.len()) {
                (b'A', FeedA::LENGTH) => FeedA(m).shares() as u64 + FeedA(m).price() as u64,
                (b'E', FeedE::LENGTH) => FeedE(m).shares() as u64,
                (b'X', FeedX::LENGTH) => FeedX(m).shares() as u64,
                (b'D', FeedD::LENGTH) => FeedD(m).r#ref(),
                (b'P', FeedP::LENGTH) => FeedP(m).shares() as u64 + FeedP(m).price() as u64,
                _ => 0,
            };
        });
    }
    (sum, n)
}

#[cfg(test)]
mod tests {
    #[test]
    fn a_packet_with_one_delete() {
        let mut p = vec![b' '; 10];
        p.extend_from_slice(&1u64.to_be_bytes());
        p.extend_from_slice(&1u16.to_be_bytes());
        let mut d = vec![b'D'];
        d.extend_from_slice(&[0u8; 10]);
        d.extend_from_slice(&42u64.to_be_bytes());
        p.extend_from_slice(&(d.len() as u16).to_be_bytes());
        p.extend_from_slice(&d);
        assert_eq!(super::decode(&[&p]), (42, 1));
    }
}
