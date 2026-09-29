"""Chapter 6 of One Quant Book 14: a first hardware design, simulated, and a model of timing closure.

    clock_mhz(gbps, width_bits)             the clock a design needs to take a line's bits `width_bits` per cycle
    timing(levels, stages, t_lvl, t_reg)    period, maximum clock and latency of a decision of `levels` levels of logic
                                            split over `stages` registered stages (model delays, stated in the chapter)
    depth_for(levels, mhz, t_lvl, t_reg)    the fewest stages that meet a clock
    first_frame(workdir, pipe)              the first frame's events, cycle by cycle, from Verilator (firm.hdlkit)
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "hdlkit"))
import firm_hdlkit as h  # noqa: E402

T_LVL, T_REG = 0.5, 0.4          # ns per level of logic (LUT and routing), register overhead: model values
FRAME = bytes(range(0x10, 0x20))  # 16 bytes: the field (bytes 6-9) is 0x16171819


def clock_mhz(gbps, width_bits):
    return gbps * 1e3 / width_bits


def timing(levels, stages, t_lvl=T_LVL, t_reg=T_REG):
    per = math.ceil(levels / stages)
    period = per * t_lvl + t_reg
    return {"levels_per_stage": per, "period_ns": period, "fmax_mhz": 1e3 / period, "latency_ns": stages * period}


def depth_for(levels, mhz, t_lvl=T_LVL, t_reg=T_REG):
    for s in range(1, levels + 1):
        if timing(levels, s, t_lvl, t_reg)["fmax_mhz"] >= mhz:
            return s
    return None


def first_frame(workdir, pipe=1, thresh=0x16171819):
    d = pathlib.Path(workdir)
    d.mkdir(parents=True, exist_ok=True)
    exe = h.build_verilator(d / f"v{pipe}", {"OFF": 6, "LEN": 4, "PIPE": pipe})
    h.write_stim(d / "stim.txt", [FRAME])
    h.write_ready(d / "ready.txt", [1])
    return h.events(h.run_verilator(exe, d / "stim.txt", d / "ready.txt", thresh))
