//! firm.simdscan -- byte scanning and digit parsing with vector instructions (build of One Quant Book 13, chapter
//! 14), the Rust twin of `firm_simdscan.hpp`. The AVX2 functions are compiled for AVX2 alone (`target_feature`) and
//! called only after a run-time check; every function equals its scalar reference and never reads past the slice.

/// Index of the first `c` in `s`, or `s.len()`.
pub fn find_byte_scalar(s: &[u8], c: u8) -> usize {
    s.iter().position(|&b| b == c).unwrap_or(s.len())
}

/// Every index of `c` in `s`, in order.
pub fn positions_scalar(s: &[u8], c: u8, out: &mut Vec<u32>) {
    out.extend(s.iter().enumerate().filter(|(_, &b)| b == c).map(|(i, _)| i as u32));
}

#[cfg(target_arch = "x86_64")]
mod x86 {
    use std::arch::x86_64::*;

    pub fn find_byte_sse2(s: &[u8], c: u8) -> usize {
        let n = s.len();
        if n < 16 {
            return super::find_byte_scalar(s, c);
        }
        let mut i = 0;
        // SAFETY: SSE2 is part of every x86-64 CPU; every load reads 16 bytes inside `s` (the last one ends at n).
        unsafe {
            let needle = _mm_set1_epi8(c as i8);
            while i < n {
                let at = if i + 16 <= n { i } else { n - 16 };
                let v = _mm_loadu_si128(s.as_ptr().add(at) as *const __m128i);
                let m = (_mm_movemask_epi8(_mm_cmpeq_epi8(v, needle)) as u32) >> (i - at);
                if m != 0 {
                    return i + m.trailing_zeros() as usize;
                }
                i += 16;
            }
        }
        n
    }

    /// # Safety
    /// The CPU must support AVX2 (check with `is_x86_feature_detected!("avx2")`).
    #[target_feature(enable = "avx2")]
    pub unsafe fn find_byte_avx2(s: &[u8], c: u8) -> usize {
        let n = s.len();
        if n < 32 {
            return find_byte_sse2(s, c);
        }
        let needle = _mm256_set1_epi8(c as i8);
        let mut i = 0;
        while i < n {
            let at = if i + 32 <= n { i } else { n - 32 }; // the last block overlaps the previous one
            let v = _mm256_loadu_si256(s.as_ptr().add(at) as *const __m256i);
            let m = (_mm256_movemask_epi8(_mm256_cmpeq_epi8(v, needle)) as u32) >> (i - at);
            if m != 0 {
                return i + m.trailing_zeros() as usize;
            }
            i += 32;
        }
        n
    }

    /// # Safety
    /// The CPU must support AVX2.
    #[target_feature(enable = "avx2")]
    pub unsafe fn positions_avx2(s: &[u8], c: u8, out: &mut Vec<u32>) {
        let n = s.len();
        if n < 32 {
            return super::positions_scalar(s, c, out);
        }
        let needle = _mm256_set1_epi8(c as i8);
        let mut i = 0;
        while i < n {
            let at = if i + 32 <= n { i } else { n - 32 };
            let v = _mm256_loadu_si256(s.as_ptr().add(at) as *const __m256i);
            let mut m = (_mm256_movemask_epi8(_mm256_cmpeq_epi8(v, needle)) as u32) >> (i - at);
            while m != 0 {
                out.push((i + m.trailing_zeros() as usize) as u32);
                m &= m - 1;
            }
            i += 32;
        }
    }
}

/// The widest implementation this CPU supports, chosen at every call (the check is a cached load).
pub fn find_byte(s: &[u8], c: u8) -> usize {
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("avx2") {
            // SAFETY: the running CPU supports AVX2, checked just above.
            return unsafe { x86::find_byte_avx2(s, c) };
        }
        x86::find_byte_sse2(s, c)
    }
    #[cfg(not(target_arch = "x86_64"))]
    find_byte_scalar(s, c)
}

pub fn positions(s: &[u8], c: u8, out: &mut Vec<u32>) {
    #[cfg(target_arch = "x86_64")]
    if is_x86_feature_detected!("avx2") {
        // SAFETY: AVX2 checked at run time.
        return unsafe { x86::positions_avx2(s, c, out) };
    }
    positions_scalar(s, c, out)
}

#[cfg(target_arch = "x86_64")]
pub use x86::find_byte_sse2;

/// Eight ASCII digits, scalar.
pub fn parse8_scalar(d: &[u8; 8]) -> u32 {
    d.iter().fold(0u32, |v, &b| v * 10 + (b - b'0') as u32)
}

