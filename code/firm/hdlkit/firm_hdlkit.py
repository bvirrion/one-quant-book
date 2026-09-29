"""firm.hdlkit -- the book's hardware toolkit (build of One Quant Book 14, chapter 6).

SystemVerilog stream primitives (hdl/): a skid buffer, a big-endian field extractor, a CRC-32 unit and a pipelined
comparator, assembled in hdk_top; a Verilator testbench (tb/hdk_tb.cpp) and an Icarus testbench (tb/hdk_tb.sv) that
print the same event lines for the same inputs; Python drivers that build and run both, and a golden model.
The HDL is written for Verilator 4.038 and Icarus Verilog 11 (and their newer releases): no interfaces or classes,
always @(*) where Icarus 11 limits always_comb. Missing tools raise ToolMissing: tests fail, never skip.

Streams: 8-byte beats, byte 0 of a beat in data[63:56], keep bits contiguous from bit 7; `last` on a frame's final beat.

API (stable):
    ToolMissing ; require(*tools)
    beats(frame) -> [(last, keep, data)]
    write_stim(path, frames, idle_every=0) ; write_ready(path, pattern)
    build_verilator(outdir, params, top="hdk_top", srcs=None, tb=None) -> exe path
    build_icarus(outdir, params, tb_top="hdk_tb", srcs=None, tb=None) -> vvp path
    run_verilator(exe, stim, ready, thresh) -> text ; run_icarus(vvp, stim, ready, thresh) -> text
    events(text) -> dict(I=[cycles], F=[(cycle, int)], C=[...], M=[...])
    golden(frames, off, length, thresh) -> dict(F=[int], C=[int], M=[0|1])
    CycleModel: a Python base class for cycle-accurate golden models (step(inputs) -> outputs)
"""
import pathlib
import shutil
import subprocess
import zlib

HERE = pathlib.Path(__file__).resolve().parent
HDL = sorted(str(p) for p in (HERE / "hdl").glob("hdk_*.sv"))


class ToolMissing(RuntimeError):
    pass


def require(*tools):
    for t in tools:
        if shutil.which(t) is None:
            raise ToolMissing(f"{t} is not installed: the HDL tests need it (they fail rather than skip)")


def beats(frame):
    out = []
    for i in range(0, len(frame), 8):
        chunk = frame[i:i + 8]
        keep = (0xFF << (8 - len(chunk))) & 0xFF
        data = int.from_bytes(chunk.ljust(8, b"\0"), "big")
        out.append((int(i + 8 >= len(frame)), keep, data))
    return out


def write_stim(path, frames, idle_every=0):
    lines, n = [], 0
    for f in frames:
        for last, keep, data in beats(f):
            lines.append(f"B {last} {keep:02x} {data:016x}")
            n += 1
            if idle_every and n % idle_every == 0:
                lines.append("I")
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


def write_ready(path, pattern):
    pathlib.Path(path).write_text("\n".join(str(int(x)) for x in pattern) + "\n")


def build_verilator(outdir, params, top="hdk_top", srcs=None, tb=None):
    require("verilator")
    outdir = pathlib.Path(outdir)
    g = [f"-G{k}={v}" for k, v in params.items()]
    cmd = ["verilator", "--cc", "--exe", "--build", "-j", "1", "-Wall", "--top-module", top, *g,
           *(srcs or HDL), str(tb or HERE / "tb" / "hdk_tb.cpp"), "--Mdir", str(outdir), "-o", "sim"]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return outdir / "sim"


def build_icarus(outdir, params, tb_top="hdk_tb", srcs=None, tb=None):
    require("iverilog", "vvp")
    out = pathlib.Path(outdir) / "sim.vvp"
    p = [f"-P{tb_top}.{k}={v}" for k, v in params.items()]
    subprocess.run(["iverilog", "-g2012", "-s", tb_top, *p, "-o", str(out), *(srcs or HDL),
                    str(tb or HERE / "tb" / "hdk_tb.sv")], check=True, capture_output=True, text=True)
    return out


def run_verilator(exe, stim, ready, thresh):
    return subprocess.run([str(exe), str(stim), str(ready), f"{thresh:x}"], check=True, capture_output=True,
                          text=True).stdout


def run_icarus(vvp, stim, ready, thresh):
    out = subprocess.run(["vvp", "-n", str(vvp), f"+stim={stim}", f"+ready={ready}", f"+thresh={thresh:x}"],
                         check=True, capture_output=True, text=True).stdout
    return "\n".join(x for x in out.splitlines() if x and x[0].isdigit()) + "\n"


def events(text):
    ev = {"I": [], "F": [], "C": [], "M": []}
    for line in text.splitlines():
        p = line.split()
        if len(p) == 2:
            ev[p[1]].append(int(p[0]))
        elif len(p) == 3:
            ev[p[1]].append((int(p[0]), int(p[2], 16) if p[1] in "FC" else int(p[2])))
    return ev


def golden(frames, off, length, thresh):
    fld = [int.from_bytes(f[off:off + length], "big") for f in frames if len(f) >= off + length]
    return {"F": fld, "C": [zlib.crc32(f) for f in frames], "M": [int(v <= thresh) for v in fld]}


class CycleModel:
    """Base class of a cycle-accurate golden model: `step(inputs)` computes the outputs registered at the next edge
    from the current state and inputs, then updates the state."""

    def reset(self):
        raise NotImplementedError

    def step(self, inputs):
        raise NotImplementedError
