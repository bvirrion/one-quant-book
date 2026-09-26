//! firm.wsclient -- the WebSocket frame codec and the HMAC-SHA-256 request signer in Rust (build of One Quant Book
//! 13, chapter 17), twins of the C++20 header, held to RFC 6455's examples, RFC 4231's vectors, a venue's published
//! signing example and the shared frame fixture.

pub const TEXT: u8 = 0x1;
pub const BINARY: u8 = 0x2;
pub const CLOSE: u8 = 0x8;
pub const PING: u8 = 0x9;

#[derive(Debug, PartialEq, Eq)]
pub struct Frame {
    pub fin: bool,
    pub opcode: u8,
    pub payload: Vec<u8>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum FrameError {
    Incomplete,
    ReservedBits,
    LengthEncoding,
    BadControl,
}

fn unmask(p: &mut [u8], key: [u8; 4]) {
    for (i, b) in p.iter_mut().enumerate() {
        *b ^= key[i % 4];
    }
}

pub fn encode_frame(payload: &[u8], opcode: u8, fin: bool, key: Option<[u8; 4]>) -> Vec<u8> {
    let mut out = vec![(if fin { 0x80 } else { 0 }) | opcode];
    let m = if key.is_some() { 0x80 } else { 0 };
    let n = payload.len();
    if n <= 125 {
        out.push(m | n as u8);
    } else if n <= 0xFFFF {
        out.push(m | 126);
        out.extend_from_slice(&(n as u16).to_be_bytes());
    } else {
        out.push(m | 127);
        out.extend_from_slice(&(n as u64).to_be_bytes());
    }
    let start = out.len() + if key.is_some() { 4 } else { 0 };
    if let Some(k) = key {
        out.extend_from_slice(&k);
    }
    out.extend_from_slice(payload);
    if let Some(k) = key {
        unmask(&mut out[start..], k);
    }
    out
}

/// One frame at the start of `b`: the frame (payload unmasked) and the bytes used.
pub fn decode_frame(b: &[u8]) -> Result<(Frame, usize), FrameError> {
    if b.len() < 2 {
        return Err(FrameError::Incomplete);
    }
    if b[0] & 0x70 != 0 {
        return Err(FrameError::ReservedBits);
    }
    let (fin, opcode, masked) = (b[0] & 0x80 != 0, b[0] & 0x0F, b[1] & 0x80 != 0);
    let (mut n, mut i) = ((b[1] & 0x7F) as u64, 2usize);
    if n == 126 {
        let x = b.get(2..4).ok_or(FrameError::Incomplete)?;
        n = u16::from_be_bytes([x[0], x[1]]) as u64;
        i = 4;
        if n < 126 {
            return Err(FrameError::LengthEncoding);
        }
    } else if n == 127 {
        let x = b.get(2..10).ok_or(FrameError::Incomplete)?;
        n = u64::from_be_bytes(x.try_into().unwrap());
        i = 10;
        if n <= 0xFFFF || n >> 63 != 0 {
            return Err(FrameError::LengthEncoding);
        }
    }
    if opcode >= 0x8 && (n > 125 || !fin) {
        return Err(FrameError::BadControl);
    }
    let mut key = None;
    if masked {
        let k = b.get(i..i + 4).ok_or(FrameError::Incomplete)?;
        key = Some([k[0], k[1], k[2], k[3]]);
        i += 4;
    }
    let n = n as usize;
    let mut payload = b.get(i..i + n).ok_or(FrameError::Incomplete)?.to_vec();
    if let Some(k) = key {
        unmask(&mut payload, k);
    }
    Ok((Frame { fin, opcode, payload }, i + n))
}

/// SHA-256 (FIPS 180-4).
#[derive(Clone)]
pub struct Sha256 {
    h: [u32; 8],
    buf: Vec<u8>,
    n: u64,
}

const K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98,
    0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8,
    0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819,
    0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
    0xc67178f2,
];

impl Default for Sha256 {
    fn default() -> Self {
        Sha256 {
            h: [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19],
            buf: Vec::with_capacity(64),
            n: 0,
        }
    }
}

