"""Chapter 7 of One Quant Book 13: compile a function to Intel-syntax assembly and extract its body.

`body(fn)` compiles cpp/ll_asm_pipeline.cpp with the flags of the book (g++ -O2) and returns the instructions of `fn`
(labels and directives removed). The tests check properties of the body with whatever g++ is installed (no `call` in
the static pipeline, an indirect call in the dynamic one); `write()` stores the listing printed in the book, generated
on the book's laptop (g++ 11.4)."""
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).resolve().parents[1]
SRC = HERE / "cpp/ll_asm_pipeline.cpp"
FLAGS = ["-std=c++20", "-O2", "-S", "-masm=intel", "-fno-asynchronous-unwind-tables", "-fno-exceptions", "-o", "-"]


def assembly():
    return subprocess.run(["g++", *FLAGS, str(SRC)], check=True, capture_output=True, text=True).stdout


def body(fn, asm=None):
    lines = (asm or assembly()).splitlines()
    start = lines.index(f"{fn}:") + 1
    out = []
    for line in lines[start:]:
        s = line.strip()
        if s.startswith(".size") or (s.endswith(":") and not s.startswith(".L")):
            break
        if s and not s.startswith("."):
            out.append(line.rstrip())
        elif s.startswith(".L") and s.endswith(":"):
            out.append(s)
    return out


def calls(lines):
    return [x for x in lines if re.search(r"\bcall\b|\bjmp\s+\[|\bjmp\s+QWORD", x)]


def write():
    asm = assembly()
    for fn in ("run_static", "run_dynamic"):
        (HERE / f"cpp/asm/{fn}.s").write_text("\n".join(body(fn, asm)) + "\n")


if __name__ == "__main__":
    write()
