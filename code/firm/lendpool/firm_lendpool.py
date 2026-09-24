"""Lending pool engine (build of Book 3, Chapter 23).

One reserve per asset with supply and borrow indices accruing at a kinked rate in utilisation;
accounts with collateral and debt; the health factor; liquidation with a close factor and a bonus;
and flash loans that must be repaid, with a fee, before the call returns or the whole call is undone.
Amounts in units of each asset, prices in dollars, time in years.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RateModel:
    base: float
    slope1: float
    slope2: float
    optimal: float

    def borrow_rate(self, u: float) -> float:
        """Kinked: base + slope1 u/u* below the kink, then slope2 on the excess over it."""
        if u <= self.optimal:
            return self.base + self.slope1 * u / self.optimal
        return self.base + self.slope1 + self.slope2 * (u - self.optimal) / (1 - self.optimal)


@dataclass
class Reserve:
    model: RateModel
    reserve_factor: float = 0.1
    supplied: float = 0.0          # principal in today's units: supply balance = scaled x index
    borrowed: float = 0.0
    supply_index: float = 1.0
    borrow_index: float = 1.0

    def utilisation(self) -> float:
        s = self.supplied * self.supply_index
        return 0.0 if s == 0 else self.borrowed * self.borrow_index / s

    def rates(self) -> tuple[float, float]:
        u = self.utilisation()
        rb = self.model.borrow_rate(u)
        return rb, rb * u * (1 - self.reserve_factor)

    def accrue(self, dt: float) -> None:
        rb, rs = self.rates()
        self.borrow_index *= 1 + rb * dt
        self.supply_index *= 1 + rs * dt

    def available(self) -> float:
        return self.supplied * self.supply_index - self.borrowed * self.borrow_index


@dataclass
class Account:
    collateral: dict = field(default_factory=dict)     # asset -> amount
    debt: dict = field(default_factory=dict)           # asset -> scaled debt (x borrow index = owed)


@dataclass
class Pool:
    reserves: dict
    prices: dict
    ltv: dict                   # borrowing power per dollar of collateral
    threshold: dict             # liquidation threshold per dollar of collateral
    bonus: dict                 # liquidation bonus on the collateral seized
    close_factor: float = 0.5
    flash_fee: float = 0.0005

    def owed(self, acct: Account, asset: str) -> float:
        return acct.debt.get(asset, 0.0) * self.reserves[asset].borrow_index

    def debt_value(self, acct: Account) -> float:
        return sum(self.owed(acct, a) * self.prices[a] for a in acct.debt)

    def health(self, acct: Account) -> float:
        d = self.debt_value(acct)
        c = sum(q * self.prices[a] * self.threshold[a] for a, q in acct.collateral.items())
        return float("inf") if d == 0 else c / d

    def supply(self, asset: str, amount: float) -> None:
        r = self.reserves[asset]
        r.supplied += amount / r.supply_index

    def borrow(self, acct: Account, asset: str, amount: float) -> None:
        power = sum(q * self.prices[a] * self.ltv[a] for a, q in acct.collateral.items())
        if self.debt_value(acct) + amount * self.prices[asset] > power:
            raise ValueError("borrow exceeds loan-to-value")
        r = self.reserves[asset]
        if amount > r.available():
            raise ValueError("insufficient liquidity")
        r.borrowed += amount / r.borrow_index
        acct.debt[asset] = acct.debt.get(asset, 0.0) + amount / r.borrow_index

    def liquidate(self, acct: Account, debt_asset: str, coll_asset: str, repay: float) -> float:
        """Repay up to the close factor of the debt of an account whose health is below one; returns the
        collateral seized, worth the repayment plus the bonus."""
        if self.health(acct) >= 1:
            raise ValueError("account is healthy")
        repay = min(repay, self.close_factor * self.owed(acct, debt_asset))
        seize = repay * self.prices[debt_asset] / self.prices[coll_asset] * (1 + self.bonus[coll_asset])
        seize = min(seize, acct.collateral[coll_asset])
        r = self.reserves[debt_asset]
        acct.debt[debt_asset] -= repay / r.borrow_index
        r.borrowed -= repay / r.borrow_index
        acct.collateral[coll_asset] -= seize
        return seize

    def flash_loan(self, asset: str, amount: float, callback) -> float:
        """Lend `amount`; `callback(amount)` must return at least amount x (1 + fee), else the loan reverts
        (raises) and nothing happened. Returns the fee earned by the reserve's suppliers."""
        r = self.reserves[asset]
        if amount > r.available():
            raise ValueError("insufficient liquidity")
        repaid = callback(amount)
        due = amount * (1 + self.flash_fee)
        if repaid < due:
            raise ValueError("flash loan not repaid: transaction reverts")
        fee = repaid - amount
        r.supplied += fee / r.supply_index
        return fee
