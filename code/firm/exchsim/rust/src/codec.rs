//! Byte layouts of PROTOCOL.md / schema.json. Big-endian; one struct per protocol carries every field any
//! message of that protocol uses, and `kind` selects the layout (as in `cpp/exchsim_codec.hpp`).

#[derive(Debug, PartialEq, Eq)]
pub enum CodecError {
    Empty,
    UnknownType(u8),
    BadLength { kind: u8, len: usize },
    Truncated,
}

fn put(b: &mut Vec<u8>, v: u64, n: usize) {
    for i in (0..n).rev() {
        b.push((v >> (8 * i)) as u8);
    }
}

fn get(s: &[u8], off: usize, n: usize) -> u64 {
    s[off..off + n].iter().fold(0u64, |v, &x| (v << 8) | u64::from(x))
}

fn put_alpha(b: &mut Vec<u8>, s: &[u8], n: usize) {
    for i in 0..n {
        b.push(*s.get(i).unwrap_or(&b' '));
    }
}

fn a8(s: &[u8], off: usize) -> [u8; 8] {
    let mut x = [0u8; 8];
    x.copy_from_slice(&s[off..off + 8]);
    x
}

fn check(s: &[u8], len: fn(u8) -> usize) -> Result<u8, CodecError> {
    let kind = *s.first().ok_or(CodecError::Empty)?;
    let want = len(kind);
    if want == 0 {
        return Err(CodecError::UnknownType(kind));
    }
    if s.len() != want {
        return Err(CodecError::BadLength { kind, len: s.len() });
    }
    Ok(kind)
}

/// A feed message (the `feed` protocol).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Feed {
    pub kind: u8,
    pub locate: u16,
    pub tracking: u16,
    pub ts: u64,
    pub reference: u64,
    pub new_ref: u64,
    pub matched: u64,
    pub seq: u64,
    pub side: u8,
    pub printable: u8,
    pub cross_type: u8,
    pub direction: u8,
    pub variation: u8,
    pub event: u8,
    pub state: u8,
    pub reserved: u8,
    pub matching: u8,
    pub shares: u64,
    pub stock: [u8; 8],
    pub price: u32,
    pub far: u32,
    pub near: u32,
    pub ref_price: u32,
    pub tick: u32,
    pub lot: u32,
    pub orders: u32,
    pub crc: u32,
    pub paired: u64,
    pub imbalance: u64,
    pub reason: [u8; 4],
}

impl Default for Feed {
    fn default() -> Self {
        Feed {
            kind: 0,
            locate: 0,
            tracking: 0,
            ts: 0,
            reference: 0,
            new_ref: 0,
            matched: 0,
            seq: 0,
            side: b' ',
            printable: b' ',
            cross_type: b' ',
            direction: b' ',
            variation: b' ',
            event: b' ',
            state: b' ',
            reserved: b' ',
            matching: b' ',
            shares: 0,
            stock: [b' '; 8],
            price: 0,
            far: 0,
            near: 0,
            ref_price: 0,
            tick: 0,
            lot: 0,
            orders: 0,
            crc: 0,
            paired: 0,
            imbalance: 0,
            reason: [b' '; 4],
        }
    }
}

pub fn feed_length(kind: u8) -> usize {
    match kind {
        b'A' => 36,
        b'E' => 31,
        b'X' => 23,
        b'D' => 19,
        b'P' => 44,
        b'U' => 35,
        b'C' => 36,
        b'Q' => 40,
        b'I' => 50,
        b'S' => 12,
        b'H' => 25,
        b'R' => 28,
        b'G' => 23,
        b'W' => 23,
        _ => 0,
    }
}