impl Sha256 {
    fn block(&mut self, p: &[u8]) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes([p[4 * i], p[4 * i + 1], p[4 * i + 2], p[4 * i + 3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16].wrapping_add(s0).wrapping_add(w[i - 7]).wrapping_add(s1);
        }
        let mut v = self.h;
        for i in 0..64 {
            let e = v[4];
            let t1 = v[7]
                .wrapping_add(e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25))
                .wrapping_add((e & v[5]) ^ (!e & v[6]))
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let a = v[0];
            let t2 = (a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22))
                .wrapping_add((a & v[1]) ^ (a & v[2]) ^ (v[1] & v[2]));
            v = [t1.wrapping_add(t2), a, v[1], v[2], v[3].wrapping_add(t1), e, v[5], v[6]];
        }
        for (h, x) in self.h.iter_mut().zip(v) {
            *h = h.wrapping_add(x);
        }
    }

    pub fn update(&mut self, mut p: &[u8]) {
        self.n += p.len() as u64;
        if !self.buf.is_empty() {
            let k = p.len().min(64 - self.buf.len());
            self.buf.extend_from_slice(&p[..k]);
            p = &p[k..];
            if self.buf.len() < 64 {
                return;
            }
            let b = std::mem::take(&mut self.buf);
            self.block(&b);
            self.buf = b;
            self.buf.clear();
        }
        while p.len() >= 64 {
            self.block(&p[..64]);
            p = &p[64..];
        }
        self.buf.extend_from_slice(p);
    }

    pub fn finish(mut self) -> [u8; 32] {
        let bits = self.n * 8;
        self.update(&[0x80]);
        while self.buf.len() != 56 {
            self.update(&[0]);
        }
        self.update(&bits.to_be_bytes());
        let mut out = [0u8; 32];
        for (i, h) in self.h.iter().enumerate() {
            out[4 * i..4 * i + 4].copy_from_slice(&h.to_be_bytes());
        }
        out
    }
}

/// HMAC-SHA-256 with the key's pads hashed once (RFC 2104).
pub struct HmacSha256 {
    inner: Sha256,
    outer: Sha256,
}

impl HmacSha256 {
    pub fn new(key: &[u8]) -> Self {
        let mut k = [0u8; 64];
        if key.len() > 64 {
            let mut h = Sha256::default();
            h.update(key);
            k[..32].copy_from_slice(&h.finish());
        } else {
            k[..key.len()].copy_from_slice(key);
        }
        let (mut inner, mut outer) = (Sha256::default(), Sha256::default());
        inner.update(&k.map(|b| b ^ 0x36));
        outer.update(&k.map(|b| b ^ 0x5c));
        HmacSha256 { inner, outer }
    }

    pub fn sign(&self, msg: &[u8]) -> [u8; 32] {
        let mut i = self.inner.clone();
        i.update(msg);
        let mut o = self.outer.clone();
        o.update(&i.finish());
        o.finish()
    }

    pub fn hex(&self, msg: &[u8]) -> String {
        self.sign(msg).iter().map(|b| format!("{b:02x}")).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn hex(b: &[u8]) -> String {
        b.iter().map(|x| format!("{x:02x}")).collect()
    }

    #[test]
    fn rfc6455_examples() {
        assert_eq!(hex(&encode_frame(b"Hello", TEXT, true, None)), "810548656c6c6f");
        let m = encode_frame(b"Hello", TEXT, true, Some([0x37, 0xfa, 0x21, 0x3d]));
        assert_eq!(hex(&m), "818537fa213d7f9f4d5158");
        assert_eq!(decode_frame(&m).unwrap().0.payload, b"Hello");
        assert_eq!(&encode_frame(&[b'x'; 65536], BINARY, true, None)[..10], &[0x82, 127, 0, 0, 0, 0, 0, 1, 0, 0]);
        assert_eq!(decode_frame(&[0x81, 0x7e, 0, 5, b'h']).err(), Some(FrameError::LengthEncoding));
        assert_eq!(decode_frame(&[0x89, 0x7e]).err(), Some(FrameError::Incomplete));
    }

    #[test]
    fn fixture_stream_matches_the_reference() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../data");
        let st = std::fs::read(dir.join("frames.bin")).unwrap();
        let want = std::fs::read_to_string(dir.join("frames_expected.txt")).unwrap();
        let (mut i, mut got, mut op, mut parts) = (0, Vec::new(), 0u8, Vec::new());
        while i < st.len() {
            let (f, used) = decode_frame(&st[i..]).unwrap();
            i += used;
            if f.opcode >= 0x8 {
                got.push(format!("{} {}", f.opcode, hex(&f.payload)));
                continue;
            }
            if f.opcode != 0 {
                op = f.opcode;
            }
            parts.extend_from_slice(&f.payload);
            if f.fin {
                got.push(format!("{} {}", op, hex(&parts)));
                parts.clear();
            }
        }
        assert_eq!(got, want.lines().collect::<Vec<_>>());
    }

    #[test]
    fn hmac_vectors() {
        assert_eq!(
            HmacSha256::new(&[0x0b; 20]).hex(b"Hi There"),
            "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"
        );
        assert_eq!(
            HmacSha256::new(b"Jefe").hex(b"what do ya want for nothing?"),
            "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        );
        assert_eq!(
            HmacSha256::new(&[0xaa; 131]).hex(b"Test Using Larger Than Block-Size Key - Hash Key First"),
            "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54"
        );
        let s = HmacSha256::new(b"NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j");
        let p = b"symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559";
        assert_eq!(s.hex(p), "c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71");
    }
}
