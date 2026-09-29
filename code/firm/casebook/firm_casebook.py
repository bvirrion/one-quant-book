"""firm.casebook -- the public record of the book's case studies as small tables, and the reconstructions and
counterfactuals of chapters 28 and 29 (build of One Quant Book 16, chapters 28-29).

Every figure in a table carries the ledger row that sources it (sources/desk/28-*.md, 29-*.md). Reconstructions
derive monthly returns on capital from the public capital figures; counterfactuals rescale them (half the leverage
halves the return on capital when the assets' returns are unchanged) and rerun Book 7's unwind simulator
(firm.capacity.unwind) for a fund that sells into a crowded exit against one that holds.

API (stable):
    LTCM ; ltcm_returns() ; capital_path(returns, start, scale) ; AMARANTH ; days_to_liquidate(position, adv, share)
    quant_unwind(n, funds, overlap, fraction, days, horizon, seed) -> dict
    KNIGHT ; rescue(equity, loss, new_money, new_shares, old_shares) -> dict
    ARCHEGOS ; exit_race(shares, margins, impact) -> list ; race_impact(loss, share, margin, place, shares_before)
    ftx_balances() -> dict ; ftx_flows() -> dict ; NICKEL ; margin_call(tonnes, p0, p1) ; break_price(tonnes, cash, p0)
"""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "capacity"))
import firm_capacity as cap  # noqa: E402

# Long-Term Capital Management, $ billion (GAO/GGD-00-3; ledger 28 F1-F4).
LTCM = {"nav_1997": 4.67, "returned_1997": 2.7, "nav_aug_1998": 2.3, "august_loss_share": 0.44,
        "recap": 3.6, "recap_share_of_nav": 0.90, "nav_sep30_1998": 3.81, "leverage_1997": 28.0,
        "leverage_1998_end": 21.0, "notional_aug_1998": 1400.0, "august_loss": 1.8}

# Amaranth Advisors, natural gas, 2006 (Senate PSI hearing record, S. Hrg. 110-235; ledger 28 F5-F6).
AMARANTH = {"share_winter_oi": 0.40, "share_nov_2006": 0.75, "share_jan_2007": 0.60, "share_mar_2007": 0.60,
            "max_contracts_month": 100_000, "loss_late_aug_mid_sep": 2.0}


def ltcm_returns():
    """Returns on capital by period, derived from the GAO figures: January to July (from the year-end NAV to the
    end-July NAV implied by August's 44% loss), August, and September to the recapitalisation (the fund's own equity
    implied by the $3.6 billion being 90% of NAV on 28 September)."""
    nav_jul = LTCM["nav_aug_1998"] / (1 - LTCM["august_loss_share"])
    nav_before = LTCM["recap"] / LTCM["recap_share_of_nav"] - LTCM["recap"]
    return {"jan_jul": nav_jul / LTCM["nav_1997"] - 1, "aug": -LTCM["august_loss_share"],
            "sep": nav_before / LTCM["nav_aug_1998"] - 1}


def capital_path(returns, start, scale=1.0):
    """Capital after each period when every period's return on capital is multiplied by `scale`."""
    out, c = [start], start
    for r in returns:
        c *= 1 + scale * r
        out.append(c)
    return out


def days_to_liquidate(position, adv, share=0.2):
    """Days to sell a position trading `share` of the average daily volume."""
    return position / (share * adv)


def quant_unwind(n=200, funds=3, overlap=0.8, fraction=0.5, days=5, horizon=20, seed=28, gross=3e10, adv=5e7,
                 leverage=6.0):
    """Funds with overlapping long-short books (a common component of weight `overlap`) of `gross` dollars each; fund 0
    sells `fraction` of its book over `days` days, the others hold. Cumulative P&L as a fraction of equity (gross
    over leverage) for the seller and a holder."""
    rng = np.random.default_rng(seed)
    common = rng.standard_normal(n)
    books = np.array([overlap * common + (1 - overlap) * rng.standard_normal(n) for _ in range(funds)])
    books /= np.abs(books).sum(axis=1, keepdims=True)
    caps = np.full(funds, gross)
    advs, sigma = np.full(n, adv), np.full(n, 0.02)
    res = cap.unwind(books, caps, 0, fraction, days, advs, sigma, horizon=horizon)
    return {"seller": leverage * res["cum"][:, 0], "holder": leverage * res["cum"][:, 1],
            "overlap": cap.overlap(books[0], books[1])}