/// True when all eight bytes are ASCII digits.
pub fn is8digits(d: &[u8; 8]) -> bool {
    let v = u64::from_le_bytes(*d);
    ((v & 0xF0F0F0F0F0F0F0F0) | (((v.wrapping_add(0x0606060606060606)) & 0xF0F0F0F0F0F0F0F0) >> 4))
        == 0x3333333333333333
}

/// Eight ASCII digits in one 64-bit register: pairs, then quads, then the whole (see the C++ twin).
pub fn parse8_swar(d: &[u8; 8]) -> u32 {
    let mut v = u64::from_le_bytes(*d).wrapping_sub(0x3030303030303030);
    v = (v.wrapping_mul(10) + (v >> 8)) & 0x00FF00FF00FF00FF;
    v = (v.wrapping_mul(100) + (v >> 16)) & 0x0000FFFF0000FFFF;
    v = (v.wrapping_mul(10000) + (v >> 32)) & 0xFFFFFFFF;
    v as u32
}

/// Unsigned integer of up to 19 digits at the start of `s`: (value, digits used), or None if no digit.
pub fn parse_uint(s: &[u8]) -> Option<(u64, usize)> {
    let (mut v, mut i) = (0u64, 0usize);
    while i + 8 <= s.len() && i + 8 <= 19 {
        let d: &[u8; 8] = s[i..i + 8].try_into().ok()?;
        if !is8digits(d) {
            break;
        }
        v = v * 100_000_000 + parse8_swar(d) as u64;
        i += 8;
    }
    while i < s.len() && i < 19 && s[i].is_ascii_digit() {
        v = v * 10 + (s[i] - b'0') as u64;
        i += 1;
    }
    (i > 0).then_some((v, i))
}

/// A decimal price as an integer number of 10^-scale units, with the C++ twin's rules.
pub fn parse_fixed(s: &[u8], scale: u32) -> Option<i64> {
    let neg = s.first() == Some(&b'-');
    let mut i = neg as usize;
    let (ip, used) = parse_uint(&s[i..])?;
    i += used;
    let (mut fp, mut decimals) = (0u64, 0u32);
    if s.get(i) == Some(&b'.') {
        i += 1;
        if let Some((f, u)) = parse_uint(&s[i..]) {
            fp = f;
            decimals = u as u32;
            i += u;
        }
    }
    if i != s.len() || decimals > scale {
        return None;
    }
    let v = (ip * 10u64.pow(scale) + fp * 10u64.pow(scale - decimals)) as i64;
    Some(if neg { -v } else { v })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn lcg(x: &mut u64) -> u64 {
        *x = x.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        *x >> 33
    }

    #[test]
    fn scans_equal_scalar_for_every_length() {
        let mut seed = 7u64;
        for n in 0..=200usize {
            for trial in 0..20 {
                let mut s: Vec<u8> = (0..n).map(|_| b'A' + (lcg(&mut seed) % 20) as u8).collect();
                if n > 0 && trial % 2 == 0 {
                    for _ in 0..1 + trial / 4 {
                        let k = (lcg(&mut seed) as usize) % n;
                        s[k] = 1;
                    }
                }
                let want = find_byte_scalar(&s, 1);
                assert_eq!(find_byte(&s, 1), want);
                #[cfg(target_arch = "x86_64")]
                assert_eq!(find_byte_sse2(&s, 1), want);
                let (mut a, mut b) = (Vec::new(), Vec::new());
                positions_scalar(&s, 1, &mut a);
                positions(&s, 1, &mut b);
                assert_eq!(a, b);
            }
        }
    }

    #[test]
    fn eight_digits() {
        let mut seed = 11u64;
        for t in 0..200_000u64 {
            let v = match t {
                0 => 0,
                1 => 99_999_999,
                _ => lcg(&mut seed) % 100_000_000,
            };
            let s = format!("{v:08}");
            let d: &[u8; 8] = s.as_bytes().try_into().unwrap();
            assert!(is8digits(d));
            assert_eq!(parse8_scalar(d), v as u32);
            assert_eq!(parse8_swar(d), v as u32);
        }
        assert!(!is8digits(b"1234567a") && !is8digits(b"12/45678"));
    }

    #[test]
    fn integers_and_prices_match_the_cpp_twin() {
        assert_eq!(parse_uint(b"1234567890123456789x"), Some((1234567890123456789, 19)));
        assert_eq!(parse_uint(b"x1"), None);
        assert_eq!(parse_fixed(b"123.4567", 6), Some(123456700));
        assert_eq!(parse_fixed(b"-0.05", 4), Some(-500));
        assert_eq!(parse_fixed(b"17.", 2), Some(1700));
        assert_eq!(parse_fixed(b"1.234", 2), None);
        assert_eq!(parse_fixed(b".5", 2), None);
    }
}
