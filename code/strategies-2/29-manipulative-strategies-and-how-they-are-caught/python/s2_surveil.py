"""Manipulative strategies and how they are caught (One Quant Book 9, chapter 29).

Synthetic: firm.surveil's account-days (11,600 for spoofing, with 100 planted episodes; 5,600 for the close, 100
planted; 5,100 for wash trades, 100 planted), each detector's true-positive rate at a 1% false-positive rate, the
share of each legitimate type it flags, and the spoofing detectors' ROC curves. No manipulation's profitability is
modelled. NumPy.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "surveil"))
from firm_surveil import (  # noqa: E402
    close_days,
    close_scores,
    flagged_by_type,
    spoof_scores,
    spoofing_days,
    tpr_at_fpr,
    wash_days,
    wash_scores,
)

FPR = 0.01


@functools.lru_cache(maxsize=1)
def data() -> dict:
    return {"spoof": spoofing_days(), "close": close_days(), "wash": wash_days()}


def detectors() -> dict:
    """For each family and detector: true-positive rate at a 1% false-positive rate, and the share of each account type
    flagged."""
    d = data()
    out = {}
    for fam, scorer in (("spoof", spoof_scores), ("close", close_scores), ("wash", wash_scores)):
        out[fam] = {name: {"tpr": tpr_at_fpr(s, d[fam]["label"], FPR)["tpr"],
                           "by_type": flagged_by_type(s, d[fam], FPR).tolist()} for name, s in scorer(d[fam]).items()}
    return out


FPRS = tuple(float(x) for x in np.round(np.geomspace(0.001, 0.5, 16), 4))


def roc(fprs=FPRS) -> dict:
    """The spoofing detectors' true-positive rate against the false-positive rate."""
    d = data()["spoof"]
    return {name: [tpr_at_fpr(s, d["label"], f)["tpr"] for f in fprs] for name, s in spoof_scores(d).items()} | {
        "fpr": list(fprs)}


def counts() -> dict:
    d = data()
    return {fam: (len(v["label"]), int(v["label"].sum())) for fam, v in d.items()}
