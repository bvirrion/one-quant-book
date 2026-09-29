"""Numbers gate for Book 18, chapter 22: every output-prediction snippet is compiled and run and its output
asserted; every undefined-behaviour snippet is built with AddressSanitizer and UndefinedBehaviorSanitizer and the
test asserts the sanitizer's diagnosis, never an output. The coding answers are in cpp/iv_cpp_test.cpp, which
tools/test_code.sh builds with -Werror."""
import pathlib
import subprocess

import pytest

SNIP = pathlib.Path(__file__).resolve().parents[1] / "cpp" / "snippets"

EXPECTED = {
    "virtual_in_ctor": "Base\nDerived\nDerived\n",
    "lifetime_order": "make second\nmake first\nbody\nmake temp\ndrop temp\nafter t\ndrop first\ndrop second\n",
    "overload_rvalue": "lvalue\nrvalue\nrvalue\nlvalue\n",
    "sign_compare": "over limit\n4294967295\n",  # 32-bit unsigned: x86-64 Linux
    "static_init": "init b\ninit a\na=3 b=2\n",
    "moved_from": "w=3 v=0\nv[0]=7\n",  # v.size() == 0 after the move is libstdc++'s choice, not a guarantee
    "smart_sizes": "8 16 32\n",  # implementation-defined: libstdc++ on x86-64 Linux
}

UB = {
    "ub_dangling_view": "heap-use-after-free",
    "ub_signed_overflow": "signed integer overflow",
    "ub_invalidated": "heap-use-after-free",
}


def build_and_run(name, tmp_path, flags):
    exe = tmp_path / name
    comp = subprocess.run(["g++", "-std=c++20", *flags, str(SNIP / f"{name}.cpp"), "-o", str(exe)],
                          capture_output=True, text=True, check=True)
    run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=60)
    return comp, run


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_output_prediction(name, tmp_path):
    comp, run = build_and_run(name, tmp_path, ["-O2", "-Wall", "-Wextra"])
    assert run.returncode == 0 and run.stdout == EXPECTED[name]
    if name == "sign_compare":
        assert "-Wsign-compare" in comp.stderr  # the compiler warns about the comparison
    else:
        assert "warning" not in comp.stderr


@pytest.mark.reference
@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_output_prediction_O0(name, tmp_path):
    _, run = build_and_run(name, tmp_path, ["-O0"])
    assert run.stdout == EXPECTED[name]


@pytest.mark.parametrize("name", sorted(UB))
def test_undefined_behaviour_is_diagnosed(name, tmp_path):
    flags = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
    _, run = build_and_run(name, tmp_path, flags)
    assert run.returncode != 0 and UB[name] in run.stderr
