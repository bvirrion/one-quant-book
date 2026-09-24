"""Model risk management tooling (build of One Quant Book 6, chapter 26).

- A model inventory: records with owner, use, tier, validation status and known limitations; a tiering
  rule from materiality, complexity and uncertainty scores (1 to 3 each), and the validation interval
  the tier implies (an illustrative policy).
- A benchmarking harness: run a candidate implementation against an independent benchmark over a
  parameter grid with absolute and relative tolerances, record every point, summarise failures.
- Outcomes analysis: a binomial test of exception counts.
- The two ways of computing a relative change, the intended one and the one in the spreadsheet of
  JPMorgan's 2012 VaR model (dividing by the sum instead of the average of the old and new values).
"""
import itertools
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field


@dataclass
class ModelRecord:
    model_id: str
    name: str
    owner: str
    use: str
    materiality: int          # 1 low .. 3 high (capital, P&L, reporting impact)
    complexity: int           # 1 .. 3
    uncertainty: int          # 1 .. 3 (inputs, assumptions, data)
    status: str = "validated"
    limitations: list[str] = field(default_factory=list)

    @property
    def tier(self) -> int:
        score = self.materiality * 2 + self.complexity + self.uncertainty
        return 1 if score >= 10 else (2 if score >= 7 else 3)

    @property
    def revalidate_years(self) -> int:
        return {1: 1, 2: 2, 3: 3}[self.tier]


def inventory_summary(records: Sequence[ModelRecord]) -> dict:
    out = {1: 0, 2: 0, 3: 0}
    for r in records:
        out[r.tier] += 1
    return out


@dataclass
class BenchmarkResult:
    params: dict
    candidate: float
    benchmark: float
    abs_err: float
    rel_err: float
    passed: bool


def benchmark(candidate: Callable[..., float], reference: Callable[..., float], grid: dict[str, Sequence],
              abs_tol: float, rel_tol: float) -> list[BenchmarkResult]:
    """Evaluate both on every combination of the grid; a point passes if within abs_tol or rel_tol."""
    keys = list(grid)
    out = []
    for combo in itertools.product(*(grid[k] for k in keys)):
        p = dict(zip(keys, combo, strict=True))
        c, b = candidate(**p), reference(**p)
        ae = abs(c - b)
        re_ = ae / abs(b) if b != 0 else math.inf
        out.append(BenchmarkResult(p, c, b, ae, re_, ae <= abs_tol or re_ <= rel_tol))
    return out


def summary(results: Sequence[BenchmarkResult]) -> dict:
    fails = [r for r in results if not r.passed]
    return {"points": len(results), "failures": len(fails), "max_abs": max(r.abs_err for r in results),
            "max_rel": max(r.rel_err for r in results if math.isfinite(r.rel_err)), "failed": fails}


def binomial_tail(n: int, k: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))


def relative_change(new: float, old: float, error: bool = False) -> float:
    """(new - old) / average(new, old) as intended; divided by the sum when `error` (the 2012 spreadsheet)."""
    return (new - old) / ((new + old) if error else 0.5 * (new + old))