impl Feed {
    pub fn encode(&self, b: &mut Vec<u8>) {
        b.push(self.kind);
        put(b, u64::from(self.locate), 2);
        put(b, u64::from(self.tracking), 2);
        put(b, self.ts, 6);
        match self.kind {
            b'A' => {
                put(b, self.reference, 8);
                b.push(self.side);
                put(b, self.shares, 4);
                b.extend_from_slice(&self.stock);
                put(b, u64::from(self.price), 4);
            }
            b'E' => {
                put(b, self.reference, 8);
                put(b, self.shares, 4);
                put(b, self.matched, 8);
            }
            b'X' => {
                put(b, self.reference, 8);
                put(b, self.shares, 4);
            }
            b'D' => put(b, self.reference, 8),
            b'P' => {
                put(b, self.reference, 8);
                b.push(self.side);
                put(b, self.shares, 4);
                b.extend_from_slice(&self.stock);
                put(b, u64::from(self.price), 4);
                put(b, self.matched, 8);
            }
            b'U' => {
                put(b, self.reference, 8);
                put(b, self.new_ref, 8);
                put(b, self.shares, 4);
                put(b, u64::from(self.price), 4);
            }
            b'C' => {
                put(b, self.reference, 8);
                put(b, self.shares, 4);
                put(b, self.matched, 8);
                b.push(self.printable);
                put(b, u64::from(self.price), 4);
            }
            b'Q' => {
                put(b, self.shares, 8);
                b.extend_from_slice(&self.stock);
                put(b, u64::from(self.price), 4);
                put(b, self.matched, 8);
                b.push(self.cross_type);
            }
            b'I' => {
                put(b, self.paired, 8);
                put(b, self.imbalance, 8);
                b.push(self.direction);
                b.extend_from_slice(&self.stock);
                put(b, u64::from(self.far), 4);
                put(b, u64::from(self.near), 4);
                put(b, u64::from(self.ref_price), 4);
                b.push(self.cross_type);
                b.push(self.variation);
            }
            b'S' => b.push(self.event),
            b'H' => {
                b.extend_from_slice(&self.stock);
                b.push(self.state);
                b.push(self.reserved);
                b.extend_from_slice(&self.reason);
            }
            b'R' => {
                b.extend_from_slice(&self.stock);
                put(b, u64::from(self.tick), 4);
                put(b, u64::from(self.lot), 4);
                b.push(self.matching);
            }
            b'G' => {
                put(b, self.seq, 8);
                put(b, u64::from(self.orders), 4);
            }
            b'W' => {
                put(b, self.seq, 8);
                put(b, u64::from(self.crc), 4);
            }
            _ => {}
        }
    }

    pub fn decode(s: &[u8]) -> Result<Feed, CodecError> {
        let kind = check(s, feed_length)?;
        let mut m = Feed {
            kind,
            locate: get(s, 1, 2) as u16,
            tracking: get(s, 3, 2) as u16,
            ts: get(s, 5, 6),
            ..Feed::default()
        };
        let u4 = |o: usize| get(s, o, 4) as u32;
        match kind {
            b'A' => {
                m.reference = get(s, 11, 8);
                m.side = s[19];
                m.shares = get(s, 20, 4);
                m.stock = a8(s, 24);
                m.price = u4(32);
            }
            b'E' => {
                m.reference = get(s, 11, 8);
                m.shares = get(s, 19, 4);
                m.matched = get(s, 23, 8);
            }
            b'X' => {
                m.reference = get(s, 11, 8);
                m.shares = get(s, 19, 4);
            }
            b'D' => m.reference = get(s, 11, 8),
            b'P' => {
                m.reference = get(s, 11, 8);
                m.side = s[19];
                m.shares = get(s, 20, 4);
                m.stock = a8(s, 24);
                m.price = u4(32);
                m.matched = get(s, 36, 8);
            }
            b'U' => {
                m.reference = get(s, 11, 8);
                m.new_ref = get(s, 19, 8);
                m.shares = get(s, 27, 4);
                m.price = u4(31);
            }
            b'C' => {
                m.reference = get(s, 11, 8);
                m.shares = get(s, 19, 4);
                m.matched = get(s, 23, 8);
                m.printable = s[31];
                m.price = u4(32);
            }
            b'Q' => {
                m.shares = get(s, 11, 8);
                m.stock = a8(s, 19);
                m.price = u4(27);
                m.matched = get(s, 31, 8);
                m.cross_type = s[39];
            }
            b'I' => {
                m.paired = get(s, 11, 8);
                m.imbalance = get(s, 19, 8);
                m.direction = s[27];
                m.stock = a8(s, 28);
                m.far = u4(36);
                m.near = u4(40);
                m.ref_price = u4(44);
                m.cross_type = s[48];
                m.variation = s[49];
            }
            b'S' => m.event = s[11],
            b'H' => {
                m.stock = a8(s, 11);
                m.state = s[19];
                m.reserved = s[20];
                m.reason.copy_from_slice(&s[21..25]);
            }
            b'R' => {
                m.stock = a8(s, 11);
                m.tick = u4(19);
                m.lot = u4(23);
                m.matching = s[27];
            }
            b'G' => {
                m.seq = get(s, 11, 8);
                m.orders = u4(19);
            }
            b'W' => {
                m.seq = get(s, 11, 8);
                m.crc = u4(19);
            }
            _ => {}
        }
        Ok(m)
    }
}

