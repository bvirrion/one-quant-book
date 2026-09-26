"""Writes data/limits.json: an example limits snapshot in firm.riskctl's schema with its firm.riskgate section, the
fixture One Quant Book 13's gate replays (its from_riskctl reads the "riskgate" key)."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import firm_riskctl as rc  # noqa: E402

LIMITS = {
    "version": 1,
    "gate": {"max_age_ns": 1_000_000_000, "ref_max_age_ns": 500_000_000, "dup_ns": 100_000_000},
    "firm": {"max_gross_usd": 1.0e9, "max_loss_usd": 5.0e6, "max_msgs_per_s": 5000},
    "desks": {"equity_mm": {"max_gross_usd": 6.0e8, "max_loss_usd": 3.0e6},
              "etf_mm": {"max_gross_usd": 4.0e8, "max_loss_usd": 2.0e6}},
    "strategies": {"quoter_a": {"desk": "equity_mm", "rate": 500, "burst": 50, "max_open": 400, "max_loss_usd": 1.0e6,
                                "max_position_usd": 2.5e8},
                   "quoter_b": {"desk": "equity_mm", "rate": 300, "burst": 30, "max_open": 200, "max_loss_usd": 5.0e5,
                                "max_position_usd": 1.0e8},
                   "etf_arb": {"desk": "etf_mm", "rate": 200, "burst": 20, "max_open": 100, "max_loss_usd": 1.0e6,
                               "max_position_usd": 2.0e8}},
    "instruments": {"1": {"collar_bp": 500, "max_qty": 5000, "max_notional_usd": 5.0e5, "max_long": 50000,
                          "max_short": 50000},
                    "2": {"collar_bp": 300, "max_qty": 2000, "max_notional_usd": 4.0e5, "max_long": 20000,
                          "max_short": 20000},
                    "3": {"collar_bp": 1000, "max_qty": 10000, "max_notional_usd": 2.0e5, "max_long": 100000,
                          "max_short": 100000}},
}

if __name__ == "__main__":
    (HERE / "data" / "limits.json").write_text(json.dumps(rc.export(LIMITS), indent=1, sort_keys=True) + "\n")
    print("wrote data/limits.json")
