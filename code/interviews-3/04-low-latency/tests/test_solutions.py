"""Every behavioural claim in the answers of "Low Latency": compile each printed listing, run it, read the sanitizer.

Rules: every printed C++ file compiles with g++ -std=c++20 -O2 -Wall -Wextra -Werror; every printed Rust file builds under
cargo with warnings denied. A bug printed on purpose is shown by a sanitizer report or a wrong output; its fix is shown clean.
Tests assert correctness, never a timing. Figures measured here are recorded in sources/interviews-3/04-low-latency.md.
TSan needs setarch -R on this kernel. Rust TSan uses the nightly toolchain with an uninstrumented std, so reports from the
standard library's own Arc (it uses fences) are ignored: a Rust test looks only for reports that name our code.
"""
import math
import os
import pathlib
import platform
import re
import shutil
import subprocess

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
CPP = HERE / "cpp"
RUST = HERE / "rust"
DRAFT = HERE.parents[2]
BUILD = DRAFT / "build" / "iv33"
BUILD.mkdir(parents=True, exist_ok=True)
STRICT = ["-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror"]
TSAN = ["-std=c++20", "-O1", "-g", "-fsanitize=thread"]
TSAN_RACE = "WARNING: ThreadSanitizer: data race"
TARGET = "x86_64-unknown-linux-gnu"
HAS_NIGHTLY = shutil.which("rustup") is not None and subprocess.run(
    ["rustc", "+nightly", "--version"], capture_output=True).returncode == 0
needs_nightly = pytest.mark.skipif(not HAS_NIGHTLY, reason="Rust TSan needs the nightly toolchain")

NONNUMERIC = {
    28: "a diagnosis of jitter sources on a tuned machine: every fact is a kernel documentation row in the ledger, and this machine has no isolated cores to demonstrate on",
}