/// An inbound order-entry message.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct In {
    pub kind: u8,
    pub cl_ord_id: u64,
    pub new_cl_ord_id: u64,
    pub quote_id: u64,
    pub locate: u16,
    pub stp_group: u16,
    pub side: u8,
    pub tif: u8,
    pub display: u8,
    pub post_only: u8,
    pub stp_mode: u8,
    pub qty: u32,
    pub price: u32,
    pub display_qty: u32,
    pub min_qty: u32,
    pub stop_price: u32,
    pub leave_qty: u32,
    pub bid_price: u32,
    pub bid_qty: u32,
    pub ask_price: u32,
    pub ask_qty: u32,
}

impl Default for In {
    fn default() -> Self {
        In {
            kind: 0,
            cl_ord_id: 0,
            new_cl_ord_id: 0,
            quote_id: 0,
            locate: 0,
            stp_group: 0,
            side: b'B',
            tif: b'D',
            display: b'Y',
            post_only: b'N',
            stp_mode: b'N',
            qty: 0,
            price: 0,
            display_qty: 0,
            min_qty: 0,
            stop_price: 0,
            leave_qty: 0,
            bid_price: 0,
            bid_qty: 0,
            ask_price: 0,
            ask_qty: 0,
        }
    }
}

pub fn in_length(kind: u8) -> usize {
    match kind {
        b'O' => 38,
        b'U' => 25,
        b'X' => 13,
        b'M' => 4,
        b'Q' => 27,
        _ => 0,
    }
}

impl In {
    pub fn encode(&self, b: &mut Vec<u8>) {
        b.push(self.kind);
        match self.kind {
            b'O' => {
                put(b, self.cl_ord_id, 8);
                put(b, u64::from(self.locate), 2);
                b.push(self.side);
                put(b, u64::from(self.qty), 4);
                put(b, u64::from(self.price), 4);
                b.push(self.tif);
                b.push(self.display);
                b.push(self.post_only);
                put(b, u64::from(self.display_qty), 4);
                put(b, u64::from(self.min_qty), 4);
                put(b, u64::from(self.stp_group), 2);
                b.push(self.stp_mode);
                put(b, u64::from(self.stop_price), 4);
            }
            b'U' => {
                put(b, self.cl_ord_id, 8);
                put(b, self.new_cl_ord_id, 8);
                put(b, u64::from(self.qty), 4);
                put(b, u64::from(self.price), 4);
            }
            b'X' => {
                put(b, self.cl_ord_id, 8);
                put(b, u64::from(self.leave_qty), 4);
            }
            b'M' => {
                put(b, u64::from(self.locate), 2);
                b.push(self.side);
            }
            b'Q' => {
                put(b, self.quote_id, 8);
                put(b, u64::from(self.locate), 2);
                put(b, u64::from(self.bid_price), 4);
                put(b, u64::from(self.bid_qty), 4);
                put(b, u64::from(self.ask_price), 4);
                put(b, u64::from(self.ask_qty), 4);
            }
            _ => {}
        }
    }

