"""Chapter 20 of Book 2: settlement risk. The exposure of a bank's one-day FX book through the
settlement day, gross, after payment netting, and with payment-versus-payment settlement of every
currency but one. Times, currencies' schedules and the book are illustrative; "EMC" stands for an
emerging-market currency outside the PvP system."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/settlerisk"))
from firm_settlerisk import Trade, net_by_counterparty, peak, profile, window

TIMES = {"JPY": (-2.0, 7.0), "EUR": (6.0, 16.0), "GBP": (7.0, 16.0), "USD": (13.0, 21.0), "EMC": (4.0, 12.0)}
PVP = {"JPY", "EUR", "GBP", "USD"}
BOOK = [Trade("A", "EUR", "USD", 400e6), Trade("A", "USD", "EUR", 300e6),
        Trade("B", "JPY", "USD", 250e6), Trade("B", "USD", "JPY", 150e6),
        Trade("C", "EUR", "GBP", 200e6), Trade("C", "USD", "EUR", 100e6),
        Trade("D", "EMC", "USD", 80e6), Trade("D", "USD", "EMC", 50e6)]


def profiles() -> dict[str, list[tuple[float, float]]]:
    net = net_by_counterparty(BOOK)
    return {"gross": profile(BOOK, TIMES), "net": profile(net, TIMES), "pvp": profile(net, TIMES, pvp=PVP)}


def summary() -> dict[str, float]:
    p = profiles()
    herstatt = window(Trade("x", "JPY", "USD", 1.0), TIMES)
    return {"gross_turnover": sum(t.value_usd for t in BOOK),
            "net_payments": sum(t.value_usd for t in net_by_counterparty(BOOK)),
            "peak_gross": peak(p["gross"]), "peak_net": peak(p["net"]), "peak_pvp": peak(p["pvp"]),
            "herstatt_hours": herstatt[1] - herstatt[0]}
