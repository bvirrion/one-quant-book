"""Chapter 22 helpers: the 2012 incident's totals (SEC Release 34-70694, paragraph 17), the runaway's rates derived
from them, and the runs behind the chapter's table and figure.

KNIGHT            the order's totals: executions, shares, minutes, net long and short positions, loss (dollars)
rate_per_s()      executions a second over the 45 minutes
per_45_minutes(x_per_s)   a rate carried over the incident's duration
runs(seconds)     {config: firm_riskgate_runaway.Stats} for every configuration of the chapter's table
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/riskgate"))
import firm_riskgate as rg  # noqa: E402,F401
import firm_riskgate_runaway as ra  # noqa: E402

KNIGHT = {"executions": 4_000_000, "stocks": 154, "shares": 397_000_000, "minutes": 45,
          "long_usd": 3.5e9, "short_usd": 3.15e9, "loss_usd": 460e6, "parents": 212}
SECONDS = 5.0


def rate_per_s():
    return KNIGHT["executions"] / (KNIGHT["minutes"] * 60)


def shares_per_execution():
    return KNIGHT["shares"] / KNIGHT["executions"]


def per_45_minutes(x_per_s):
    return x_per_s * KNIGHT["minutes"] * 60


def runs(seconds=SECONDS):
    return {k: ra.run(c, seconds) for k, c in ra.CONFIGS.items()}
