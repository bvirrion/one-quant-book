"""Numbers gate for Book 18, chapter 23: every compile-fail snippet is compiled with the pinned rustc and the error
code asserted; every output-prediction snippet is compiled and run and its output asserted. The coding answers are
unit tests of the crate in rust/ (cargo test, clippy -D warnings, run by tools/test_code.sh)."""
import pathlib
import re
import subprocess

import pytest

SNIP = pathlib.Path(__file__).resolve().parents[1] / "rust" / "snippets"

COMPILE_FAIL = {
    "borrow_conflict": "E0502",
    "two_mut": "E0499",
    "use_after_move": "E0382",
    "missing_lifetime": "E0106",
    "return_local": "E0515",
    "rc_not_send": "E0277",
}

OUTPUT = {
    "drop_order": "drop ignored\nend of main\ndrop b\ndrop first\ndrop second\ndrop a\n",
    "shadowing": "201\n200\n",
}


def rustc(name, out):
    return subprocess.run(["rustc", "--edition", "2021", "-o", str(out), str(SNIP / f"{name}.rs")],
                          capture_output=True, text=True)


@pytest.mark.parametrize("name", sorted(COMPILE_FAIL))
def test_compile_fail(name, tmp_path):
    r = rustc(name, tmp_path / name)
    assert r.returncode != 0
    codes = re.findall(r"error\[(E\d{4})\]", r.stderr)
    assert codes and codes[0] == COMPILE_FAIL[name]


@pytest.mark.parametrize("name", sorted(OUTPUT))
def test_output(name, tmp_path):
    r = rustc(name, tmp_path / name)
    assert r.returncode == 0, r.stderr
    run = subprocess.run([str(tmp_path / name)], capture_output=True, text=True, timeout=60)
    assert run.stdout == OUTPUT[name]
