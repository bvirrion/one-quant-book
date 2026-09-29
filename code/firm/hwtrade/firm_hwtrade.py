"""firm.hwtrade -- a hardware trigger, its cycle model and its golden model (build of One Quant Book 14, chapter 7).

hdl/hwt_trigger.sv reads the exchange simulator's MoldUDP64 packets 8 bytes a cycle, fires on a sell-side add order
for one instrument at or below a threshold, checks the order against a maximum size, a token bucket and a kill bit,
and patches it into an order template, one pipeline stage each. The same design is modelled three times:
    CycleModel (Python) and cpp/firm_hwtrade.hpp (C++20)   register for register, the same outputs on the same cycles
    triggers(packets, ...)                                   the message-level reference: which messages must fire
The tests run the design in Verilator and Icarus and require all four to agree.

API (stable):
    beats_of(packets, idle=2) -> list of beats and idle cycles     (last, keep, data) or None for an idle cycle
    write_stim(path, beats)
    CycleModel(loc, burst, refill).run(beats, thresh, max_qty, kill_at) -> (orders, rejects)
        orders: [(cycle, id, qty, price)]
    triggers(packets, thresh, loc) -> [(qty, price)]
    build_verilator(outdir, params) ; build_icarus(outdir, params) ; run_verilator(...) ; run_icarus(...)
    parse_output(text) -> (orders, rejects)
    wirepath_stage(cycles, clock_mhz) -> firm.wirepath Stage (the hardware variant of the wire-to-wire path)
"""
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "hdlkit"))
sys.path.insert(0, str(HERE.parent / "wirepath"))
import firm_hdlkit as hk  # noqa: E402
import firm_wirepath as wp  # noqa: E402

HDL = [str(HERE / "hdl" / "hwt_trigger.sv")]


def beats_of(packets, idle=2):
    out = []
    for p in packets:
        out.extend(hk.beats(p))
        out.extend([None] * idle)
    return out


def write_stim(path, beats):
    lines = ["I" if b is None else f"B {b[0]} {b[1]:02x} {b[2]:016x}" for b in beats]
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


class CycleModel:
    """The design's registers in Python, updated in the same order as the always_ff block."""

    def __init__(self, loc=1, burst=4, refill=64):
        self.loc, self.burst, self.refill = loc, burst, refill

    def run(self, beats, thresh, max_qty, kill_at=-1):
        ppos = mlen = mpos = lstate = mtype = mside = mloc = mqty = mprice = 0
        trig, tqty, tprice = False, 0, 0
        tokens, since = self.burst, 0
        passed, pqty, pprice, next_id, rejects = False, 0, 0, 1, 0
        orders = []
        for cycle in range(len(beats) + 8):
            b = beats[cycle] if cycle < len(beats) else None
            kill = 0 <= kill_at <= cycle
            n_trig, n_tqty, n_tprice = False, 0, 0
            if b is not None:
                last, keep, data = b
                s = [ppos, mlen, mpos, lstate, mtype, mside, mloc, mqty, mprice]
                for i in range(8):
                    if not keep >> (7 - i) & 1:
                        continue
                    byte = (data >> (56 - 8 * i)) & 0xFF
                    pp, ml, mp, ls, mt, ms, mc, mq, mr = s
                    if ls == 0:
                        if pp == 19:
                            ls = 1
                    elif ls == 1:
                        ml, ls = (byte << 8) | (ml & 0xFF), 2
                    elif ls == 2:
                        ml, mp, ls = (ml & 0xFF00) | byte, 0, 3
                    else:
                        if mp == 0:
                            mt = byte
                        if mp == 1:
                            mc = (byte << 8) | (mc & 0xFF)
                        if mp == 2:
                            mc = (mc & 0xFF00) | byte
                        if mp == 19:
                            ms = byte
                        if 20 <= mp <= 23:
                            mq = ((mq << 8) | byte) & 0xFFFFFFFF
                        if 32 <= mp <= 35:
                            mr = ((mr << 8) | byte) & 0xFFFFFFFF
                        if mp + 1 == ml:
                            if mt == ord("A") and ml == 36 and mc == self.loc and ms == ord("S") and mr <= thresh:
                                n_trig, n_tqty, n_tprice = True, mq, mr
                            ls = 1
                        mp = (mp + 1) & 0xFFFF
                    pp = (pp + 1) & 0xFFFF
                    s = [pp, ml, mp, ls, mt, ms, mc, mq, mr]
                ppos, mlen, mpos, lstate, mtype, mside, mloc, mqty, mprice = s
                if last:
                    ppos, lstate = 0, 0
            # stage 3 (uses stage 2's registers of the previous cycle)
            out_valid = passed and not kill
            if passed:
                if out_valid:
                    orders.append((cycle, next_id, pqty, pprice))
                    next_id += 1
            # stage 2 (uses stage 1's registers of the previous cycle)
            refill_now = since + 1 == self.refill
            new_tokens = tokens + 1 if (refill_now and tokens < self.burst) else tokens
            since = 0 if refill_now else since + 1
            new_pass = False
            if trig:
                if kill or tqty > max_qty or tokens == 0:
                    rejects += 1
                else:
                    new_pass, pqty, pprice = True, tqty, tprice
                    new_tokens = tokens - 1 + (1 if (refill_now and tokens < self.burst) else 0)
            tokens, passed = new_tokens, new_pass
            trig, tqty, tprice = n_trig, n_tqty, n_tprice
        return orders, rejects


