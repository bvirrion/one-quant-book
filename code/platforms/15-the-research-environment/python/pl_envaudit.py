"""The research environment (One Quant Book 15, chapter 15).

A planted notebook computes a headline number -- the average real growth of country-years with public debt above 90%
of output, averaged by country -- from a synthetic panel of twenty countries. Its history is written down: a cell that
excluded five countries was run and then deleted, and a cleaning cell placed near the top was run last. The notebook
as saved shows the number that history produced. The chapter audits the document, reruns it from the top in a fresh
interpreter (it fails), fixes it, promotes the calculation to a tested library function, and reproduces the corrected
number from a clean directory with the data snapshot and the environment lock checked.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/envaudit"))
import firm_envaudit as E  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import research_lib as lib  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EXCLUDED = ["C01", "C02", "C03", "C04", "C05"]


def panel(seed: int = 15) -> pd.DataFrame:
    """Twenty countries, 1946-2009: debt/GDP a persistent random walk, growth falling mildly with debt."""
    rng = np.random.default_rng(seed)
    rows = []
    for c in range(1, 21):
        debt = 40.0 + 60.0 * rng.random() + (40.0 if c <= 5 else 0.0)
        for y in range(1946, 2010):
            debt = max(5.0, debt + rng.normal(0, 6))
            g = 3.5 - 0.012 * debt + rng.normal(0, 2.5) + (1.5 if c <= 5 else 0.0)
            rows.append((f"C{c:02d}", y, round(debt, 1), round(g, 2)))
    return pd.DataFrame(rows, columns=["country", "year", "debt", "growth"])


CELLS = {                       # the notebook's code cells, in document order
    "load": 'import pandas as pd\ndf = pd.read_csv("panel.csv")',
    "clean": "df = df[df.year >= 1950]",
    "high": "high = df[df.debt > 90]",
    "select": "sel = high[~high.country.isin(exclude)]",
    "result": 'result = sel.groupby("country").growth.mean().mean()\n'
              'print(f"{result:.2f}")',
}
DELETED = f"exclude = {EXCLUDED!r}"
HISTORY = ["load", "high", "DELETED", "select", "result", "clean"]    # what ran, in that order


def planted(workdir: pathlib.Path) -> dict:
    """Write panel.csv and the notebook as its history left it (outputs from that history)."""
    workdir.mkdir(parents=True, exist_ok=True)
    panel().to_csv(workdir / "panel.csv", index=False)
    ns: dict = {}
    counter, outputs, count = 0, {}, {}
    import contextlib
    import io
    import os
    cwd = os.getcwd()
    os.chdir(workdir)
    try:
        for name in HISTORY:
            counter += 1
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                exec(DELETED if name == "DELETED" else CELLS[name], ns)
            if name != "DELETED":
                count[name], outputs[name] = counter, buf.getvalue()
    finally:
        os.chdir(cwd)
    cells = [{"cell_type": "markdown", "metadata": {}, "source": "# Growth and public debt"}]
    for name, src in CELLS.items():
        out = [{"output_type": "stream", "name": "stdout", "text": outputs[name]}] if outputs[name] else []
        cells.append({"cell_type": "code", "metadata": {}, "source": src, "execution_count": count[name],
                      "outputs": out})
    nb = {"nbformat": 4, "nbformat_minor": 5, "metadata": {"kernelspec": {"name": "python3"}}, "cells": cells}
    (workdir / "analysis.ipynb").write_text(json.dumps(nb, indent=1))
    return nb


def fixed(nb: dict) -> dict:
    """The fix: no exclusion; the cells as they stand, top to bottom."""
    nb = json.loads(json.dumps(nb))
    for c in nb["cells"]:
        if c["cell_type"] == "code" and "exclude" in E._source(c):
            c["source"] = "sel = high"
        if c["cell_type"] == "code":
            c["execution_count"], c["outputs"] = None, []
    return nb


def study(workdir: pathlib.Path) -> dict:
    nb = planted(workdir)
    result_cell = 1 + list(CELLS).index("result")
    saved = E.saved_output(nb, result_cell).strip()
    findings = E.audit(nb)
    first = E.rerun(nb, workdir)
    corrected = E.rerun(fixed(nb), workdir)
    df = panel()
    return {"saved": saved, "findings": findings, "rerun_ok": first.ok,
            "rerun_error": first.stderr.strip().splitlines()[-1],
            "corrected": corrected.stdout.strip(),
            "library": f"{lib.average_growth(df, 90, since=1950):.2f}",
            "library_excluding": f"{lib.average_growth(df, 90, exclude=EXCLUDED):.2f}",
            "pooled": f"{lib.average_growth(df, 90, since=1950, weight='country-year'):.2f}",
            "country_years": int(((df.debt > 90) & (df.year >= 1950)).sum())}


def reproduce(clean_dir: pathlib.Path, source_dir: pathlib.Path) -> dict:
    """From a clean directory: the promoted script, the data snapshot and the lock; check all three, then run."""
    if clean_dir.exists():
        shutil.rmtree(clean_dir)
    clean_dir.mkdir(parents=True)
    shutil.copy(source_dir / "panel.csv", clean_dir / "panel.csv")
    shutil.copy(HERE / "research_lib.py", clean_dir / "research_lib.py")
    manifest = E.snapshot([source_dir / "panel.csv"])
    data_diffs = E.check_snapshot([clean_dir / "panel.csv"], manifest)
    env_diffs = E.compare_env(E.capture_env(), (ROOT / "requirements.txt").read_text())
    script = clean_dir / "headline.py"
    script.write_text("import pandas as pd\nfrom research_lib import average_growth\n"
                      "print(f\"{average_growth(pd.read_csv('panel.csv'), 90, since=1950):.2f}\")\n")
    import subprocess
    r = subprocess.run([sys.executable, str(script)], cwd=clean_dir, capture_output=True, text=True, check=True)
    return {"result": r.stdout.strip(), "data_diffs": data_diffs, "env_diffs": env_diffs, "manifest": manifest}
