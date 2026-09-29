"""firm.envaudit -- audit a notebook, rerun it from the top, check its environment and data (One Quant Book 15, ch. 15).

A Jupyter notebook is a JSON document (nbformat 4): cells in document order, each code cell with its source, the
kernel's execution counter when it last ran (an integer, or null if it never ran) and its saved outputs. The audit
reads only that document. It reports execution out of document order (a cell above with a higher counter than a cell
below), skipped counters (a cell re-run, or run and then deleted), cells with outputs but no counter, names read
before any cell above defines them (in document order: the rerun will fail or find something else), and names never
defined in the notebook at all (defined by a deleted cell or typed at the prompt: hidden state). The rerun joins the
code cells in document order into one script and runs it in a fresh interpreter, in a subprocess, in a scratch
directory, and returns what it prints. Environment capture lists the interpreter and installed distributions and
compares them with a lock file of `name==version` lines; the data check compares files with a manifest of hashes.

API (stable):
    load(path) -> dict ; code_cells(nb) -> [(index, source, execution_count, outputs)]
    audit(nb) -> [Finding(kind, cell, detail)]   kinds: 'out-of-order', 'skipped-counter', 'output-without-run',
                                                'used-before-defined', 'never-defined', 'never-run'
    saved_output(nb, cell) -> str                the text of a cell's saved outputs
    rerun(nb, workdir, timeout=120, env=None) -> Rerun(ok, stdout, stderr, returncode)
    capture_env() -> {'python', 'platform', 'packages': {name: version}}
    compare_env(env, lock_text) -> [str]         differences (missing, different version); [] if it matches
    snapshot(paths) -> {name: sha256} ; check_snapshot(paths, manifest) -> [str]
    promotion_checklist(nb, rerun_result, expected, tests_passed, env_diffs, data_diffs) -> [(item, bool)]
"""
from __future__ import annotations

import ast
import builtins
import hashlib
import importlib.metadata as md
import json
import pathlib
import platform
import subprocess
import sys
from dataclasses import dataclass

BUILTINS = set(dir(builtins))


@dataclass(frozen=True)
class Finding:
    kind: str
    cell: int
    detail: str


@dataclass(frozen=True)
class Rerun:
    ok: bool
    stdout: str
    stderr: str
    returncode: int


def load(path) -> dict:
    return json.loads(pathlib.Path(path).read_text())


def _source(cell) -> str:
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else s


def code_cells(nb: dict) -> list[tuple]:
    return [(i, _source(c), c.get("execution_count"), c.get("outputs", []))
            for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]


def _names(src: str) -> tuple[set, set]:
    """(names bound, names read before being bound in this cell) by a simple pass over the syntax tree."""
    tree = ast.parse(src)
    bound, read = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                bound.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in bound:
            read.add(node.id)
    return bound, read


def audit(nb: dict) -> list[Finding]:
    out: list[Finding] = []
    cells = code_cells(nb)
    ran = [(i, n) for i, _s, n, _o in cells if n is not None]
    for (i, n), (j, m) in zip(ran, ran[1:], strict=False):
        if m < n:
            why = f"counter {m} below the cell above it ({n}, cell {i})"
            out.append(Finding("out-of-order", j, why))
    counters = sorted(n for _i, n in ran)
    for a, b in zip(counters, counters[1:], strict=False):
        if b - a > 1:
            gap = f"{a + 1}" if b - a == 2 else f"{a + 1} to {b - 1}"
            why = f"counter {gap} missing: a re-run or a deleted cell"
            out.append(Finding("skipped-counter", -1, why))
    everywhere = set()
    for _i, s, _n, _o in cells:
        everywhere |= _names(s)[0]
    defined = set()
    for i, s, n, outputs in cells:
        if n is None and outputs:
            why = "outputs saved but no execution counter"
            out.append(Finding("output-without-run", i, why))
        if n is None and not outputs and s.strip():
            out.append(Finding("never-run", i, "code never executed"))
        bound, read = _names(s)
        for name in sorted(read - defined - BUILTINS):
            kind = "used-before-defined" if name in everywhere else "never-defined"
            out.append(Finding(kind, i, name))
        defined |= bound
    return out


def saved_output(nb: dict, cell: int) -> str:
    text = []
    for o in nb["cells"][cell].get("outputs", []):
        if "text" in o:
            text.append("".join(o["text"]) if isinstance(o["text"], list) else o["text"])
        elif "data" in o and "text/plain" in o["data"]:
            d = o["data"]["text/plain"]
            text.append("".join(d) if isinstance(d, list) else d)
    return "".join(text)


def rerun(nb: dict, workdir, timeout: int = 120, env: dict | None = None) -> Rerun:
    """All code cells, top to bottom, as one script in a fresh interpreter."""
    workdir = pathlib.Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    script = workdir / "rerun.py"
    script.write_text("\n\n".join(s for _i, s, _n, _o in code_cells(nb)) + "\n")
    r = subprocess.run([sys.executable, str(script)], cwd=workdir, capture_output=True,
                       text=True, timeout=timeout, env=env)
    return Rerun(r.returncode == 0, r.stdout, r.stderr, r.returncode)


def capture_env() -> dict:
    pk = {}
    for d in md.distributions():
        name = d.metadata["Name"]
        if name:
            pk[name.lower().replace("_", "-")] = d.version
    return {"python": platform.python_version(), "platform": platform.platform(), "packages": pk}


def compare_env(env: dict, lock_text: str) -> list[str]:
    diffs = []
    for line in lock_text.splitlines():
        line = line.split("#")[0].strip()
        if "==" not in line:
            continue
        name, ver = (x.strip() for x in line.split("==", 1))
        have = env["packages"].get(name.lower().replace("_", "-"))
        if have is None:
            diffs.append(f"{name}: locked {ver}, not installed")
        elif have != ver:
            diffs.append(f"{name}: locked {ver}, installed {have}")
    return diffs


def snapshot(paths) -> dict:
    return {pathlib.Path(p).name: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in paths}


def check_snapshot(paths, manifest: dict) -> list[str]:
    now = snapshot(paths)
    out = [f"{k}: missing" for k in manifest if k not in now]
    out += [f"{k}: content changed" for k in manifest if k in now and now[k] != manifest[k]]
    out += [f"{k}: not in the manifest" for k in now if k not in manifest]
    return out


def promotion_checklist(nb: dict, rerun_result: Rerun, expected: str, tests_passed: bool, env_diffs: list,
                        data_diffs: list) -> list[tuple[str, bool]]:
    findings = audit(nb)
    return [("audit finds no hidden state", not any(f.kind in ("never-defined", "used-before-defined",
                                                                "out-of-order") for f in findings)),
            ("rerun from the top succeeds", rerun_result.ok),
            ("rerun reproduces the saved result", rerun_result.ok and expected.strip() in rerun_result.stdout),
            ("library functions tested", tests_passed),
            ("environment matches the lock", not env_diffs),
            ("data match the snapshot", not data_diffs)]