def triggers(packets, thresh, loc=1):
    out = []
    for p in packets:
        _, _, count = struct.unpack_from(">10sQH", p, 0)
        off = 20
        for _ in range(count if count != 0xFFFF else 0):
            n = struct.unpack_from(">H", p, off)[0]
            m = p[off + 2:off + 2 + n]
            off += 2 + n
            if m[:1] == b"A" and n == 36 and struct.unpack_from(">H", m, 1)[0] == loc and m[19:20] == b"S":
                price = struct.unpack_from(">I", m, 32)[0]
                if price <= thresh:
                    out.append((struct.unpack_from(">I", m, 20)[0], price))
    return out


def build_verilator(outdir, params):
    hk.require("verilator")
    g = [f"-G{k}={v}" for k, v in params.items()]
    subprocess.run(["verilator", "--cc", "--exe", "--build", "-j", "1", "-Wall", "--top-module", "hwt_trigger", *g,
                    *HDL, str(HERE / "tb" / "hwt_tb.cpp"), "--Mdir", str(outdir), "-o", "sim"],
                   check=True, capture_output=True, text=True)
    return pathlib.Path(outdir) / "sim"


def build_icarus(outdir, params):
    hk.require("iverilog", "vvp")
    out = pathlib.Path(outdir) / "hwt.vvp"
    p = [f"-Phwt_tb.{k}={v}" for k, v in params.items()]
    subprocess.run(["iverilog", "-g2012", "-s", "hwt_tb", *p, "-o", str(out), *HDL, str(HERE / "tb" / "hwt_tb.sv")],
                   check=True, capture_output=True, text=True)
    return out


def run_verilator(exe, stim, thresh, max_qty, kill_at=-1):
    return subprocess.run([str(exe), str(stim), str(thresh), str(max_qty), str(kill_at)], check=True,
                          capture_output=True, text=True).stdout


def run_icarus(vvp, stim, thresh, max_qty, kill_at=-1):
    out = subprocess.run(["vvp", "-n", str(vvp), f"+stim={stim}", f"+thresh={thresh}", f"+maxq={max_qty}",
                          f"+kill={kill_at}"], check=True, capture_output=True, text=True).stdout
    return "\n".join(x for x in out.splitlines() if x[:1].isdigit() or x.startswith("R ")) + "\n"


def parse_output(text):
    orders, rejects = [], None
    for line in text.splitlines():
        p = line.split()
        if len(p) == 5 and p[1] == "O":
            orders.append((int(p[0]), int(p[2]), int(p[3]), int(p[4])))
        elif len(p) == 2 and p[0] == "R":
            rejects = int(p[1])
    return orders, rejects


def wirepath_stage(cycles, clock_mhz):
    return wp.hardware_stage(cycles, clock_mhz)
