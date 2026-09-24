//! firm.bond -- fixed-coupon government bonds (build of Chapter 3, One Quant Book 2), Rust twin
//! of firm_bond.py. Dates are civil (year, month, day); day differences use the
//! days-from-civil algorithm, so the crate has no dependencies.

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Date {
    pub y: i32,
    pub m: u32,
    pub d: u32,
}

fn is_leap(y: i32) -> bool {
    (y % 4 == 0 && y % 100 != 0) || y % 400 == 0
}

fn month_len(y: i32, m: u32) -> u32 {
    match m {
        2 if is_leap(y) => 29,
        2 => 28,
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

impl Date {
    pub fn new(y: i32, m: u32, d: u32) -> Date {
        Date { y, m, d }
    }

    /// Days since 1970-01-01 (proleptic Gregorian).
    pub fn serial(self) -> i64 {
        let y = i64::from(self.y) - i64::from(self.m <= 2);
        let era = y.div_euclid(400);
        let yoe = y - era * 400;
        let m = i64::from(self.m);
        let doy = (153 * (if m > 2 { m - 3 } else { m + 9 }) + 2) / 5 + i64::from(self.d) - 1;
        let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
        era * 146_097 + doe - 719_468
    }

    pub fn is_month_end(self) -> bool {
        self.d == month_len(self.y, self.m)
    }

    pub fn add_months(self, n: i32, eom: bool) -> Date {
        let total = self.y * 12 + self.m as i32 - 1 + n;
        let (y, m) = (total.div_euclid(12), total.rem_euclid(12) as u32 + 1);
        let last = month_len(y, m);
        Date::new(y, m, if eom { last } else { self.d.min(last) })
    }
}

fn days_between(a: Date, b: Date) -> f64 {
    (b.serial() - a.serial()) as f64
}

#[derive(Debug)]
pub struct Risk {
    pub dirty: f64,
    pub macaulay: f64,
    pub modified: f64,
    pub dv01: f64,
    pub convexity: f64,
}

pub struct Bond {
    pub coupon: f64,
    pub maturity: Date,
    pub freq: i32,
}

impl Bond {
    /// (previous coupon date, next coupon date, coupons left after settle).
    pub fn locate(&self, settle: Date) -> (Date, Date, i32) {
        let eom = self.maturity.is_month_end();
        let step = 12 / self.freq;
        let (mut d, mut next, mut n) = (self.maturity, self.maturity, 0);
        while d > settle {
            next = d;
            n += 1;
            d = self.maturity.add_months(-step * n, eom);
        }
        (d, next, n)
    }

    fn fraction_to_next(&self, settle: Date) -> (f64, i32) {
        let (prev, next, n) = self.locate(settle);
        (days_between(settle, next) / days_between(prev, next), n)
    }

    pub fn accrued(&self, settle: Date) -> f64 {
        let (w, _) = self.fraction_to_next(settle);
        self.coupon / f64::from(self.freq) * (1.0 - w)
    }

    pub fn dirty_price(&self, y: f64, settle: Date, treasury: bool) -> f64 {
        let (w, n) = self.fraction_to_next(settle);
        let f = f64::from(self.freq);
        let (c, v) = (self.coupon / f, 1.0 / (1.0 + y / f));
        let at_next = (0..n).map(|k| c * v.powi(k)).sum::<f64>() + 100.0 * v.powi(n - 1);
        if treasury {
            at_next / (1.0 + w * y / f)
        } else {
            at_next * v.powf(w)
        }
    }

    pub fn clean_price(&self, y: f64, settle: Date, treasury: bool) -> f64 {
        self.dirty_price(y, settle, treasury) - self.accrued(settle)
    }

    pub fn yield_from_clean(&self, clean: f64, settle: Date) -> f64 {
        let mut y = self.coupon / 100.0;
        for _ in 0..100 {
            let h = 1e-7;
            let f = self.clean_price(y, settle, false) - clean;
            let df = (self.clean_price(y + h, settle, false) - self.clean_price(y - h, settle, false)) / (2.0 * h);
            let step = f / df;
            y -= step;
            if step.abs() < 1e-12 {
                break;
            }
        }
        y
    }

    pub fn risk(&self, y: f64, settle: Date) -> Risk {
        let (w, n) = self.fraction_to_next(settle);
        let f = f64::from(self.freq);
        let (c, v) = (self.coupon / f, 1.0 / (1.0 + y / f));
        let (mut p, mut t1, mut t2) = (0.0, 0.0, 0.0);
        for k in 0..n {
            let t = f64::from(k) + w;
            let pv = (c + if k == n - 1 { 100.0 } else { 0.0 }) * v.powf(t);
            p += pv;
            t1 += t * pv;
            t2 += t * (t + 1.0) * pv;
        }
        let mac = t1 / p / f;
        let modified = mac / (1.0 + y / f);
        let convexity = t2 / p / (f * f) / ((1.0 + y / f) * (1.0 + y / f));
        Risk { dirty: p, macaulay: mac, modified, dv01: p * modified * 1e-4, convexity }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn near(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    #[test]
    fn cfr_example_a() {
        let b = Bond { coupon: 8.75, maturity: Date::new(2020, 5, 15), freq: 2 };
        let s = Date::new(1990, 5, 15);
        assert_eq!(b.accrued(s), 0.0);
        assert!(near(b.clean_price(0.0884, s, true), 99.057893, 5e-7));
        assert!(near(b.clean_price(0.0884, s, false), 99.057893, 5e-7));
    }

    #[test]
    fn cfr_example_d() {
        let b = Bond { coupon: 9.50, maturity: Date::new(1995, 11, 15), freq: 2 };
        let s = Date::new(1985, 11, 29);
        assert!(near(b.accrued(s), 0.367403, 5e-7));
        assert!(near(b.clean_price(0.0954, s, true), 99.730918, 5e-7));
    }

    #[test]
    fn month_end_schedule() {
        let b = Bond { coupon: 4.0, maturity: Date::new(2028, 8, 31), freq: 2 };
        let (prev, next, n) = b.locate(Date::new(2028, 3, 10));
        assert_eq!((prev, next, n), (Date::new(2028, 2, 29), Date::new(2028, 8, 31), 1));
    }

    #[test]
    fn serial_matches_known_differences() {
        assert_eq!(Date::new(1970, 1, 1).serial(), 0);
        assert_eq!(Date::new(2026, 12, 31).serial() - Date::new(2026, 9, 23).serial(), 99);
    }

    #[test]
    fn yield_round_trip_and_dv01() {
        let b = Bond { coupon: 4.25, maturity: Date::new(2036, 8, 15), freq: 2 };
        let s = Date::new(2026, 9, 25);
        assert!(near(b.yield_from_clean(b.clean_price(0.042, s, false), s), 0.042, 1e-12));
        let r = b.risk(0.042, s);
        let bump = (b.dirty_price(0.0419, s, false) - b.dirty_price(0.0421, s, false)) / 2.0;
        assert!(near(r.dv01, bump, 1e-6 * r.dv01));
        assert!(r.modified < r.macaulay && r.convexity > 0.0);
    }
}
