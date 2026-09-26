"""Chapter 8 of One Quant Book 13: what the optimiser does with undefined behaviour, in assembly.

`body(fn, opt)` compiles cpp/ll_ub.cpp at the given level (Intel syntax) and returns the function's instructions;
`write()` stores the -O0 and -O2 listings printed in the book (generated with the laptop's g++ 11.4). The tests check
properties with whatever g++ is installed. `ubsan(x)` compiles and runs a call of increment(x) (return x + 1) under
-fsanitize=undefined and returns its diagnostics (plus_one_greater itself is folded to `true` even at -O0).
"""
import pathlib
import subprocess
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]
SRC = HERE / "cpp/ll_ub.cpp"


def assembly(opt="-O2"):
    cmd = ["g++", "-std=c++20", opt, "-S", "-masm=intel", "-fno-asynchronous-unwind-tables", "-fcf-protection=none",
           "-o", "-", str(SRC)]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def body(fn, opt="-O2"):
    lines = assembly(opt).splitlines()
    out = []
    for line in lines[lines.index(f"{fn}:") + 1:]:
        s = line.strip()
        if s.startswith(".size") or (s.endswith(":") and not s.startswith(".L")):
            break
        if s and not s.startswith("."):
            out.append(line.rstrip())
    return out


def ubsan(x):
    prog = f"""extern "C" int increment(int x) {{ return x + 1; }}
int main() {{ volatile int v = {x}; return increment(v) > v ? 0 : 1; }}
"""
    with tempfile.TemporaryDirectory() as d:
        src, exe = pathlib.Path(d) / "u.cpp", pathlib.Path(d) / "u"
        src.write_text(prog)
        subprocess.run(["g++", "-std=c++20", "-O0", "-fsanitize=undefined", str(src), "-o", str(exe)], check=True,
                       capture_output=True)
        return subprocess.run([str(exe)], capture_output=True, text=True).stderr


def write():
    for fn in ("plus_one_greater", "first_then_check", "alias"):
        (HERE / f"cpp/asm/{fn}_O2.s").write_text("\n".join(body(fn, "-O2")) + "\n")
    (HERE / "cpp/asm/plus_one_greater_O0.s").write_text("\n".join(body("plus_one_greater", "-O0")) + "\n")


if __name__ == "__main__":
    write()
