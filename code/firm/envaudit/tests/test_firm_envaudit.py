"""Acceptance tests of firm.envaudit (One Quant Book 15, chapter 15)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_envaudit as E  # noqa: E402


def nb(*cells):
    out = []
    for src, n, text in cells:
        o = [{"output_type": "stream", "name": "stdout", "text": text}] if text else []
        out.append({"cell_type": "code", "source": src, "execution_count": n, "outputs": o, "metadata": {}})
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": out}


def kinds(n):
    return sorted((f.kind, f.cell, f.detail) for f in E.audit(n))


def test_clean_notebook_has_no_findings(tmp_path):
    n = nb(("x = 2", 1, ""), ("y = x * 3\nprint(y)", 2, "6\n"))
    assert E.audit(n) == [] and E.saved_output(n, 1) == "6\n"
    r = E.rerun(n, tmp_path)
    assert r.ok and r.stdout == "6\n"


def test_hidden_state_is_found(tmp_path):
    n = nb(("a = 1", 1, ""), ("b = a + c", 5, ""), ("c = 2", 2, ""), ("print(z)", 6, "9\n"), ("d = 1", None, ""),
           ("print(1)", None, "1\n"))
    k = kinds(n)
    assert ("out-of-order", 2, "counter 2 below the cell above it (5, cell 1)") in k
    assert ("skipped-counter", -1, "counter 3 to 4 missing: a re-run or a deleted cell") in k
    assert ("used-before-defined", 1, "c") in k and ("never-defined", 3, "z") in k
    assert ("never-run", 4, "code never executed") in k and ("output-without-run", 5, "outputs saved but no execution counter") in k
    r = E.rerun(n, tmp_path)
    assert not r.ok and "NameError" in r.stderr


def test_imports_functions_and_builtins_are_not_findings():
    n = nb(("import numpy as np\ndef f(x):\n    return np.sum(x) + len(x)", 1, ""), ("print(f([1, 2]))", 2, "5\n"))
    assert E.audit(n) == []


def test_environment_and_snapshot(tmp_path):
    env = {"python": "3.10", "platform": "x", "packages": {"numpy": "2.0.0", "pandas": "2.3.3"}}
    lock = "numpy==2.0.0\npandas==2.2.0\nscipy==1.0 # comment\n"
    assert E.compare_env(env, lock) == ["pandas: locked 2.2.0, installed 2.3.3", "scipy: locked 1.0, not installed"]
    p = tmp_path / "d.csv"
    p.write_text("a,b\n1,2\n")
    m = E.snapshot([p])
    assert E.check_snapshot([p], m) == []
    p.write_text("a,b\n1,3\n")
    assert E.check_snapshot([p], m) == ["d.csv: content changed"]
    assert "numpy" in E.capture_env()["packages"]


def test_promotion_checklist(tmp_path):
    n = nb(("x = 2\nprint(x)", 1, "2\n"))
    r = E.rerun(n, tmp_path)
    items = dict(E.promotion_checklist(n, r, "2", True, [], []))
    assert all(items.values()) and len(items) == 6
    bad = dict(E.promotion_checklist(nb(("print(q)", 1, "1\n")), E.Rerun(False, "", "", 1), "1", False, ["x"], []))
    assert not bad["audit finds no hidden state"] and not bad["rerun reproduces the saved result"]