    pub fn decode(s: &[u8]) -> Result<In, CodecError> {
        let kind = check(s, in_length)?;
        let mut m = In { kind, ..In::default() };
        let u4 = |o: usize| get(s, o, 4) as u32;
        match kind {
            b'O' => {
                m.cl_ord_id = get(s, 1, 8);
                m.locate = get(s, 9, 2) as u16;
                m.side = s[11];
                m.qty = u4(12);
                m.price = u4(16);
                m.tif = s[20];
                m.display = s[21];
                m.post_only = s[22];
                m.display_qty = u4(23);
                m.min_qty = u4(27);
                m.stp_group = get(s, 31, 2) as u16;
                m.stp_mode = s[33];
                m.stop_price = u4(34);
            }
            b'U' => {
                m.cl_ord_id = get(s, 1, 8);
                m.new_cl_ord_id = get(s, 9, 8);
                m.qty = u4(17);
                m.price = u4(21);
            }
            b'X' => {
                m.cl_ord_id = get(s, 1, 8);
                m.leave_qty = u4(9);
            }
            b'M' => {
                m.locate = get(s, 1, 2) as u16;
                m.side = s[3];
            }
            b'Q' => {
                m.quote_id = get(s, 1, 8);
                m.locate = get(s, 9, 2) as u16;
                m.bid_price = u4(11);
                m.bid_qty = u4(15);
                m.ask_price = u4(19);
                m.ask_qty = u4(23);
            }
            _ => {}
        }
        Ok(m)
    }
}

/// An outbound order-entry message (a report).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Out {
    pub kind: u8,
    pub ts: u64,
    pub cl_ord_id: u64,
    pub new_cl_ord_id: u64,
    pub reference: u64,
    pub matched: u64,
    pub locate: u16,
    pub side: u8,
    pub tif: u8,
    pub display: u8,
    pub state: u8,
    pub priority: u8,
    pub reason: u8,
    pub liquidity: u8,
    pub event: u8,
    pub qty: u32,
    pub price: u32,
    pub decrement: u32,
    pub leaves: u32,
    pub fee: i64,
}

impl Default for Out {
    fn default() -> Self {
        Out {
            kind: 0,
            ts: 0,
            cl_ord_id: 0,
            new_cl_ord_id: 0,
            reference: 0,
            matched: 0,
            locate: 0,
            side: b' ',
            tif: b' ',
            display: b' ',
            state: b' ',
            priority: b' ',
            reason: b' ',
            liquidity: b' ',
            event: b' ',
            qty: 0,
            price: 0,
            decrement: 0,
            leaves: 0,
            fee: 0,
        }
    }
}

pub fn out_length(kind: u8) -> usize {
    match kind {
        b'S' => 10,
        b'A' => 39,
        b'U' => 42,
        b'C' => 22,
        b'E' => 46,
        b'J' => 18,
        _ => 0,
    }
}

impl Out {
    pub fn encode(&self, b: &mut Vec<u8>) {
        b.push(self.kind);
        put(b, self.ts, 8);
        match self.kind {
            b'S' => b.push(self.event),
            b'A' => {
                put(b, self.cl_ord_id, 8);
                put(b, self.reference, 8);
                put(b, u64::from(self.locate), 2);
                b.push(self.side);
                put(b, u64::from(self.qty), 4);
                put(b, u64::from(self.price), 4);
                b.push(self.tif);
                b.push(self.display);
                b.push(self.state);
            }
            b'U' => {
                put(b, self.cl_ord_id, 8);
                put(b, self.new_cl_ord_id, 8);
                put(b, self.reference, 8);
                put(b, u64::from(self.qty), 4);
                put(b, u64::from(self.price), 4);
                b.push(self.priority);
            }
            b'C' => {
                put(b, self.cl_ord_id, 8);
                put(b, u64::from(self.decrement), 4);
                b.push(self.reason);
            }
            b'E' => {
                put(b, self.cl_ord_id, 8);
                put(b, u64::from(self.qty), 4);
                put(b, u64::from(self.price), 4);
                put(b, self.matched, 8);
                b.push(self.liquidity);
                put(b, self.fee as u64, 8);
                put(b, u64::from(self.leaves), 4);
            }
            b'J' => {
                put(b, self.cl_ord_id, 8);
                b.push(self.reason);
            }
            _ => {}
        }
    }

