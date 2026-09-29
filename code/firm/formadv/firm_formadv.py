"""firm.formadv -- the SEC's Form ADV adviser file as data (build of One Quant Book 17, chapter 4).

The SEC publishes, roughly monthly, one CSV row per registered investment adviser with the answers to Form ADV Part 1A
(the "firm roster" download). This module streams it from its zip, keeps a handful of items, and computes per-head
measures and concentration. Items read (Form ADV Part 1A):
    5A       approximate number of employees
    5B(1)    of whom perform investment advisory functions (including research)
    5F(2)(c) regulatory assets under management, total (gross: no deduction of indebtedness)
    7B       private funds advised: "Any Hedge Funds", "Total number of Hedge funds",
             "Total Gross Assets of Private Funds"
Nothing is written back; raw files stay outside the repository.

API (stable):
    Adviser(crd, name, employees, advisory, raum, pf_gav, n_hedge, filed)
    read(path_or_fileobj, hedge_only=True) -> list[Adviser]     a .zip (CSV or xlsx inside), a .csv or a .xlsx;
                                    files before 2023 have no hedge-fund columns: those fields are None and
                                    hedge_only must be False
    per_head(a) -> dict             RAUM per employee and per advisory employee, advisory share
    quantiles(values, qs) -> list
    concentration(values, k=10) -> (top-k share, HHI on 0-10,000)   wraps firm.moats
"""
import csv
import io
import pathlib
import sys
import zipfile
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "moats"))
import firm_moats as moats  # noqa: E402

COLS = {"crd": "Organization CRD#", "name": "Primary Business Name", "employees": "5A", "advisory": "5B(1)",
        "raum": "5F(2)(c)", "any_hedge": "Any Hedge Funds", "n_hedge": "Total number of Hedge funds",
        "pf_gav": "Total Gross Assets of Private Funds", "filed": "Latest ADV Filing Date"}


@dataclass(frozen=True)
class Adviser:
    crd: str
    name: str
    employees: float | None
    advisory: float | None
    raum: float | None
    pf_gav: float | None
    n_hedge: float | None
    filed: str


def _num(x):
    x = (x or "").replace(",", "").replace("$", "").strip()
    try:
        return float(x)
    except ValueError:
        return None


def _xlsx(fileobj):
    import openpyxl  # read_only: the workbook is streamed row by row
    ws = openpyxl.load_workbook(fileobj, read_only=True).worksheets[0]
    for row in ws.iter_rows(values_only=True):
        yield ["" if v is None else str(v) for v in row]


def _rows(src):
    if hasattr(src, "read"):
        return csv.reader(src)
    p = pathlib.Path(src)
    if p.suffix == ".zip":
        z = zipfile.ZipFile(p)
        names = [n for n in z.namelist() if n.upper().endswith((".CSV", ".XLSX"))]
        if names[0].upper().endswith(".XLSX"):
            return _xlsx(io.BytesIO(z.read(names[0])))
        return csv.reader(io.TextIOWrapper(z.open(names[0]), encoding="latin-1"))
    if p.suffix == ".xlsx":
        return _xlsx(p)
    return csv.reader(open(p, encoding="latin-1"))


def read(src, hedge_only=True):
    r = _rows(src)
    h = next(r)
    ix = {k: h.index(v) for k, v in COLS.items() if v in h}
    if hedge_only and "any_hedge" not in ix:
        raise ValueError("this file has no hedge-fund columns: read it with hedge_only=False")

    def get(row, k):
        return row[ix[k]] if k in ix and ix[k] < len(row) else ""
    out = []
    for row in r:
        if hedge_only and get(row, "any_hedge").strip().upper() not in ("Y", "YES"):
            continue
        out.append(Adviser(get(row, "crd").strip(), get(row, "name").strip(), _num(get(row, "employees")),
                           _num(get(row, "advisory")), _num(get(row, "raum")), _num(get(row, "pf_gav")),
                           _num(get(row, "n_hedge")), get(row, "filed").strip()))
    return out


def per_head(a):
    e, adv, raum = a.employees, a.advisory, a.raum
    return dict(raum_per_employee=raum / e if raum and e else None,
                raum_per_advisory=raum / adv if raum and adv else None,
                advisory_share=adv / e if adv is not None and e else None)


def quantiles(values, qs=(0.25, 0.5, 0.75)):
    v = np.asarray([x for x in values if x is not None], float)
    return [float(np.quantile(v, q)) for q in qs]


def concentration(values, k=10):
    v = [x for x in values if x]
    return moats.cr(v, k), moats.hhi(v)
