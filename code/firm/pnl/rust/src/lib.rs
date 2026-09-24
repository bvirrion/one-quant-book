//! firm.pnl -- position and P&L keeper (build of Chapter 7, One Quant Book 1).
//! Exact part in integers (ledger units); the realised / unrealised split in f64.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Side {
    Buy,
    Sell,
}

impl Side {
    fn sign(self) -> i64 {
        match self {
            Side::Buy => 1,
            Side::Sell => -1,
        }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct BadFill;

#[derive(Clone, Debug, Default)]
pub struct Position {
    pub quantity: i64,
    pub cash: i64,
    pub fees: i64,
    pub avg_cost: f64,
    pub realised: f64,
}

impl Position {
    pub fn on_fill(&mut self, side: Side, qty: i64, price: i64, fee: i64) -> Result<(), BadFill> {
        if qty <= 0 || price <= 0 || fee < 0 {
            return Err(BadFill);
        }
        let signed = side.sign() * qty;
        self.cash -= signed * price;
        self.fees += fee;
        let adding = self.quantity == 0 || (self.quantity > 0) == (signed > 0);
        if adding {
            let open = self.quantity.abs();
            self.avg_cost = (open as f64 * self.avg_cost + (qty * price) as f64) / (open + qty) as f64;
            self.quantity += signed;
            return Ok(());
        }
        let closing = qty.min(self.quantity.abs());
        let direction = if self.quantity > 0 { 1.0 } else { -1.0 };
        self.realised += direction * closing as f64 * (price as f64 - self.avg_cost);
        self.quantity += signed;
        if qty > closing {
            self.avg_cost = price as f64; // flipped: the remainder opens at the fill price
        } else if self.quantity == 0 {
            self.avg_cost = 0.0;
        }
        Ok(())
    }

    pub fn unrealised(&self, mark: i64) -> f64 {
        self.quantity as f64 * (mark as f64 - self.avg_cost)
    }

    /// Exact: value of the position plus every cash flow so far, less fees.
    pub fn total(&self, mark: i64) -> i64 {
        self.cash + self.quantity * mark - self.fees
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trip() {
        let mut p = Position::default();
        p.on_fill(Side::Buy, 100, 500_000, 0).unwrap();
        p.on_fill(Side::Sell, 100, 501_200, 0).unwrap();
        assert_eq!((p.quantity, p.total(1)), (0, 120_000));
        assert!((p.realised - 120_000.0).abs() < 1e-6);
    }

    #[test]
    fn flip_opens_remainder_at_fill_price() {
        let mut p = Position::default();
        p.on_fill(Side::Buy, 100, 500_000, 0).unwrap();
        p.on_fill(Side::Sell, 250, 498_000, 0).unwrap();
        assert_eq!(p.quantity, -150);
        assert!((p.avg_cost - 498_000.0).abs() < 1e-6 && (p.realised + 200_000.0).abs() < 1e-6);
        assert!((p.unrealised(497_000) - 150_000.0).abs() < 1e-6);
    }

    #[test]
    fn split_adds_up_to_exact_total() {
        let mut p = Position::default();
        let mut x: u64 = 7;
        for _ in 0..5000 {
            x = x.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            let side = if (x >> 33) & 1 == 1 { Side::Buy } else { Side::Sell };
            let qty = (1 + (x >> 40) % 8) as i64 * 100;
            let price = 499_000 + ((x >> 20) % 2000) as i64;
            p.on_fill(side, qty, price, ((x >> 10) % 50) as i64).unwrap();
        }
        let mark = 500_250;
        let split = p.realised + p.unrealised(mark) - p.fees as f64;
        assert!((split - p.total(mark) as f64).abs() < 1.0);
    }

    #[test]
    fn rejects_bad_fills() {
        assert_eq!(Position::default().on_fill(Side::Buy, 0, 1, 0), Err(BadFill));
    }
}