def gxx(name, flags=STRICT, text=None, extra=(), tag=""):
    """Compile cpp/<name>.cpp, or text in its place, under build/iv33. Returns the executable."""
    exe = BUILD / f"{name}{tag}"
    src = CPP / f"{name}.cpp"
    if text is not None:
        src = BUILD / f"{name}{tag}.cpp"
        src.write_text(text, encoding="utf-8")
    r = subprocess.run(["g++", *flags, str(src), "-o", str(exe), "-pthread", *extra], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return exe


def run(exe, *args, timeout=60):
    return subprocess.run([str(exe), *map(str, args)], capture_output=True, text=True, timeout=timeout)


def tsan(name, text=None, tag="_tsan", args=(), flags=TSAN):
    exe = gxx(name, flags, text=text, tag=tag)
    return subprocess.run(["setarch", platform.machine(), "-R", str(exe), *map(str, args)],
                          capture_output=True, text=True, timeout=120)


def asm(name, flags=("-std=c++20", "-O2"), text=None):
    src = CPP / f"{name}.cpp"
    if text is not None:
        src = BUILD / f"{name}_asm.cpp"
        src.write_text(text, encoding="utf-8")
    r = subprocess.run(["g++", *flags, "-S", "-o", "-", str(src)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def functions(assembly):
    """Map each symbol to the instruction lines under its label, up to the next .cfi_endproc."""
    out, cur = {}, None
    for line in assembly.splitlines():
        m = re.match(r"^([A-Za-z_][\w.]*):$", line)
        if m and not line.startswith(".L"):
            cur = m.group(1)
            out[cur] = []
        elif cur and ".cfi_endproc" in line:
            cur = None
        elif cur and line.startswith("\t") and not line.startswith("\t.") and "endbr64" not in line:
            out[cur].append(line.strip())
    return out


def rust_env(target="rt"):
    env = dict(os.environ, RUSTFLAGS="-Dwarnings", CARGO_TARGET_DIR=str(BUILD / target))
    return env


@pytest.fixture(scope="session")
def rust_bins():
    """cargo test and a release build of every bin, warnings denied: the rule for every printed Rust file."""
    env = rust_env()
    t = subprocess.run(["cargo", "test", "--offline", "-q"], cwd=RUST, env=env, capture_output=True, text=True)
    assert t.returncode == 0, t.stdout + t.stderr
    b = subprocess.run(["cargo", "build", "--release", "--offline", "--bins", "-q"], cwd=RUST, env=env,
                       capture_output=True, text=True)
    assert b.returncode == 0, b.stderr
    return BUILD / "rt" / "release"


def rustc(name, text, opt=False, tag=""):
    """Compile text as a single-file program. Returns (returncode, stderr, exe)."""
    src = BUILD / f"{name}{tag}.rs"
    src.write_text(text, encoding="utf-8")
    exe = BUILD / f"{name}{tag}_rs"
    flags = ["-C", "opt-level=3"] if opt else []
    r = subprocess.run(["rustc", "--edition", "2021", *flags, str(src), "-o", str(exe)], capture_output=True, text=True)
    return r.returncode, r.stderr, exe


def rust_tsan(name, text):
    """Build on nightly with -Zsanitizer=thread and run; returns the stderr."""
    src = BUILD / f"{name}_ts.rs"
    src.write_text(text, encoding="utf-8")
    exe = BUILD / f"{name}_ts_rs"
    r = subprocess.run(["rustc", "+nightly", "--edition", "2021", "-g", "-Zsanitizer=thread",
                        "-Cunsafe-allow-abi-mismatch=sanitizer", "--target", TARGET, str(src), "-o", str(exe)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    p = subprocess.run(["setarch", platform.machine(), "-R", str(exe)], capture_output=True, text=True, timeout=180)
    return p.stderr


def race_reports(stderr):
    return [b for b in stderr.split("==================") if TSAN_RACE in b]


def test_every_cpp_listing_compiles_strictly():
    for src in sorted(CPP.glob("*.cpp")):
        extra = ["-latomic"] if src.stem == "quote_atomic" else []
        if src.stem == "atomic_ops":
            r = subprocess.run(["g++", *STRICT, "-c", str(src), "-o", str(BUILD / "atomic_ops.o")], capture_output=True, text=True)
            assert r.returncode == 0, r.stderr
        else:
            gxx(src.stem, extra=extra)


def test_q1():
    assert run(gxx("layout")).stdout.split() == ["24", "16", "64", "192", "16", "13"]


def test_q2():
    src = (CPP / "spin_flag.cpp").read_text(encoding="utf-8")
    # g++ 11.4 at -O2 deletes the loop (-ffinite-loops) and prints the unset value.
    assert run(gxx("spin_flag")).stdout.strip() == "0"
    assert run(gxx("spin_flag", ["-std=c++20", "-O0"], tag="_o0")).stdout.strip() == "42"
    jumps = re.findall(r"^\.(L\d+):\n(?:\t\.[^\n]*\n)*\tjmp\t\.\1$", asm("spin_flag", ("-std=c++20", "-O2", "-fno-finite-loops")), re.M)
    assert jumps, "without -ffinite-loops the reader becomes a jump to itself"
    assert not re.findall(r"^\.(L\d+):\n(?:\t\.[^\n]*\n)*\tjmp\t\.\1$", asm("spin_flag"), re.M)
    with pytest.raises(subprocess.TimeoutExpired):  # without that assumption the read is hoisted: it spins for ever
        run(gxx("spin_flag", [*STRICT, "-fno-finite-loops"], tag="_nofinite"), timeout=2)
    at_o0 = [f if f != "-O1" else "-O0" for f in TSAN]  # at -O1 the reader spins for ever on its hoisted copy
    assert TSAN_RACE in tsan("spin_flag", flags=at_o0).stderr
    vol = src.replace("bool ready = false", "volatile bool ready = false")
    assert run(gxx("spin_flag", STRICT, text=vol, tag="_vol")).stdout.strip() == "42"
    assert TSAN_RACE in tsan("spin_flag", text=vol, tag="_vol_tsan", flags=at_o0).stderr
    fixed = src.replace("#include <chrono>", "#include <atomic>\n#include <chrono>").replace(
        "bool ready = false", "std::atomic<bool> ready{false}")
    r = tsan("spin_flag", text=fixed, tag="_fix_tsan", flags=at_o0)
    assert TSAN_RACE not in r.stderr and r.stdout.strip() == "42"
    assert run(gxx("spin_flag", STRICT, text=fixed, tag="_fix")).stdout.strip() == "42"


def test_q3(rust_bins):
    assert run(rust_bins / "sizes").stdout.split() == ["8", "16", "8", "8", "8", "16", "16", "24", "24", "1"]


def test_q4(rust_bins):
    assert run(rust_bins / "spawn_borrow").stdout.strip() == "300"
    assert run(rust_bins / "spawn_scoped").stdout.split() == ["300", "3"]
    text = (RUST / "src/bin/spawn_borrow.rs").read_text(encoding="utf-8")
    assert "move ||" in text
    rc, err, _ = rustc("spawn_nomove", text.replace("move ||", "||"))
    assert rc != 0 and "E0373" in err


def test_q5():
    ghz, ipc, dram = 4, 2, 90
    cycles = 1000 * ghz
    assert cycles == 4000 and cycles * ipc == 8000
    assert 1000 // dram == 11 and 500 // dram == 5
    assert 5 * dram == 450 and 450 * ghz == 1800 and 1800 * ipc == 3600
    assert 20 / ghz == 5  # a 20-cycle mispredict in nanoseconds


def test_q6():
    r = run(gxx("counters"), 4, 200000)
    first = r.stdout.splitlines()[0].split()
    assert first[:2] == ["64", "512"]
    assert first[2:] == ["800000", "800000"]
    probe = '#include <new>\n#include <cstdio>\nint main(){\n#ifdef __cpp_lib_hardware_interference_size\nstd::puts("yes");\n#else\nstd::puts("no");\n#endif\n}\n'
    assert run(gxx("probe", STRICT, text=probe)).stdout.strip() == "no"  # absent on g++ 11.4


def test_q7():
    f = functions(asm("atomic_ops"))
    for name in ("_Z12load_relaxedv", "_Z12load_acquirev", "_Z12load_seq_cstv"):
        assert f[name][0].startswith("movq"), f[name]
    for name in ("_Z13store_relaxedl", "_Z13store_releasel"):
        assert f[name][0].startswith("movq") and not any("lock" in i or "xchg" in i for i in f[name])
    assert f["_Z13store_seq_cstl"][0].startswith("xchgq")
    assert any(i.startswith("lock") for i in f["_Z11add_relaxedv"])
    assert not any("lock" in i for i in f["_Z9add_plainv"])


def test_q8():
    out = run(gxx("list_order"), 200000).stdout.splitlines()
    assert out[0] == "1"
    near = [float(x) for x in out[1].split(":")[1].split()]
    assert near[0] > 0.99 and near[1] < 0.01


def test_q9():
    lines = dict(re.findall(r"^(.*?)\s+(\d+)$", run(gxx("count_new")).stdout, re.M))
    assert lines == {"string 15": "0", "string 16": "1", "push 1000": "11", "reserved": "1", "function 16": "0",
                     "function 24": "1", "shared new": "2", "make_shared": "1", "map 10": "10"}


def test_q10():
    assert run(gxx("parse_header")).stdout.split() == ["123456789", "123456789"]
    u = gxx("parse_header", ["-std=c++20", "-O1", "-g", "-fsanitize=alignment"], tag="_ub")
    r = run(u)
    assert "misaligned address" in r.stderr and "parse_header.cpp:12" in r.stderr
    assert "parse_header.cpp:17" not in r.stderr and "parse_header.cpp:18" not in r.stderr
    f = functions(asm("parse_header"))
    for name in ("_Z7ts_castPKh", "_Z7ts_copyPKh"):
        assert f[name][0] == "movq\t8(%rdi), %rax" and not any("call" in i for i in f[name])


def test_q11():
    f = functions(asm("bench_bad"))
    assert not any("work" in i or "imul" in i or i.startswith("j") for i in f["main"])
    assert any("_Z4workm" in i for i in functions(asm("bench_good"))["main"])
    assert re.match(r"median \d+ ns, p99 \d+ ns, max \d+ ns", run(gxx("bench_good")).stdout)


def test_q12():
    src = (CPP / "publish.cpp").read_text(encoding="utf-8")
    assert run(gxx("publish")).stdout.strip() == "42"
    assert TSAN_RACE in tsan("publish").stderr
    fixed = src.replace("ready.store(true, std::memory_order_relaxed)", "ready.store(true, std::memory_order_release)")
    fixed = fixed.replace("ready.load(std::memory_order_relaxed)", "ready.load(std::memory_order_acquire)")
    r = tsan("publish", text=fixed, tag="_fix_tsan")
    assert TSAN_RACE not in r.stderr and r.stdout.strip() == "42"


def test_q13():
    r = tsan("spinlock")
    assert TSAN_RACE in r.stderr
    assert run(gxx("spinlock")).stdout.strip() == "80000"
    good = tsan("spinlock_ttas")
    assert TSAN_RACE not in good.stderr and good.stdout.strip() == "80000"
    assert run(gxx("spinlock_ttas")).stdout.strip() == "80000"


def test_q14():
    exe = gxx("quote_atomic", extra=["-latomic"])
    assert run(exe).stdout.splitlines() == ["1 1", "0 0", "0 0", "99.5 100.5"]
    syms = subprocess.run(["nm", "-u", str(exe)], capture_output=True, text=True).stdout
    assert "__atomic_load_16" in syms and "__atomic_store_16" in syms
    no_lib = subprocess.run(["g++", *STRICT, str(CPP / "quote_atomic.cpp"), "-o", str(BUILD / "qa_nolib")], capture_output=True, text=True)
    assert no_lib.returncode != 0 and "__atomic" in no_lib.stderr


def test_q15():
    table = [  # type, Send, Sync
        ("std::rc::Rc<u64>", False, False),
        ("std::sync::Arc<u64>", True, True),
        ("std::sync::Arc<std::cell::Cell<u64>>", False, False),
        ("std::cell::Cell<u64>", True, False),
        ("std::cell::RefCell<u64>", True, False),
        ("std::sync::Mutex<std::cell::Cell<u64>>", True, True),
        ("std::sync::Mutex<std::rc::Rc<u64>>", False, False),
        ("&'static std::cell::Cell<u64>", False, False),
        ("*mut u64", False, False),
        ("std::sync::MutexGuard<'static, u64>", False, True),
        ("std::sync::atomic::AtomicU64", True, True),
    ]
    lines = ["fn send<T: Send>() {}", "fn sync<T: Sync>() {}", "fn main() {"]
    where = {}
    for ty, _, _ in table:
        for trait in ("send", "sync"):
            where[len(lines) + 1] = (ty, trait)
            lines.append(f"    {trait}::<{ty}>();")
    lines.append("}")
    rc, err, _ = rustc("send_sync", "\n".join(lines) + "\n")
    assert rc != 0
    failed = {where[int(n)] for n in re.findall(r"send_sync\.rs:(\d+):\d+", err) if int(n) in where}
    for ty, s, y in table:
        assert ((ty, "send") not in failed) == s, ty
        assert ((ty, "sync") not in failed) == y, ty


def smallest_final(threads, n):
    """Smallest final count over all interleavings of k threads doing n read-then-write increments of one variable."""
    seen, best = set(), None
    start = (0, (0,) * threads, (0,) * threads)  # memory, each thread's register, each thread's completed steps
    stack = [start]
    while stack:
        state = stack.pop()
        if state in seen:
            continue
        seen.add(state)
        mem, reg, steps = state
        moved = False
        for t in range(threads):
            if steps[t] < 2 * n:
                moved = True
                r, m = list(reg), mem
                if steps[t] % 2 == 0:
                    r[t] = mem
                else:
                    m = reg[t] + 1
                stack.append((m, tuple(r), steps[:t] + (steps[t] + 1,) + steps[t + 1:]))
        if not moved:
            best = mem if best is None else min(best, mem)
    return best


def test_q16(rust_bins):
    finals = [int(run(rust_bins / "lost_update").stdout) for _ in range(5)]
    assert all(0 < v <= 4_000_000 for v in finals) and min(finals) < 4_000_000
    assert smallest_final(2, 1) == 1 and smallest_final(2, 2) == 2 and smallest_final(2, 3) == 2 and smallest_final(3, 2) == 2
    text = (RUST / "src/bin/lost_update.rs").read_text(encoding="utf-8")
    fixed = text.replace("let v = COUNT.load(Relaxed);\n", "").replace("COUNT.store(v + 1, Relaxed);", "COUNT.fetch_add(1, Relaxed);")
    rc, err, exe = rustc("lost_fixed", fixed, opt=True)
    assert rc == 0, err
    assert run(exe).stdout.strip() == "4000000"


def test_q17(rust_bins):
    rc, err, exe = rustc("vec_cap", 'fn main() { let mut v = Vec::new(); v.push(1_u64); println!("{}", v.capacity()); }\n')
    assert rc == 0, err
    assert run(exe).stdout.strip() == "4"
    got = dict(re.findall(r"^(.*?)\s+(\d+)$", run(rust_bins / "count_alloc").stdout, re.M))
    assert got == {"Vec::new": "0", "with_capacity(8)": "1", "String::new": "0", "to_string": "1", "Box<()>": "0",
                   "Box<u64>": "1", "1000 pushes": "9", "clear and refill": "0", "Arc::clone": "0"}


def test_q18():
    out = BUILD / "bounds.s"
    r = subprocess.run(["rustc", "--edition", "2021", "-C", "opt-level=3", "--emit=asm", "--crate-type=lib",
                        str(RUST / "src/bounds.rs"), "-o", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    f = functions(out.read_text(encoding="utf-8"))
    has = {k: any("panic_bounds_check" in i for i in v) for k, v in f.items() if k in
           ("sum_a", "sum_b", "sum_c", "sum_d", "diff_e", "pick_f", "pick_g")}
    assert has == {"sum_a": False, "sum_b": True, "sum_c": False, "sum_d": False, "diff_e": False, "pick_f": True, "pick_g": False}
    assert not any("panic" in i for i in f["sum_a"]) and not any("panic" in i for i in f["pick_g"])
    assert any("slice" in i and "fail" in i for i in f["sum_c"]) and any("panic" in i for i in f["sum_d"])


def test_q19():
    entries, gib = 2048, 2**30
    assert entries * 4096 == 8 * 2**20 and entries * 2 * 2**20 == 4 * gib
    table = 8 * gib
    assert 1 - entries * 4096 / table == pytest.approx(0.99902, abs=1e-5)
    assert 1 - entries * 2 * 2**20 / table == 0.5
    assert (1 - entries * 4096 / table) * 30 == pytest.approx(29.97, abs=0.01)
    assert 0.5 * 30 == 15
    assert table // 4096 * 8 == 16 * 2**20 and table // (2 * 2**20) * 8 == 32 * 2**10


def sc_outcomes(threads):
    """All final register maps over every interleaving, under sequential consistency. Ops: ('w', var, v) or ('r', var, reg)."""
    results = set()

    def go(pcs, mem, regs):
        moved = False
        for i, th in enumerate(threads):
            if pcs[i] < len(th):
                moved = True
                kind, var, arg = th[pcs[i]]
                new_mem, new_regs = dict(mem), dict(regs)
                if kind == "w":
                    new_mem[var] = arg
                else:
                    new_regs[arg] = new_mem.get(var, 0)
                go(pcs[:i] + (pcs[i] + 1,) + pcs[i + 1:], new_mem, new_regs)
        if not moved:
            results.add(tuple(sorted(regs.items())))

    go(tuple(0 for _ in threads), {}, {})
    return results


def test_q20():
    counts = dict(re.findall(r"^(\w+) (\d+)$", run(gxx("store_buffer"), timeout=120).stdout, re.M))
    assert counts["seq_cst"] == "0"
    assert int(counts["relaxed"]) > 0 and int(counts["acq_rel"]) > 0
    sb = [[("w", "x", 1), ("r", "y", "r1")], [("w", "y", 1), ("r", "x", "r2")]]
    assert (("r1", 0), ("r2", 0)) not in sc_outcomes(sb)
    iriw = [[("w", "x", 1)], [("w", "y", 1)], [("r", "x", "a"), ("r", "y", "b")], [("r", "y", "c"), ("r", "x", "d")]]
    assert (("a", 1), ("b", 0), ("c", 1), ("d", 0)) not in sc_outcomes(iriw)


def test_q21():
    src = (CPP / "spsc.cpp").read_text(encoding="utf-8")
    assert run(gxx("spsc")).stdout.strip() == "0 wrong of 200000"
    r = tsan("spsc")
    assert TSAN_RACE not in r.stderr and r.stdout.strip() == "0 wrong of 200000"
    # each of the four orders is needed: relaxing any one gives a report on the slots
    for i, (a, b) in enumerate([
        ("tail_.store(t + 1, std::memory_order_release)", "tail_.store(t + 1, std::memory_order_relaxed)"),
        ("h == tail_.load(std::memory_order_acquire)", "h == tail_.load(std::memory_order_relaxed)"),
        ("head_.store(h + 1, std::memory_order_release)", "head_.store(h + 1, std::memory_order_relaxed)"),
        ("t - head_.load(std::memory_order_acquire)", "t - head_.load(std::memory_order_relaxed)"),
    ]):
        assert a in src
        m = tsan("spsc", text=src.replace(a, b), tag=f"_m{i}")
        assert TSAN_RACE in m.stderr, f"mutation {i} was not caught"
    driver = ('#define main spsc_main\n#include "' + str(CPP / "spsc.cpp") + '"\n#undef main\n'
              'int main() { Spsc<long, 8> r; long x = 0; int ok = 0; for (int i = 0; i < 9; ++i) ok += r.push(i);\n'
              'std::printf("%d %d ", ok, (int) r.pop(x)); std::printf("%ld\\n", x); }\n')
    assert run(gxx("spsc_driver", ["-std=c++20", "-O2"], text=driver)).stdout.split() == ["8", "1", "0"]


def test_q22():
    out = run(gxx("spsc_layout"), 200000).stdout.splitlines()
    assert out[0] == "wrong 0; offsets 8 64 64"
    r = tsan("spsc_layout", args=(100000,))
    assert TSAN_RACE not in r.stderr and "wrong 0" in r.stdout


def test_q23():
    src = (CPP / "wrap.cpp").read_text(encoding="utf-8")
    assert run(gxx("wrap")).stdout.strip() == "100 wrong of 500"
    assert 2**32 % 1000 == 296
    assert 2**32 / 1e6 / 60 == pytest.approx(71.6, abs=0.1)
    pow2 = src.replace("capacity = 1000", "capacity = 1024")
    assert run(gxx("wrap", STRICT, text=pow2, tag="_p2")).stdout.strip() == "0 wrong of 500"
    wide = src.replace("std::uint32_t head = 0, tail = 0", "std::uint64_t head = 0, tail = 0").replace(
        "static constexpr std::uint32_t capacity", "static constexpr std::uint64_t capacity")
    assert run(gxx("wrap", STRICT, text=wide, tag="_w")).stdout.strip() == "0 wrong of 500"
    assert 2**64 / 1e9 / 86400 / 365.25 == pytest.approx(584.5, abs=0.1)
    # the exact condition: more than 296 items straddling the wrap
    for before, after, wrong in ((100, 196, 0), (100, 197, 1), (296, 0, 0), (290, 7, 1)):
        bounds = src.replace("0xFFFFFFFFu - 399", f"0xFFFFFFFFu - {before - 1}").replace("i < 500", f"i < {before + after}")
        got = run(gxx("wrap", STRICT, text=bounds, tag="_b")).stdout.strip()
        assert got == f"{wrong} wrong of {before + after}", (before, after, got)


def test_q24():
    out = run(gxx("hist")).stdout.split()
    assert out[:2] == ["1600", "12800"]
    assert int(out[2]) == 983040 and abs(990000 - 983040) / 990000 < 1 / 64
    assert float(out[3]) <= 1 / 64


def test_q25():
    if "[always]" in pathlib.Path("/sys/kernel/mm/transparent_hugepage/enabled").read_text():
        pytest.skip("transparent huge pages set to always")
    lines = run(gxx("first_touch")).stdout.splitlines()
    m = re.match(r"malloc (\d+), first pass (\d+), second pass (\d+)", lines[0])
    v = re.match(r"vector (\d+), first pass (\d+)", lines[1])
    pages = 64 * 2**20 // 4096
    assert pages == 16384
    assert int(m.group(1)) < 16 and int(m.group(2)) > 0.9 * pages and int(m.group(3)) < 16
    assert int(v.group(1)) > 0.9 * pages and int(v.group(2)) < 16


def percentile(sorted_values, p):
    return sorted_values[math.ceil(p * len(sorted_values)) - 1]


def test_q26():
    arrivals = [i * 0.002 for i in range(50000)]
    service, stall_at, stall = 0.001, 50.0, 1.0
    # true latency per intended send time: a FIFO server that freezes for 1 s
    free, truth = 0.0, []
    for t in arrivals:
        start = max(t, free)
        if start < stall_at + stall and start + service > stall_at:
            start = stall_at + stall
        free = start + service
        truth.append(free - t)
    # what a tool that waits for each reply before sending records: one slow sample, then nothing during the stall
    tool, now = [], 0.0
    for t in arrivals:
        if t < now:
            continue
        start = t
        if start < stall_at + stall and start + service > stall_at:
            start = stall_at + stall
        now = start + service
        tool.append(now - t)
    truth.sort()
    tool.sort()
    assert len(tool) == 49500
    assert percentile(tool, 0.99) == pytest.approx(0.001, abs=1e-9) and percentile(tool, 0.999) == pytest.approx(0.001, abs=1e-9)
    assert tool[-1] == pytest.approx(stall + 0.001, abs=0.003)
    affected = sum(1 for x in truth if x > 0.0015)
    assert affected == pytest.approx(1000, abs=5)
    assert percentile(truth, 0.98) == pytest.approx(0.001, abs=0.005)
    assert percentile(truth, 0.99) == pytest.approx(0.5, abs=0.01)
    assert percentile(truth, 0.999) == pytest.approx(0.95, abs=0.01)
    assert sum(truth) / len(truth) == pytest.approx(0.011, abs=0.001)
    assert sum(tool) / len(tool) == pytest.approx(0.00102, abs=0.00002)


def test_q27():
    bits = (64 + 20) * 8
    assert bits == 672
    pps = 10e9 / bits
    assert pps == pytest.approx(14.88e6, abs=1e4)
    assert 1e9 / pps == pytest.approx(67.2, abs=0.01)
    assert 3 * 1e9 / pps == pytest.approx(201.6, abs=0.1)
    per_call = 1e9 / (500 + 150)  # one call per packet, at the stated costs
    assert per_call == pytest.approx(1.54e6, abs=0.01e6) and pps / per_call == pytest.approx(9.7, abs=0.1)
    batched = 500 / 32 + 150
    assert batched == pytest.approx(165.6, abs=0.1) and 1e9 / batched == pytest.approx(6.04e6, abs=0.01e6)
    assert 25e9 / bits == pytest.approx(37.2e6, abs=0.1e6)


def test_q29(rust_bins):
    out = run(rust_bins / "header").stdout.split()
    assert out[:4] == ["16", "12", "16", "24"] and out[4] == out[5]
    text = (RUST / "src/bin/header.rs").read_text(encoding="utf-8")
    rc, err, exe = rustc("header_dbg", text)
    assert rc == 0, err
    d = run(exe)
    assert d.returncode != 0 and "misaligned pointer dereference" in d.stderr
    assert '{ p.ts }' in text
    bad = text.replace('let p = Packed { seq: 1, ts: 9 };', 'let p = Packed { seq: 1, ts: 9 };\n    let r = &p.ts;\n    println!("{}", r);')
    assert bad != text
    rc, err, _ = rustc("header_ref", bad)
    assert rc != 0 and "E0793" in err


def test_q30(rust_bins):
    run(rust_bins / "mailbox")
    text = (RUST / "src/bin/mailbox.rs").read_text(encoding="utf-8")
    bounded = text.replace("unsafe impl<T> Sync for Mailbox<T> {}", "unsafe impl<T: Send> Sync for Mailbox<T> {}")
    rc, err, _ = rustc("mailbox_bound", bounded)
    assert rc != 0 and "E0277" in err and "Rc" in err
    head = text[:text.index("fn main()")]
    leak = head + ('static DROPS: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);\n'
                   'struct D;\nimpl Drop for D { fn drop(&mut self) { DROPS.fetch_add(1, Ordering::Relaxed); } }\n'
                   'fn main() { { let m = Mailbox::new(); assert!(m.put(D)); }\n'
                   'println!("{}", DROPS.load(Ordering::Relaxed)); let _ = (Rc::new(0), thread::current()); let n: Mailbox<u8> = Mailbox::new(); let _ = n.take(); }\n')
    rc, err, exe = rustc("mailbox_leak", leak)
    assert rc == 0, err
    assert run(exe).stdout.strip() == "0"
    lost = head + ("struct D(&'static str);\n"
                   'impl Drop for D { fn drop(&mut self) { println!("dropped {}", self.0); } }\n'
                   'fn main() { let m = Mailbox::new(); assert!(m.put(D("first"))); println!("{}", m.put(D("second")));\n'
                   'let _ = (Rc::new(0), thread::current(), Ordering::Relaxed); }\n')
    rc, err, exe = rustc("mailbox_lost", lost)
    assert rc == 0, err
    # The second value is gone before put answers; the first stays in the box and leaks.
    assert run(exe).stdout.splitlines() == ["dropped second", "false"]
    if HAS_NIGHTLY:
        reports = race_reports(rust_tsan("mailbox", text))
        assert any("alloc::rc::Rc" in b or "Cell<usize>" in b for b in reports)
        two = head + ('fn main() { let m: Mailbox<u64> = Mailbox::new(); let _ = Rc::new(0);\n'
                      'thread::scope(|s| { for _ in 0..2 { s.spawn(|| { for i in 0..20000 { m.put(i); m.take(); } }); } }); }\n')
        reports = race_reports(rust_tsan("mailbox_two", two))
        assert any("mailbox_two" in b and "Mailbox" in b for b in reports)


def test_q31():
    assert TSAN_RACE in tsan("seqlock_naive").stderr
    assert run(gxx("seqlock_fixed")).stdout.strip() == "0"
    r = tsan("seqlock_fixed")
    assert TSAN_RACE not in r.stderr and r.stdout.strip() == "0"
    # The writer's cost: plain stores, no locked instruction, on x86-64.
    text = (CPP / "seqlock_fixed.cpp").read_text(encoding="utf-8")
    probe = text + 'extern "C" void write_probe(SeqLock& l, const Quote& q) { l.write(q); }\n'
    body = functions(asm("seqlock_fixed", text=probe))["write_probe"]
    assert sum(i.startswith("mov") for i in body) >= 4
    assert not [i for i in body if i.startswith(("lock", "xchg", "mfence"))]


PLAIN_NEXT = """#include <atomic>
#include <cstdint>
#include <cstdio>
#include <thread>
NODE
Node pool[2];
std::atomic<std::uint64_t> head;
std::atomic<int> step{0};  // relaxed: it fixes the schedule and gives ThreadSanitizer no ordering
std::uint64_t with(std::uint64_t old, int i) { return ((old >> 32) + 1) << 32 | std::uint32_t(i); }
int main() {
    WRITE0;
    head.store(0);
    bool won = true;
    std::thread t1([&] {
        std::uint64_t seen = head.load();
        int next = READ;
        step.store(1, std::memory_order_relaxed);
        while (step.load(std::memory_order_relaxed) != 2) {}
        won = head.compare_exchange_strong(seen, with(seen, next));
    });
    std::thread t2([&] {
        while (step.load(std::memory_order_relaxed) != 1) {}
        std::uint64_t popped = with(head.load(), 1);
        head.store(popped);  // pop A
        WRITE0;              // push A back
        head.store(with(popped, 0));
        step.store(2, std::memory_order_relaxed);
    });
    t1.join();
    t2.join();
    std::printf("cas %d\\n", won);
}
"""


def test_q32():
    r = tsan("treiber")
    # Which report comes first depends on the schedule: both name the read of n->next.
    assert (TSAN_RACE in r.stderr or "ThreadSanitizer: heap-use-after-free" in r.stderr) and "treiber.cpp:23" in r.stderr
    a = gxx("treiber", ["-std=c++20", "-O1", "-g", "-fsanitize=address"], tag="_asan")
    p = run(a, timeout=120)
    assert "heap-use-after-free" in p.stderr and "treiber.cpp:23" in p.stderr
    out = run(gxx("aba_replay")).stdout.splitlines()
    assert out == ["untagged: cas 1, head 1, head in use 0, freed 1", "tagged: same index 1, cas 0"]
    assert 2**32 / 1e7 == pytest.approx(429.5, abs=0.1)
    # The tagged pool, one schedule by hand: a plain next races with a push; an atomic one, read relaxed, does not.
    plain = PLAIN_NEXT.replace("NODE", "struct Node { int next; };").replace("READ", "pool[0].next").replace("WRITE0", "pool[0].next = 1")
    r = tsan("pool_plain", text=plain)
    assert TSAN_RACE in r.stderr and r.stdout.strip() == "cas 0"
    relaxed = (PLAIN_NEXT.replace("NODE", "struct Node { std::atomic<int> next; };")
               .replace("READ", "pool[0].next.load(std::memory_order_relaxed)")
               .replace("WRITE0", "pool[0].next.store(1, std::memory_order_relaxed)"))
    r = tsan("pool_relaxed", text=relaxed)
    assert TSAN_RACE not in r.stderr and r.stdout.strip() == "cas 0"


def test_q33():
    out = run(gxx("mpmc")).stdout.splitlines()
    assert out[0] == "later pushes 7, pop while stalled 0"
    assert out[1] == "pop after resume 1 value 7"
    assert out[2] == "sum 2500050000 expected 2500050000"
    r = tsan("mpmc")
    assert TSAN_RACE not in r.stderr and "sum 2500050000 expected 2500050000" in r.stdout
    # Not only from an empty queue: two items ahead of the stalled position still come out, and five slots remain.
    text = (CPP / "mpmc.cpp").read_text(encoding="utf-8")
    ahead = text[:text.index("Mpmc<8> q;")] + (
        "Mpmc<8> r;\nint main() {\n"
        "    r.try_push(1); r.try_push(2);\n"
        "    std::size_t stalled = r.claim();\n"
        "    int later = 0;\n"
        "    for (long v = 100; r.try_push(v); ++v) ++later;\n"
        "    long a = 0, b = 0, c = 0;\n"
        "    bool one = r.try_pop(a), two = r.try_pop(b), three = r.try_pop(c);\n"
        '    std::printf("later %d, pops %d %d %d, values %ld %ld\\n", later, one, two, three, a, b);\n'
        "    r.commit(stalled, 7);\n"
        "    three = r.try_pop(c);\n"
        '    std::printf("after resume %d, value %ld\\n", three, c);\n'
        "}\n")
    assert run(gxx("mpmc_ahead", text=ahead)).stdout.splitlines() == ["later 5, pops 1 1 0, values 1 2", "after resume 1, value 7"]


def test_q34(rust_bins):
    mod = (RUST / "src/spsc_split.rs").read_text(encoding="utf-8")
    mod = mod[:mod.index("#[cfg(test)]")]
    probe = BUILD / "split_probe.rs"
    probe.write_text("mod spsc_split {\n" + mod + "}\n#[no_mangle]\npub fn push_u64(p: &mut spsc_split::Producer<u64>, v: u64) -> bool { p.push(v).is_ok() }\n", encoding="utf-8")
    out = BUILD / "split_probe.s"
    r = subprocess.run(["rustc", "--edition", "2021", "-C", "opt-level=3", "--emit=asm", "--crate-type=lib", str(probe), "-o", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert any("panic_bounds_check" in i for i in functions(out.read_text(encoding="utf-8"))["push_u64"])
    def prog(body):
        return "mod spsc_split {\n" + mod + "}\nuse spsc_split::*;\nfn main() {\n" + body + "\n}\n"
    rc, err, _ = rustc("split_clone", prog("let (p, _c) = channel::<u64>(8); let _q = p.clone();"))
    assert rc != 0 and "E0599" in err
    rc, err, _ = rustc("split_shared", prog("let (p, _c) = channel::<u64>(8); let a = std::sync::Arc::new(p); let _ = a.push(1);"))
    assert rc != 0 and "E0596" in err
    rc, err, _ = rustc("split_peek", prog("let (_p, mut c) = channel::<u64>(8); let g = c.peek(); let _ = c.pop(); drop(g);"))
    assert rc != 0 and "E0499" in err
    rc, err, _ = rustc("split_rc", prog("let (mut p, _c) = channel::<std::rc::Rc<u64>>(8); std::thread::spawn(move || { let _ = p.push(std::rc::Rc::new(1)); });"))
    assert rc != 0 and "E0277" in err
    # One unsafe impl is enough: Send is automatic, so both handles still move to another thread.
    assert mod.count("unsafe impl") == 1
    rc, err, exe = rustc("split_moves", prog(
        "let (mut p, mut c) = channel::<String>(2); p.push(\"a\".to_string()).unwrap();\n"
        "let t = std::thread::spawn(move || { p.push(\"b\".to_string()).unwrap(); p });\n"
        "let _p = t.join().unwrap();\n"
        "let t = std::thread::spawn(move || { let a = c.pop().unwrap(); let b = c.pop().unwrap(); println!(\"{a}{b}\"); });\n"
        "t.join().unwrap();"))
    assert rc == 0, err
    assert run(exe).stdout.strip() == "ab"
    # A Peek hands out &T, so sharing or moving one needs T: Sync.
    share = ("use std::cell::Cell;\n"
             "let (mut p, mut c) = channel::<Cell<u64>>(2); assert!(p.push(Cell::new(0)).is_ok());\n"
             "let g = c.peek().unwrap();\n"
             "std::thread::scope(|s| { for _ in 0..2 { s.spawn(|| { let cell: &Cell<u64> = &*g; for _ in 0..1000 { cell.set(cell.get() + 1); } }); } });\n")
    rc, err, _ = rustc("split_peek_share", prog(share))
    assert rc != 0 and "E0277" in err and "Cell<u64>" in err
    rc, err, _ = rustc("split_peek_move", prog(
        "use std::cell::Cell;\n"
        "let (mut p, mut c) = channel::<Cell<u64>>(2); assert!(p.push(Cell::new(0)).is_ok());\n"
        "let g = c.peek().unwrap();\n"
        "std::thread::scope(|s| { s.spawn(move || { g.set(1); }); });"))
    assert rc != 0 and "E0277" in err and "Cell<u64>" in err
    # The guard is still shared when the item is Sync, and Cell<u64> still crosses the queue whole.
    rc, err, exe = rustc("split_peek_sync", prog(
        "let (mut p, mut c) = channel::<String>(2); p.push(\"a\".to_string()).unwrap();\n"
        "let g = c.peek().unwrap();\n"
        "std::thread::scope(|s| { for _ in 0..2 { s.spawn(|| assert_eq!(g.as_str(), \"a\")); } });\n"
        "drop(g); println!(\"{:?}\", c.pop());\n"
        "let (mut p, mut c) = channel::<std::cell::Cell<u64>>(2); assert!(p.push(std::cell::Cell::new(5)).is_ok());\n"
        "let t = std::thread::spawn(move || c.pop().unwrap().get()); println!(\"{}\", t.join().unwrap());"))
    assert rc == 0, err
    assert run(exe).stdout.splitlines() == ["None", "5"]
    if HAS_NIGHTLY:
        stderr = rust_tsan("split", prog(
            "let (mut p, mut c) = channel::<u64>(8);\n"
            "let t = std::thread::spawn(move || { for i in 0..100000 { while p.push(i).is_err() {} } });\n"
            "let mut e = 0; while e < 100000 { if let Some(v) = c.pop() { assert_eq!(v, e); e += 1; } }\nt.join().unwrap();"))
        # A report through Arc's final drop is the fence that TSan cannot see, in a precompiled std: not ours to judge.
        ours = [b for b in race_reports(stderr) if "spsc_split" in b and "drop_slow" not in b]
        assert not ours, ours[0] if ours else ""


def test_q35(rust_bins):
    good = (RUST / "src/my_arc.rs").read_text(encoding="utf-8")
    good = good[:good.index("#[cfg(test)]")]
    bad = (RUST / "src/my_arc_bad.rs").read_text(encoding="utf-8")
    driver = ('use std::thread;\nfn main() { for _ in 0..2000 { let a = my_arc::MyArc::new(vec![1_u64; 16]); let b = a.clone();\n'
              'let t = thread::spawn(move || b.iter().sum::<u64>()); let here = a.iter().sum::<u64>(); drop(a);\n'
              'assert_eq!(t.join().unwrap() + here, 32); } println!("ok"); }\n')
    # The standard library's own form, which TSan understands: the same fetch_sub and an acquire load in place of the fence.
    seen = good.replace("fence(Ordering::Acquire);", "unsafe { self.ptr.as_ref() }.count.load(Ordering::Acquire);").replace(
        "use std::sync::atomic::{fence, AtomicUsize, Ordering};", "use std::sync::atomic::{AtomicUsize, Ordering};")
    assert seen != good
    rc, err, _ = rustc("arc_ok", "mod my_arc {\n" + seen + "}\n" + driver)
    assert rc == 0, err
    rc, err, _ = rustc("arc_rc", "mod my_arc {\n" + good + "}\nfn main() { let a = my_arc::MyArc::new(std::rc::Rc::new(1_u64)); std::thread::spawn(move || drop(a)); }\n")
    assert rc != 0 and "E0277" in err
    if HAS_NIGHTLY:
        for variant, expect in (("arc_bad", bad), ("arc_seen", seen)):
            ours = [b for b in race_reports(rust_tsan(variant, "mod my_arc {\n" + expect + "}\n" + driver)) if "my_arc" in b]
            assert bool(ours) == (variant == "arc_bad")