    pub fn decode(s: &[u8]) -> Result<Out, CodecError> {
        let kind = check(s, out_length)?;
        let mut m = Out {
            kind,
            ts: get(s, 1, 8),
            ..Out::default()
        };
        let u4 = |o: usize| get(s, o, 4) as u32;
        match kind {
            b'S' => m.event = s[9],
            b'A' => {
                m.cl_ord_id = get(s, 9, 8);
                m.reference = get(s, 17, 8);
                m.locate = get(s, 25, 2) as u16;
                m.side = s[27];
                m.qty = u4(28);
                m.price = u4(32);
                m.tif = s[36];
                m.display = s[37];
                m.state = s[38];
            }
            b'U' => {
                m.cl_ord_id = get(s, 9, 8);
                m.new_cl_ord_id = get(s, 17, 8);
                m.reference = get(s, 25, 8);
                m.qty = u4(33);
                m.price = u4(37);
                m.priority = s[41];
            }
            b'C' => {
                m.cl_ord_id = get(s, 9, 8);
                m.decrement = u4(17);
                m.reason = s[21];
            }
            b'E' => {
                m.cl_ord_id = get(s, 9, 8);
                m.qty = u4(17);
                m.price = u4(21);
                m.matched = get(s, 25, 8);
                m.liquidity = s[33];
                m.fee = get(s, 34, 8) as i64;
                m.leaves = u4(42);
            }
            b'J' => {
                m.cl_ord_id = get(s, 9, 8);
                m.reason = s[17];
            }
            _ => {}
        }
        Ok(m)
    }
}

/// A control message of the engine journal (session 0).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Ctl {
    pub kind: u8,
    pub session: u16,
    pub locate: u16,
    pub firm: u32,
    pub ref_price: u32,
    pub band_lo: u32,
    pub band_hi: u32,
    pub bid: u32,
    pub ask: u32,
    pub cod: u8,
    pub phase: u8,
    pub cross_type: u8,
    pub tif: u8,
    pub freeze: u8,
    pub event: u8,
    pub reason: [u8; 4],
}

pub fn ctl_length(kind: u8) -> usize {
    match kind {
        b'L' => 8,
        b'D' => 3,
        b'P' => 8,
        b'X' | b'I' => 4,
        b'R' => 15,
        b'E' | b'F' => 4,
        b'S' => 2,
        b'N' => 11,
        _ => 0,
    }
}

impl Ctl {
    pub fn encode(&self, b: &mut Vec<u8>) {
        b.push(self.kind);
        match self.kind {
            b'L' => {
                put(b, u64::from(self.session), 2);
                put(b, u64::from(self.firm), 4);
                b.push(self.cod);
            }
            b'D' => put(b, u64::from(self.session), 2),
            b'P' => {
                put(b, u64::from(self.locate), 2);
                b.push(self.phase);
                b.extend_from_slice(&self.reason);
            }
            b'X' | b'I' => {
                put(b, u64::from(self.locate), 2);
                b.push(self.cross_type);
            }
            b'R' => {
                put(b, u64::from(self.locate), 2);
                put(b, u64::from(self.ref_price), 4);
                put(b, u64::from(self.band_lo), 4);
                put(b, u64::from(self.band_hi), 4);
            }
            b'E' => {
                put(b, u64::from(self.locate), 2);
                b.push(self.tif);
            }
            b'F' => {
                put(b, u64::from(self.locate), 2);
                b.push(self.freeze);
            }
            b'S' => b.push(self.event),
            b'N' => {
                put(b, u64::from(self.locate), 2);
                put(b, u64::from(self.bid), 4);
                put(b, u64::from(self.ask), 4);
            }
            _ => {}
        }
    }