# Knight Capital Group, 2012, $ million and million shares (10-Q for Q2 2012; 8-Ks of 6 Aug 2012; ledger 29 F1-F4).
KNIGHT = {"equity_jun_2012": 1496.966, "shares_jun_2012": 97.909, "loss_pretax": 440.0, "new_money": 400.0,
          "new_shares": 266.7, "cash_per_share_2013": 3.75, "kcg_shares_per_share": 1 / 3}

# Archegos, March 2021 (Credit Suisse special committee report; ledger 29 F5-F6): $ billion.
ARCHEGOS = {"gross": 120.0, "long": 70.0, "short": 50.0, "equity": 9.5, "cs_gross_mar23": 27.0, "cs_gross_mar26": 17.0,
            "cs_loss": 5.5, "cs_margin": 0.094, "cs_margin_2020": 0.069}

# LME nickel, March 2022 (Court of Appeal [2024] EWCA Civ 1168; FCA final notice 19 March 2025; ledger 29 F11-F12).
NICKEL = {"close_7mar": 48_078.0, "price_0700_8mar": 80_000.0, "peak_8mar": 101_365.0, "margin_if_stood": 19.75,
          "calls_4mar": 3.5, "calls_7mar_morning": 5.1}

DATA3 = pathlib.Path(__file__).resolve().parents[3] / "data/markets-3"


def rescue(equity, loss, new_money, new_shares, old_shares):
    """Book equity and the old shareholders' stake before the loss, after it, and after a rescue that issues
    `new_shares` for `new_money` (taxes ignored)."""
    after_loss = equity - loss
    after = after_loss + new_money
    old = old_shares / (old_shares + new_shares)
    return {"after_loss": after_loss, "after": after, "old_fraction": old, "old_book": old * after,
            "new_book": (1 - old) * after, "price": new_money / new_shares, "bps_before": equity / old_shares,
            "bps_after_loss": after_loss / old_shares, "bps_after": after / (old_shares + new_shares)}


def exit_race(shares, margins, impact):
    """Brokers holding fractions `shares` of one long position (value 1 at default) sell in turn, in list order,
    under linear permanent impact: the price after a cumulative fraction f is sold is 1 - impact f. Each broker's
    loss per unit of the whole position, net of its margin (fraction of its exposure), floored at zero."""
    out, f = [], 0.0
    for s, m in zip(shares, margins, strict=True):
        avg = 1 - impact * (f + s / 2)                 # average price over its segment
        out.append(max(0.0, s * (1 - avg - m)))
        f += s
    return out


def race_impact(loss_share, share, margin, shares_before):
    """Impact coefficient at which a broker with `share` and `margin`, after `shares_before`
    was sold ahead of it, loses `loss_share` of the whole position."""
    return (loss_share / share + margin) / (shares_before + share / 2)


def _read(name):
    with open(DATA3 / name) as f:
        return list(csv.DictReader(f))


def ftx_balances():
    """FTX.com petition-time payables and located assets, USD million (Book 3's transcription of the debtors'
    table): Category A and all tokens with receivables."""
    rows = _read("ftx_com_petition_balances.csv")
    a = [r for r in rows if r["category"] == "A"]
    pay_a, loc_a = sum(float(r["customer_payables"]) for r in a), sum(float(r["located_assets"]) for r in a)
    pay = sum(float(r["customer_payables"]) for r in rows)
    assets = sum(float(r["located_assets"]) + float(r["customer_receivables"]) for r in rows)
    return {"payables_a": pay_a, "located_a": loc_a, "payables": pay, "assets": assets}


def ftx_flows():
    """Cumulative daily net flows, 1-11 November 2022, USD million: customers and related parties."""
    rows = _read("ftx_com_daily_flows_nov2022.csv")
    cust = np.cumsum([float(r["customer_deposits"]) - float(r["customer_withdrawals"]) for r in rows])
    rel = np.cumsum([float(r["related_deposits"]) - float(r["related_withdrawals"]) for r in rows])
    return {"date": [r["date"] for r in rows], "customers": cust, "related": rel}


def margin_call(tonnes, p0, p1):
    """Variation margin owed by a short of `tonnes` when the price moves from p0 to p1 ($)."""
    return tonnes * (p1 - p0)


def break_price(tonnes, cash, p0):
    """The price at which a short's variation margin exhausts `cash`."""
    return p0 + cash / tonnes
