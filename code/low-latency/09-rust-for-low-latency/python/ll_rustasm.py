"""Chapter 9 of One Quant Book 13: the assembly rustc -O generates for two exported functions of the chapter's crate.

`body(fn)` compiles rust/src/lib.rs as a library (release optimisation, Intel syntax) and returns the instructions
of `fn`; `write()` stores the listings printed in the book (rustc 1.97). The tests check properties with the
installed rustc.
"""
import pathlib
import subprocess
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]
SRC = HERE / "rust/src/lib.rs"


def assembly():
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d) / "lib.s"
        cmd = ["rustc", "--edition", "2021", "-O", "--crate-type=lib", "--crate-name", "ll_rust",
               "--emit", f"asm={out}", "-C", "llvm-args=-x86-asm-syntax=intel", "-C", "debuginfo=0", str(SRC)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return out.read_text()


def body(fn, asm=None):
    lines = (asm or assembly()).splitlines()
    out = []
    for line in lines[lines.index(f"{fn}:") + 1:]:
        s = line.strip()
        if s.startswith(".Lfunc_end") or (s.endswith(":") and not s.startswith(".L")):
            break
        if s and not s.startswith(".") and not s.startswith("#"):
            out.append(line.split("#")[0].rstrip())
        elif s.startswith(".LBB") and s.endswith(":"):
            out.append(s)
    return out


def write():
    asm = assembly()
    for fn in ("sum_counted", "get_checked"):
        (HERE / f"rust/asm/{fn}.s").write_text("\n".join(body(fn, asm)) + "\n")


if __name__ == "__main__":
    write()