    pub fn decode(s: &[u8]) -> Result<Ctl, CodecError> {
        let kind = check(s, ctl_length)?;
        let mut m = Ctl {
            kind,
            session: 0,
            locate: 0,
            firm: 0,
            ref_price: 0,
            band_lo: 0,
            band_hi: 0,
            bid: 0,
            ask: 0,
            cod: b'N',
            phase: b' ',
            cross_type: b' ',
            tif: b' ',
            freeze: b'N',
            event: b' ',
            reason: [b' '; 4],
        };
        match kind {
            b'L' => {
                m.session = get(s, 1, 2) as u16;
                m.firm = get(s, 3, 4) as u32;
                m.cod = s[7];
            }
            b'D' => m.session = get(s, 1, 2) as u16,
            b'P' => {
                m.locate = get(s, 1, 2) as u16;
                m.phase = s[3];
                m.reason.copy_from_slice(&s[4..8]);
            }
            b'X' | b'I' => {
                m.locate = get(s, 1, 2) as u16;
                m.cross_type = s[3];
            }
            b'R' => {
                m.locate = get(s, 1, 2) as u16;
                m.ref_price = get(s, 3, 4) as u32;
                m.band_lo = get(s, 7, 4) as u32;
                m.band_hi = get(s, 11, 4) as u32;
            }
            b'E' => {
                m.locate = get(s, 1, 2) as u16;
                m.tif = s[3];
            }
            b'F' => {
                m.locate = get(s, 1, 2) as u16;
                m.freeze = s[3];
            }
            b'S' => m.event = s[1],
            b'N' => {
                m.locate = get(s, 1, 2) as u16;
                m.bid = get(s, 3, 4) as u32;
                m.ask = get(s, 7, 4) as u32;
            }
            _ => {}
        }
        Ok(m)
    }
}

/// One journal record: (t_ns, session, message).
pub type Record<'a> = (u64, u16, &'a [u8]);

/// Journal records: t_ns u64 | session u16 | length u16 | message.
pub fn journal_records(data: &[u8]) -> Result<Vec<Record<'_>>, CodecError> {
    let mut out = Vec::new();
    let mut i = 0;
    while i + 12 <= data.len() {
        let t = get(data, i, 8);
        let s = get(data, i + 8, 2) as u16;
        let n = get(data, i + 10, 2) as usize;
        if i + 12 + n > data.len() {
            return Err(CodecError::Truncated);
        }
        out.push((t, s, &data[i + 12..i + 12 + n]));
        i += 12 + n;
    }
    Ok(out)
}

/// A MoldUDP64 packet: session alpha10 | seq u64 | count u16 | (u16 length | message)*.
pub fn mold_packet(session: &[u8], seq: u64, msgs: &[Vec<u8>]) -> Vec<u8> {
    let mut b = Vec::new();
    put_alpha(&mut b, session, 10);
    put(&mut b, seq, 8);
    put(&mut b, msgs.len() as u64, 2);
    for m in msgs {
        put(&mut b, m.len() as u64, 2);
        b.extend_from_slice(m);
    }
    b
}

/// Parses a MoldUDP64 packet into (seq, count, messages).
pub fn mold_parse(p: &[u8]) -> Result<(u64, u16, Vec<&[u8]>), CodecError> {
    if p.len() < 20 {
        return Err(CodecError::Truncated);
    }
    let seq = get(p, 10, 8);
    let count = get(p, 18, 2) as u16;
    let mut msgs = Vec::new();
    if count != 0 && count != 0xFFFF {
        let mut i = 20;
        for _ in 0..count {
            if i + 2 > p.len() {
                return Err(CodecError::Truncated);
            }
            let n = get(p, i, 2) as usize;
            if i + 2 + n > p.len() {
                return Err(CodecError::Truncated);
            }
            msgs.push(&p[i + 2..i + 2 + n]);
            i += 2 + n;
        }
    }
    Ok((seq, count, msgs))
}

/// A SoupBinTCP frame: u16 length (type included) | type | payload.
pub fn soup_frame(kind: u8, payload: &[u8]) -> Vec<u8> {
    let mut b = Vec::new();
    put(&mut b, payload.len() as u64 + 1, 2);
    b.push(kind);
    b.extend_from_slice(payload);
    b
}

/// CRC-32 (the zlib polynomial), the W message's book checksum.
pub fn crc32(data: &[u8]) -> u32 {
    let mut c = 0xFFFF_FFFFu32;
    for &byte in data {
        c ^= u32::from(byte);
        for _ in 0..8 {
            c = (c >> 1) ^ (0xEDB8_8320 & 0u32.wrapping_sub(c & 1));
        }
    }
    !c
}

/// Big-endian helpers for the engine and tests.
pub fn be_put(b: &mut Vec<u8>, v: u64, n: usize) {
    put(b, v, n)
}

pub fn be_get(s: &[u8], off: usize, n: usize) -> u64 {
    get(s, off, n)
}
