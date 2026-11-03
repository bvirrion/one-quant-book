"""Reading, Debugging and Software Design: every printed listing compiles or runs, and a test shows each bug it claims.

C++ follows the chapter's rules: g++ -std=c++20 -O2 -Wall -Wextra -Werror, buggy listings included. A bug is shown by a wrong
output, a sanitizer report or a compile failure. Sanitizers on this kernel need setarch -R. Java runs through the single-file
source launcher, and C# through dotnet; a test that needs either skips with a reason when it is absent. No test asserts a timing.
"""
import csv
import os
import pathlib
import platform
import random
import re
import shutil
import statistics
import subprocess
import sys
import warnings
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
CPP, PY, RUST, JAVA, CS = HERE / "cpp", HERE / "python", HERE / "rust", HERE / "java", HERE / "csharp"
BUILD = HERE.parents[2] / "build" / "iv39"
BUILD.mkdir(parents=True, exist_ok=True)
STRICT = ["-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror"]
ASAN = ["-std=c++20", "-O1", "-g", "-fsanitize=address"]
TSAN = ["-std=c++20", "-O1", "-g", "-fsanitize=thread"]
RACE = "WARNING: ThreadSanitizer: data race"
DOTNET = shutil.which("dotnet") or str(pathlib.Path.home() / ".dotnet" / "dotnet")
HAS_DOTNET = pathlib.Path(DOTNET).exists()
HAS_JAVA = shutil.which("java") is not None and b"jdk.compiler" in subprocess.run(
    ["java", "--list-modules"], capture_output=True).stdout
needs_java = pytest.mark.skipif(not HAS_JAVA, reason="needs a JDK with the single-file source launcher")
needs_dotnet = pytest.mark.skipif(not HAS_DOTNET, reason="needs the .NET SDK")
sys.path.insert(0, str(PY))

import rd_prop_book  # noqa: E402
import rd_prop_check  # noqa: E402
import rd_read_only  # noqa: E402
import rd_replay_fixed  # noqa: E402
import rd_review  # noqa: E402
import rd_review_fixed  # noqa: E402
import rd_strategy  # noqa: E402
import rd_strategy_fixed  # noqa: E402

NONNUMERIC = {
    29: "a design judgement: no output decides it, though the listing is imported by this file and top_up really raises",
    38: "a design judgement on rolling out a wire format, with no code printed: every outside fact is a ledger row",
}


def gxx(name, flags=STRICT, text=None, extra=(), tag="", suffix=".cpp"):
    exe = BUILD / f"{name}{tag}"
    src = CPP / f"{name}{suffix}"
    if text is not None:
        src = BUILD / f"{name}{tag}{suffix}"
        src.write_text(text, encoding="utf-8")
    r = subprocess.run(["g++", *flags, f"-I{CPP}", str(src), "-o", str(exe), "-pthread", *extra], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return exe


def fails_to_compile(name, text, tag="_bad"):
    src = BUILD / f"{name}{tag}.cpp"
    src.write_text(text, encoding="utf-8")
    return subprocess.run(["g++", *STRICT, f"-I{CPP}", "-c", str(src), "-o", str(BUILD / f"{name}{tag}.o")], capture_output=True, text=True)


def run(exe, *args, timeout=60, env=None, stdin=None):
    return subprocess.run([str(exe), *map(str, args)], capture_output=True, text=True, timeout=timeout, input=stdin,
                          env={**os.environ, **(env or {})})


def san(exe, *args, timeout=120, env=None, stdin=None):
    return subprocess.run(["setarch", platform.machine(), "-R", str(exe), *map(str, args)], capture_output=True, text=True,
                          timeout=timeout, input=stdin, env={**os.environ, **(env or {})})


def source(name, suffix=".cpp"):
    return (CPP / f"{name}{suffix}").read_text(encoding="utf-8")


def py(name, text=None, tag=""):
    path = PY / f"{name}.py"
    if text is not None:
        path = BUILD / f"{name}{tag}.py"
        path.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(path)], capture_output=True, text=True, timeout=60)


def pysrc(name):
    return (PY / f"{name}.py").read_text(encoding="utf-8")


def rustc(name, text=None, flags=(), edition="2021", tag=""):
    path = RUST / "src" / "bin" / f"{name}.rs"
    if text is not None:
        path = BUILD / f"{name}{tag}.rs"
        path.write_text(text, encoding="utf-8")
    exe = BUILD / f"{name}{tag}_{edition}_rs"
    r = subprocess.run(["rustc", "--edition", edition, "-D", "warnings", *flags, str(path), "-o", str(exe)], capture_output=True, text=True)
    return r.returncode, r.stderr, exe


def java(name, text=None, tag="j"):
    path = JAVA / f"{name}.java"
    if text is not None:
        where = BUILD / tag
        where.mkdir(exist_ok=True)
        path = where / f"{name}.java"
        path.write_text(text, encoding="utf-8")
    r = subprocess.run(["java", str(path)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_every_listing_compiles():
    for name in ("unsigned_diff", "erase_loop", "map_index", "ctor_virtual", "slicing", "no_virtual_dtor", "exception_leak",
                 "temp_range", "guard_temp", "lock_order", "cv_if", "const_move", "callback_this", "callback_fixed",
                 "swapped_args", "strong_types", "uninit", "growth", "dcl"):
        gxx(name)
    r = subprocess.run(["g++", *STRICT, "-c", str(CPP / "dispatch.cpp"), "-o", str(BUILD / "dispatch.o")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for name in ("static_rates", "static_limits"):
        r = subprocess.run(["g++", *STRICT, "-c", str(CPP / f"{name}.cpp"), "-o", str(BUILD / f"{name}.o")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    gxx("book_main")
    gxx("book_main", [*STRICT, "-DFIXED"], tag="_fixed")
    t = subprocess.run(["cargo", "test", "--offline", "-q"], cwd=RUST, capture_output=True, text=True,
                       env={**os.environ, "RUSTFLAGS": "-Dwarnings", "CARGO_TARGET_DIR": str(BUILD / "rt")})
    assert t.returncode == 0, t.stdout + t.stderr


def test_q1():
    out = run(gxx("unsigned_diff")).stdout.splitlines()
    assert out == ["more bids than asks", "18446744073709551615"] and 2**64 - 1 == 18446744073709551615
    down = "int main() {\n    std::vector<int> v{1};\n    for (std::size_t i = v.size() - 1; i >= 0; --i) v[i] = 0;\n}\n"
    loop = fails_to_compile("unsigned_diff", "#include <cstddef>\n#include <vector>\n" + down, tag="_down")
    assert loop.returncode != 0 and "type-limits" in loop.stderr
    fixed = source("unsigned_diff").replace("bids.size() - asks.size() > 0", "bids.size() > asks.size()")
    assert run(gxx("unsigned_diff", text=fixed, tag="_f")).stdout.splitlines()[0] == "no more bids than asks"
    ss = source("unsigned_diff").replace("bids.size() - asks.size() > 0", "std::ssize(bids) - std::ssize(asks) > 0")
    assert run(gxx("unsigned_diff", text=ss, tag="_s")).stdout.splitlines()[0] == "no more bids than asks"


def test_q2():
    assert py("rd_late_binding").stdout.strip() == "[30, 30, 30]"
    fixed = pysrc("rd_late_binding").replace("lambda x: k * x", "lambda x, k=k: k * x")
    assert py("rd_late_binding", fixed, "_f").stdout.strip() == "[10, 20, 30]"
    gen = pysrc("rd_late_binding").replace("    scalers = []\n    for k in [1, 2, 3]:\n        scalers.append(lambda x: k * x)\n    return scalers\n",
                                           "    return [lambda x: k * x for k in [1, 2, 3]]\n")
    assert py("rd_late_binding", gen, "_c").stdout.strip() == "[30, 30, 30]"


def test_q3():
    assert run(gxx("erase_loop")).stdout.strip() == "10 0 20"
    debug = run(gxx("erase_loop", ["-std=c++20", "-O1", "-g", "-D_GLIBCXX_DEBUG"], tag="_dbg"))
    assert debug.returncode != 0 and "singular" in debug.stderr
    tail = source("erase_loop").replace("{10, 0, 0, 20}", "{10, 0}")
    r = san(gxx("erase_loop", ASAN, text=tail, tag="_tail"))
    assert "heap-buffer-overflow" in r.stderr
    fixed = re.sub(r"for \(auto it.*?\n    \}\n", "std::erase(qty, 0L);\n", source("erase_loop"), count=1, flags=re.S)
    assert "std::erase" in fixed
    assert run(gxx("erase_loop", text=fixed, tag="_f")).stdout.strip() == "10 20"


def test_q4():
    assert run(gxx("map_index")).stdout.split() == ["1", "1", "2"]
    r = fails_to_compile("map_index", source("map_index").replace("std::map<std::string, long> limits", "const std::map<std::string, long> limits"))
    assert r.returncode != 0 and "operator[]" in r.stderr
    fixed = source("map_index").replace("    return qty <= limits[symbol];\n",
                                        "    const auto it = limits.find(symbol);\n    return it != limits.end() && qty <= it->second;\n")
    assert run(gxx("map_index", text=fixed, tag="_f")).stdout.split() == ["1", "0", "1"]


def test_q5():
    assert run(gxx("ctor_virtual")).stdout.splitlines() == ["start base", "run momentum"]
    pure = source("ctor_virtual").replace('Strategy() { std::printf("start %s\\n", name()); }',
                                          'Strategy() { show(); }\n    void show() const { std::printf("start %s\\n", name()); }').replace(
        'virtual const char* name() const { return "base"; }', "virtual const char* name() const = 0;")
    r = run(gxx("ctor_virtual", ["-std=c++20", "-O0"], text=pure, tag="_pure"))
    assert r.returncode != 0 and "pure virtual method called" in r.stderr


def test_q6():
    assert run(gxx("slicing")).stdout.strip() == "0.0 101.0 0.0"
    no_copy = source("slicing").replace("virtual ~Instrument() = default;",
                                        "Instrument() = default;\n    Instrument(const Instrument&) = delete;\n    virtual ~Instrument() = default;")
    assert fails_to_compile("slicing", no_copy).returncode != 0
    fixed = source("slicing").replace("#include <vector>", "#include <memory>\n#include <vector>").replace(
        "std::vector<Instrument> book;", "std::vector<std::unique_ptr<Instrument>> book;").replace(
        "book.push_back(Bond(99.5));", "book.push_back(std::make_unique<Bond>(99.5));").replace("book[0].value()", "book[0]->value()")
    assert run(gxx("slicing", text=fixed, tag="_f")).stdout.strip() == "99.5 101.0 0.0"


def test_q7():
    rc, err, dbg = rustc("imbalance")
    assert rc == 0, err
    r = run(dbg)
    assert r.returncode != 0 and "attempt to subtract with overflow" in r.stderr
    rc, err, rel = rustc("imbalance", flags=["-C", "opt-level=3"], tag="_rel")
    assert rc == 0, err
    assert run(rel).stdout.strip() == "18446744073709551615"
    rc, err, chk = rustc("imbalance", flags=["-C", "opt-level=3", "-C", "overflow-checks=on"], tag="_chk")
    assert rc == 0, err
    assert run(chk).returncode != 0
    text = (RUST / "src/bin/imbalance.rs").read_text(encoding="utf-8")
    rc, err, exe = rustc("imbalance", text.replace("bids.len() - asks.len()", "bids.len().abs_diff(asks.len())"), tag="_abs")
    assert rc == 0, err
    assert run(exe).stdout.strip() == "1"
    probe = 'fn main() { let (a, b) = (2_usize, 3_usize); let (a, b) = (std::hint::black_box(a), std::hint::black_box(b)); println!("{:?} {}", a.checked_sub(b), a as i64 - b as i64); }\n'
    rc, err, exe = rustc("probe", probe)
    assert rc == 0, err
    assert run(exe).stdout.strip() == "None -1"


def test_q8():
    assert py("rd_float_keys").stdout.splitlines() == ["False 0", "2.67 0 2 2"]
    assert 0.1 + 0.2 == 0.30000000000000004
    from decimal import Decimal
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
    assert 100 + 200 == 300  # prices in integer ticks of 0.001
    # rounding does give one canonical double near a grid value, and stops working near the half tick
    assert round(0.1 + 0.2, 2) == 0.3 and round(1.1 + 2.2, 2) == 3.3 and 1.1 + 2.2 != 3.3
    assert round(0.125, 2) != round(0.125 + 1e-15, 2)
    assert Decimal(2.675) < Decimal("2.675") and str(Decimal(2.675)).startswith("2.67499999")


@needs_java
def test_q9():
    assert java("Boxes").splitlines() == ["true false true", "true false true"]


def test_q10():
    exe = gxx("no_virtual_dtor")
    assert run(exe).stdout.splitlines() == ["100", "~Order"]
    a = san(gxx("no_virtual_dtor", ASAN, tag="_asan"))
    assert "new-delete-type-mismatch" in a.stderr
    leak = san(gxx("no_virtual_dtor", ASAN, tag="_asan"), env={"ASAN_OPTIONS": "new_delete_type_mismatch=0"})
    assert "detected memory leaks" in leak.stderr
    raw = source("no_virtual_dtor").replace("std::unique_ptr<Order> p = std::make_unique<LimitOrder>();", "Order* p = new LimitOrder;").replace(
        'std::printf("%ld\\n", p->qty());', 'std::printf("%ld\\n", p->qty());\n    delete p;')
    w = fails_to_compile("no_virtual_dtor", raw, tag="_raw")
    assert w.returncode != 0 and "delete-non-virtual-dtor" in w.stderr
    fixed = source("no_virtual_dtor").replace("~Order() {", "virtual ~Order() {")
    assert run(gxx("no_virtual_dtor", text=fixed, tag="_f")).stdout.splitlines() == ["100", "~LimitOrder", "~Order"]
    assert san(gxx("no_virtual_dtor", ASAN, text=fixed, tag="_fa")).returncode == 0
    shared = source("no_virtual_dtor").replace("std::unique_ptr<Order> p = std::make_unique<LimitOrder>();",
                                               "std::shared_ptr<Order> p = std::make_shared<LimitOrder>();")
    assert run(gxx("no_virtual_dtor", text=shared, tag="_sh")).stdout.splitlines() == ["100", "~LimitOrder", "~Order"]
    assert san(gxx("no_virtual_dtor", ASAN, text=shared, tag="_sha")).returncode == 0  # defined, and no leak


def test_q11():
    assert run(gxx("exception_leak")).stdout.splitlines() == ["bad qty", "300"]
    r = san(gxx("exception_leak", ASAN, tag="_asan"))
    assert "detected memory leaks" in r.stderr and "handle" in r.stderr and "1 object" in r.stderr
    fixed = source("exception_leak").replace('Order* o = new Order{qty, "tag"};', 'auto o = std::make_unique<Order>(Order{qty, "tag"});').replace(
        "    delete o;\n", "").replace("#include <cstdio>", "#include <cstdio>\n#include <memory>")
    f = san(gxx("exception_leak", ASAN, text=fixed, tag="_f"))
    assert f.returncode == 0 and f.stdout.splitlines() == ["bad qty", "300"] and "leak" not in f.stderr


def test_q12():
    r = san(gxx("temp_range", ASAN, tag="_asan"))
    assert "stack-use-after-scope" in r.stderr
    # a public member of the temporary is safe: the temporary's lifetime is extended by the binding in the range-for
    member = source("temp_range").replace("private:\n", "").replace("latest().levels()", "latest().levels_")
    m = san(gxx("temp_range", ASAN, text=member, tag="_m"))
    assert m.returncode == 0 and m.stdout.strip() == "600"
    named = source("temp_range").replace("for (long q : latest().levels()) total += q;", "const Snapshot snap = latest();\n    for (long q : snap.levels()) total += q;")
    n = san(gxx("temp_range", ASAN, text=named, tag="_n"))
    assert n.returncode == 0 and n.stdout.strip() == "600"
    guarded = source("temp_range").replace("levels() const { return levels_; }", "levels() const& { return levels_; }\n    const std::vector<long>& levels() const&& = delete;")
    assert fails_to_compile("temp_range", guarded).returncode != 0


def test_q13():
    r = san(gxx("guard_temp", TSAN, tag="_tsan"))
    assert RACE in r.stderr
    fixed = source("guard_temp").replace("std::lock_guard<std::mutex>{m};", "std::lock_guard<std::mutex> lock{m};")
    f = san(gxx("guard_temp", TSAN, text=fixed, tag="_f"))
    assert RACE not in f.stderr and f.stdout.strip() == "200000"
    paren = source("guard_temp").replace("std::lock_guard<std::mutex>{m};", "std::lock_guard<std::mutex>(m);")
    assert fails_to_compile("guard_temp", paren).returncode != 0
    empty = source("guard_temp").replace("std::lock_guard<std::mutex>{m};", "std::scoped_lock lock;")
    assert RACE in san(gxx("guard_temp", TSAN, text=empty, tag="_e")).stderr


def test_q14():
    assert run(gxx("lock_order")).stdout.strip() == "1000 1000"
    r = san(gxx("lock_order", TSAN, tag="_tsan"))
    assert "lock-order-inversion" in r.stderr
    fixed = source("lock_order").replace("    std::lock_guard a(from.m);\n    std::lock_guard b(to.m);\n", "    std::scoped_lock lock(from.m, to.m);\n")
    f = san(gxx("lock_order", TSAN, text=fixed, tag="_f"))
    assert "lock-order-inversion" not in f.stderr and f.stdout.strip() == "1000 1000"
    same = fixed.replace("transfer(x, y, 1)", "transfer(x, x, 1)")
    with pytest.raises(subprocess.TimeoutExpired):
        run(gxx("lock_order", text=same, tag="_same"), timeout=3)


def test_q15():
    checked = ["-std=c++20", "-O1", "-g", "-D_GLIBCXX_ASSERTIONS"]
    exe = gxx("cv_if", checked, tag="_chk")
    results = [run(exe) for _ in range(3)]
    assert any(r.returncode == -6 for r in results)  # SIGABRT: the library's check on front() of an empty deque
    fixed = source("cv_if").replace("if (q.empty()) cv.wait(lock);", "cv.wait(lock, [] { return !q.empty(); });")
    r = run(gxx("cv_if", checked, text=fixed, tag="_f"))
    assert r.returncode == 0 and sorted(x.split()[1] for x in r.stdout.splitlines()) == ["7", "8"]
    t = san(gxx("cv_if", TSAN, text=fixed, tag="_ft"))
    assert RACE not in t.stderr


def test_q16():
    assert run(gxx("const_move")).stdout.strip() == "copies 1, moves 1"
    fixed = source("const_move").replace("explicit Holder(const Tracked item)", "explicit Holder(Tracked item)")
    assert run(gxx("const_move", text=fixed, tag="_f")).stdout.strip() == "copies 0, moves 2"
    grow = source("const_move").replace("#include <utility>", "#include <utility>\n#include <vector>").replace(
        '    Tracked t("abc");\n    Holder h(std::move(t));\n',
        '    std::vector<Tracked> v;\n    v.emplace_back("a");\n    v.emplace_back("b");\n')
    assert run(gxx("const_move", text=grow, tag="_g")).stdout.strip() == "copies 0, moves 1"
    thrower = grow.replace("Tracked(Tracked&& o) noexcept", "Tracked(Tracked&& o)")
    assert run(gxx("const_move", text=thrower, tag="_t")).stdout.strip() == "copies 1, moves 0"


def test_q17():
    assert run(gxx("callback_this")).stdout.splitlines() == ["1", "done"]
    r = san(gxx("callback_this", ASAN, tag="_asan"))
    assert "heap-use-after-free" in r.stderr
    f = san(gxx("callback_fixed", ASAN, tag="_asan"))
    assert f.returncode == 0 and f.stdout.splitlines() == ["1", "done"]
    copying = source("callback_fixed").replace('    Feed feed;\n', '    Feed feed;\n    Strategy a(feed);\n    Strategy b = a;\n')
    assert fails_to_compile("callback_fixed", copying).returncode != 0


def test_q18():
    assert py("rd_mutable_hash").stdout.strip() == "False 1 True"
    only_id = pysrc("rd_mutable_hash").replace("return hash((self.oid, self.qty))", "return hash(self.oid)").replace(
        "return (self.oid, self.qty) == (other.oid, other.qty)", "return self.oid == other.oid")
    assert py("rd_mutable_hash", only_id, "_f").stdout.strip() == "True 1 True"
    no_hash = pysrc("rd_mutable_hash").replace("    def __hash__(self):\n        return hash((self.oid, self.qty))\n", "")
    r = py("rd_mutable_hash", no_hash, "_n")
    assert r.returncode != 0 and "unhashable type" in r.stderr


def test_q19():
    assert py("rd_method_cache").stdout.split() == ["150.0", "False"]
    per_instance = pysrc("rd_method_cache").replace("    @lru_cache(maxsize=None)\n    def price(self, strike):", "    def _price(self, strike):").replace(
        "        self.curve = curve\n", "        self.curve = curve\n        self.price = lru_cache(maxsize=None)(self._price)\n")
    assert py("rd_method_cache", per_instance, "_f").stdout.split() == ["150.0", "True"]


def test_q20():
    if not pathlib.Path("/usr/share/zoneinfo/America/New_York").exists():
        pytest.skip("no time-zone data on this machine")
    assert py("rd_dst").stdout.splitlines() == ["1 day, 0:00:00", "23:00:00"]
    ny = ZoneInfo("America/New_York")
    assert datetime(2026, 3, 8, 1, 59, tzinfo=ny).utcoffset() == timedelta(hours=-5)
    assert datetime(2026, 3, 8, 3, 0, tzinfo=ny).utcoffset() == timedelta(hours=-4)
    span = datetime(2026, 11, 2, tzinfo=ny).astimezone(timezone.utc) - datetime(2026, 11, 1, tzinfo=ny).astimezone(timezone.utc)
    assert span == timedelta(hours=25) and date(2026, 3, 8).weekday() == 6 and date(2026, 11, 1).weekday() == 6


def test_q21():
    rc, err, exe = rustc("rc_cycle")
    assert rc == 0, err
    assert run(exe).stdout.splitlines() == ["2 2"]
    rc, err, exe = rustc("rc_weak")
    assert rc == 0, err
    assert run(exe).stdout.splitlines() == ["1 1", "a", "drop b", "drop a"]


def test_q22():
    rc, err, exe = rustc("guard_match")
    assert rc == 0, err
    with pytest.raises(subprocess.TimeoutExpired):
        run(exe, timeout=3)
    text = (RUST / "src/bin/guard_match.rs").read_text(encoding="utf-8")
    rc, err, exe = rustc("guard_match", edition="2024", tag="_ed")
    assert rc == 0, err
    with pytest.raises(subprocess.TimeoutExpired):
        run(exe, timeout=3)
    fixed = text.replace("match queue.lock().unwrap().pop() {", "let item = queue.lock().unwrap().pop();\n    match item {")
    rc, err, exe = rustc("guard_match", fixed, tag="_f")
    assert rc == 0, err
    assert run(exe).stdout.splitlines() == ["requeued 3", "done"]
    iflet = text.replace("match queue.lock().unwrap().pop() {\n        Some(x) => {", "if let Some(x) = queue.lock().unwrap().pop() {").replace(
        '        }\n        None => println!("empty"),\n    }', "    }")
    rc, err, exe = rustc("guard_match", iflet, edition="2024", tag="_if")
    assert rc == 0, err
    with pytest.raises(subprocess.TimeoutExpired):  # the 2024 change drops the guard before an else, not before the body
        run(exe, timeout=3)


@needs_java
def test_q23():
    assert java("EqualsOnly").splitlines() == ["true", "null"]
    text = (JAVA / "EqualsOnly.java").read_text(encoding="utf-8")
    fixed = text.replace("        @Override public boolean equals(Object o) {", "        @Override public int hashCode() { return symbol.hashCode(); }\n\n        @Override public boolean equals(Object o) {")
    assert java("EqualsOnly", fixed).splitlines() == ["true", "1000"]
    both = fixed.replace("final String symbol;", "String symbol;").replace('        limits.put(new Key("AAA"), 1000L);\n',
                                                                          '        Key k = new Key("AAA");\n        limits.put(k, 1000L);\n        k.symbol = "BBB";\n')
    assert java("EqualsOnly", both, tag="j2").splitlines() == ["true", "null"]
    # two keys in one bucket (hash codes 1 and 17, in a table of 16): the stored hash is compared first, so no equals runs
    bucket = """import java.util.HashMap;

public class EqualsOnly {
    static int calls = 0;

    static class K {
        final int h;
        K(int h) { this.h = h; }
        @Override public int hashCode() { return h; }
        @Override public boolean equals(Object o) { calls++; return true; }
    }

    public static void main(String[] args) {
        HashMap<K, Long> m = new HashMap<>();
        m.put(new K(1), 1000L);
        System.out.println(m.get(new K(17)));
        System.out.println(calls);
        System.out.println(m.get(new K(1)));
        System.out.println(calls);
    }
}
"""
    assert java("EqualsOnly", bucket, tag="j3").splitlines() == ["null", "0", "1000", "1"]


@needs_java
def test_q24():
    finals = [int(java("LostMerge")) for _ in range(3)]
    assert all(v <= 400000 for v in finals) and min(finals) < 400000
    text = (JAVA / "LostMerge.java").read_text(encoding="utf-8")
    fixed = text.replace("        Long old = position.get(symbol);\n        position.put(symbol, (old == null ? 0L : old) + qty);\n",
                         "        position.merge(symbol, qty, Long::sum);\n")
    assert "merge" in fixed
    assert int(java("LostMerge", fixed)) == 400000


def dotnet_run(text=None, tag="base"):
    where = BUILD / f"cs_{tag}"
    where.mkdir(exist_ok=True)
    (where / "EventLeak.csproj").write_text((CS / "EventLeak" / "EventLeak.csproj").read_text(encoding="utf-8"), encoding="utf-8")
    (where / "Program.cs").write_text(text or (CS / "EventLeak" / "Program.cs").read_text(encoding="utf-8"), encoding="utf-8")
    env = {**os.environ, "DOTNET_NOLOGO": "1", "DOTNET_CLI_TELEMETRY_OPTOUT": "1"}
    b = subprocess.run([DOTNET, "build", "-c", "Release", "-o", str(where / "out")], cwd=where, capture_output=True, text=True, env=env, timeout=200)
    assert b.returncode == 0, b.stdout
    return subprocess.run([DOTNET, str(where / "out" / "EventLeak.dll")], capture_output=True, text=True, timeout=60, env=env).stdout.strip()


@needs_dotnet
def test_q25():
    assert dotnet_run() == "True"
    text = (CS / "EventLeak" / "Program.cs").read_text(encoding="utf-8")
    fixed = text.replace("class Strategy {", "class Strategy : IDisposable {\n    readonly Feed feed;").replace(
        "public Strategy(Feed feed) { feed.Tick += OnTick; }", "public Strategy(Feed feed) { this.feed = feed; feed.Tick += OnTick; }\n    public void Dispose() { feed.Tick -= OnTick; }").replace(
        "static WeakReference Make(Feed feed) => new WeakReference(new Strategy(feed));",
        "static WeakReference Make(Feed feed) { using var s = new Strategy(feed); return new WeakReference(s); }")
    assert dotnet_run(fixed, "fixed") == "False"


def test_q26():
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(PY / "rd_vwap_weak.py")],
                       capture_output=True, text=True, env=env, cwd=BUILD)
    assert "3 passed" in r.stdout
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        compile(pysrc("rd_vwap_weak"), "rd_vwap_weak.py", "exec")
    assert any("always true" in str(w.message) for w in caught)
    # the same tests, written to fail on this function
    def vwap(trades):
        return sum(price for price, _ in trades) / len(trades)
    assert vwap([(100.0, 10), (102.0, 30)]) == 101.0 and (100.0 * 10 + 102.0 * 30) / 40 == 101.5
    def right(trades):
        q = sum(q for _, q in trades)
        if q == 0:
            raise ValueError("no quantity")
        return sum(p * q for p, q in trades) / q
    assert right([(100.0, 10), (102.0, 30)]) == 101.5 and right([(100.0, 7)]) == 100.0
    with pytest.raises(ValueError):
        right([])
    # scaling every quantity leaves the answer alone, and it lies between the lowest and highest price
    rng = random.Random(26)
    for _ in range(200):
        ts = [(float(rng.randint(90, 110)), rng.randint(1, 9)) for _ in range(rng.randint(1, 8))]
        v = right(ts)
        assert min(p for p, _ in ts) <= v <= max(p for p, _ in ts)
        assert right([(p, 3 * q) for p, q in ts]) == pytest.approx(v)


def test_q27():
    assert run(gxx("swapped_args")).stdout.strip() == "101 at 500"
    assert run(gxx("strong_types")).stdout.splitlines() == ["500 at 101", "50500 50500"]
    swapped = source("strong_types").replace("send(price, qty);", "send(qty, price);")
    assert fails_to_compile("strong_types", swapped).returncode != 0
    s = subprocess.run(["g++", "-std=c++20", "-O2", "-S", "-o", "-", str(CPP / "strong_types.cpp")], capture_output=True, text=True).stdout
    def body(name):
        lines = s.split(f"\n{name}:\n")[1].split(".cfi_endproc")[0].splitlines()
        return [x.strip() for x in lines if x.strip() and x.startswith("\t") and not x.startswith("\t.") and "endbr64" not in x]
    raw, typed = body("_Z8cost_rawll"), body("_Z10cost_typed5Price3Qty")
    assert raw == typed and len(raw) == 3 and raw[0].startswith("movq") and raw[1].startswith("imulq") and raw[2] == "ret"
    none = subprocess.run(["g++", "-std=c++20", "-O2", "-fcf-protection=none", "-S", "-o", "-", str(CPP / "strong_types.cpp")], capture_output=True, text=True).stdout
    assert "endbr64" not in none  # the extra instruction comes from the default flags
    hole = source("strong_types").replace("send(price, qty);", "send({500}, {101});")
    assert run(gxx("strong_types", text=hole, tag="_hole")).stdout.splitlines()[0] == "101 at 500"
    tight = source("strong_types").replace("struct Price { long ticks; };", "struct Price { explicit Price(long t) : ticks(t) {} long ticks; };").replace(
        "struct Qty { long lots; };", "struct Qty { explicit Qty(long l) : lots(l) {} long lots; };").replace("send(price, qty);", "send({500}, {101});")
    assert fails_to_compile("strong_types", tight, tag="_tight").returncode != 0


def bisect_once(first_bad, runs, rng):
    """One search over commits 0..1024: 0 is good, 1024 bad. Returns (found, test runs). A bad commit fails 1 run in 4."""
    good, bad, total = 0, 1024, 0
    while bad - good > 1:
        mid = (good + bad) // 2
        fails = False
        for _ in range(runs):
            total += 1
            if mid >= first_bad and rng.random() < 0.25:
                fails = True
                break
        if fails:
            bad = mid
        else:
            good = mid
    return bad, total


def test_q28():
    assert 2**10 == 1024 and 10 * 6 == 60
    miss = lambda r: 0.75**r  # noqa: E731
    assert (1 - miss(24)) ** 10 >= 0.99 > (1 - miss(23)) ** 10
    assert 0.75**24 == pytest.approx(0.001, abs=0.00001)
    assert (1 - miss(24)) ** 10 == pytest.approx(0.9900, abs=0.0001) and (1 - miss(23)) ** 10 == pytest.approx(0.987, abs=0.001)
    assert miss(4) == pytest.approx(0.32, abs=0.01) and (1 - miss(4)) ** 5 < 0.5  # four runs: wrong more often than right
    assert 10 * 24 * 6 == 1440  # the worst case, in minutes: 24 hours
    per_bad = sum(0.75**k for k in range(24))  # expected runs on a bad commit, stopping at the first failure
    assert per_bad == pytest.approx(4.0, abs=0.01)
    assert (5 * 24 + 5 * per_bad) * 6 == pytest.approx(840, abs=1)  # about 14 hours for a typical path
    rng = random.Random(28)
    hit, runs = 0, []
    for _ in range(4000):
        first = rng.randint(1, 1024)
        found, n = bisect_once(first, 24, rng)
        hit += found == first
        runs.append(n)
    assert hit / 4000 > 0.99
    assert statistics.mean(runs) == pytest.approx(5 * 24 + 5 * 4, abs=6)
    worst = 0
    for _ in range(4000):
        found, _ = bisect_once(1, 24, rng)  # every commit tested is bad: the path the 99% was computed for
        worst += found == 1
    assert 0.98 < worst / 4000 <= 1.0


def test_q30():
    assert run(gxx("uninit")).stdout.strip() == "200"
    r = run(gxx("uninit"), env={"MALLOC_PERTURB_": "165"})
    assert r.stdout.strip() == "1"  # both fields start at 0x5a5a5a5a5a5a5a5a, the complement of 165 in every byte
    fixed = source("uninit").replace("return new Stats;", "return new Stats{};")
    assert run(gxx("uninit", text=fixed, tag="_f"), env={"MALLOC_PERTURB_": "165"}).stdout.strip() == "200"
    if platform.libc_ver() == ("glibc", "2.35"):  # a block from the per-thread cache is not filled, unless the cache is off
        reused = """#include <cstdio>
#include <cstdlib>
#include <cstring>
struct Stats { long count; long sum; };
int main() {
    void* p = std::malloc(16);
    std::memset(p, 0x11, 16);
    std::free(p);
    Stats* s = new Stats;
    std::printf("%lx\\n", s->sum);
}
"""
        exe = gxx("uninit_reused", ["-std=c++20", "-O0"], text=reused)
        fill = "5a5a5a5a5a5a5a5a"
        assert run(exe, env={"MALLOC_PERTURB_": "165"}).stdout.strip() != fill
        off = {"MALLOC_PERTURB_": "165", "GLIBC_TUNABLES": "glibc.malloc.tcache_count=0"}
        assert run(exe, env=off).stdout.strip() == fill
    no_msan = subprocess.run(["g++", "-std=c++20", "-fsanitize=memory", str(CPP / "uninit.cpp"), "-o", str(BUILD / "msan")], capture_output=True, text=True)
    assert no_msan.returncode != 0


def test_q31():
    r = san(gxx("growth", ASAN, tag="_asan"))
    assert r.returncode == 0 and r.stdout.strip() == "100000" and "leak" not in r.stderr
    real = source("growth").replace("void on_fill(long id) { done.emplace(id, Order{id, {}}); }", "void on_fill(long id) { new Order{id, {}}; }").replace(
        "std::printf(\"%zu\\n\", done.size());", "std::printf(\"%zu\\n\", done.size());")
    leak = san(gxx("growth", ["-std=c++20", "-O0", "-g", "-fsanitize=address"], text=real, tag="_real"))
    assert "detected memory leaks" in leak.stderr
    # a large block is mapped directly: uordblks does not see it, and hblkhd does
    big = """#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <malloc.h>
int main() {
    const auto before = mallinfo2();
    char* p = static_cast<char*>(std::malloc(200u << 20));
    std::memset(p, 1, 200u << 20);
    const auto after = mallinfo2();
    std::printf("%zu %zu\\n", after.uordblks - before.uordblks, after.hblkhd - before.hblkhd);
    std::free(p);
}
"""
    uord, mapped = run(gxx("mallinfo_big", ["-std=c++20", "-O0"], text=big)).stdout.split()
    assert int(uord) < 1 << 16 and int(mapped) >= 200 << 20


def test_q32():
    r = san(gxx("dcl", TSAN, tag="_tsan"))
    assert RACE in r.stderr
    magic = source("dcl").replace("Config* instance = nullptr;\nstd::mutex m;\n", "").replace(
        '    if (instance == nullptr) {\n        std::lock_guard lock(m);\n        if (instance == nullptr) instance = new Config;\n    }\n    return instance;\n',
        "    static Config instance;\n    return &instance;\n")
    f = san(gxx("dcl", TSAN, text=magic, tag="_f"))
    assert RACE not in f.stderr and f.stdout.strip() == "1000"
    atom = source("dcl").replace("#include <cstdio>", "#include <atomic>\n#include <cstdio>").replace(
        "Config* instance = nullptr;", "std::atomic<Config*> instance{nullptr};").replace(
        '    if (instance == nullptr) {\n        std::lock_guard lock(m);\n        if (instance == nullptr) instance = new Config;\n    }\n    return instance;\n',
        '    Config* p = instance.load(std::memory_order_acquire);\n    if (p == nullptr) {\n        std::lock_guard lock(m);\n        p = instance.load(std::memory_order_relaxed);\n'
        '        if (p == nullptr) {\n            p = new Config;\n            instance.store(p, std::memory_order_release);\n        }\n    }\n    return p;\n')
    a = san(gxx("dcl", [*TSAN, "-fsanitize=thread"], text=atom, tag="_a"), env={"TSAN_OPTIONS": "report_signal_unsafe=0"})
    assert RACE not in a.stderr and a.stdout.strip() == "1000"
    src = BUILD / "guard.cpp"
    src.write_text("long make();\nlong& get() {\n    static long v = make();\n    return v;\n}\n", encoding="utf-8")
    asm = subprocess.run(["g++", "-std=c++20", "-O2", "-S", "-o", "-", str(src)], capture_output=True, text=True).stdout
    assert "__cxa_guard_acquire" in asm and "_ZGVZ3getvE1v" in asm


def test_q33():
    objs = {}
    for n in ("static_main", "static_rates", "static_limits"):
        objs[n] = BUILD / f"{n}.o"
        r = subprocess.run(["g++", *STRICT, "-c", str(CPP / f"{n}.cpp"), "-o", str(objs[n])], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    def link(order, name):
        exe = BUILD / name
        r = subprocess.run(["g++", *[str(objs[o]) for o in order], "-o", str(exe)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return run(exe).stdout.strip()
    assert link(["static_main", "static_rates", "static_limits"], "si_a") == "1000"
    assert link(["static_main", "static_limits", "static_rates"], "si_b") == "0"
    # the function-local static: right in both orders
    rates = BUILD / "fix_rates.cpp"
    rates.write_text('#include <cstdlib>\nlong& base_rate() {\n    static long v = [] {\n        const char* s = std::getenv("BASE_RATE");\n'
                     '        return s ? std::atol(s) : 100L;\n    }();\n    return v;\n}\n', encoding="utf-8")
    limits = BUILD / "fix_limits.cpp"
    limits.write_text("long& base_rate();\nlong limit = base_rate() * 10;\n", encoding="utf-8")
    for pair, name in (((rates, limits), "si_c"), ((limits, rates), "si_d")):
        r = subprocess.run(["g++", *STRICT, str(CPP / "static_main.cpp"), *map(str, pair), "-o", str(BUILD / name)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert run(BUILD / name).stdout.strip() == "1000"
    # constinit turns the order bug into a compile error
    bad = BUILD / "ci.cpp"
    bad.write_text("extern long base_rate;\nconstinit long limit = base_rate * 10;\n", encoding="utf-8")
    assert subprocess.run(["g++", *STRICT, "-c", str(bad), "-o", str(BUILD / "ci.o")], capture_output=True).returncode != 0


def test_q34():
    s = subprocess.run(["g++", "-std=c++20", "-O2", "-S", "-o", "-", str(CPP / "dispatch.cpp")], capture_output=True, text=True).stdout
    def body(symbol):
        part = s.split(f"\n{symbol}:\n")[1].split(".cfi_endproc")[0]
        return [x.strip() for x in part.splitlines() if x.strip() and x.startswith("\t") and not x.startswith("\t.") and "endbr64" not in x]
    virt = body("_Z10by_virtualRK6Signall")
    assert any(re.match(r"(jmp|call)\s+\*", i) for i in virt)
    final = body("_Z8by_finalRK8Momentuml")
    assert not any(i.startswith(("call", "jmp")) for i in final) and len(final) <= 3
    tmpl = body("_Z11by_templateI8MomentumElRKT_l")
    assert not any(i.startswith(("call", "jmp")) for i in tmpl) and tmpl == final
    variant = body("_Z10by_variantRKSt7variantIJ8Momentum5CarryEEl")
    version = subprocess.run(["g++", "-dumpversion"], capture_output=True, text=True).stdout.strip()
    if version.startswith("11"):  # libstdc++ 11 builds a table of function pointers for this std::visit
        assert any(re.match(r"call\s+\*", i) for i in variant), variant
    switch = body("_Z9by_switchRKSt7variantIJ8Momentum5CarryEEl")
    assert not any(re.match(r"(jmp|call)\s+\*", i) for i in switch), switch
    assert any(i.startswith(("cmp", "test")) for i in switch), switch
    assert len([i for i in switch if i.startswith(("cmp", "test"))]) == 2 and len([i for i in switch if i.startswith("j")]) == 2, switch
    assert "bad_variant_access" in s.split("\n_Z9by_switchRKSt7variantIJ8Momentum5CarryEEl.cold:\n")[1].split(".cfi_endproc")[0]  # the cold path
    assert len(final) == 2  # the two lines: the endbr64 is filtered out above


def test_q35():
    assert py("rd_replay").stdout.strip() == "40"
    assert 100 - 30 == 70
    p = rd_replay_fixed.Position()
    for f in [{"seq": 1, "side": "B", "qty": 100}, {"seq": 2, "side": "S", "qty": 30}, {"seq": 2, "side": "S", "qty": 30}]:
        p.on_fill("s", f)
    assert p.qty == 70
    with pytest.raises(RuntimeError):
        p.on_fill("s", {"seq": 4, "side": "B", "qty": 1})
    p.on_fill("t", {"seq": 1, "side": "B", "qty": 5})  # a sequence is per session
    assert p.qty == 75
    rng = random.Random(35)
    for _ in range(200):
        fills = [{"seq": i + 1, "side": rng.choice("BS"), "qty": rng.randint(1, 9)} for i in range(rng.randint(1, 20))]
        truth = sum(f["qty"] if f["side"] == "B" else -f["qty"] for f in fills)
        p = rd_replay_fixed.Position()
        done = 0
        while done < len(fills):
            for f in fills[max(0, done - rng.randint(0, 3)) : done + 1]:  # a resend of the last few, then one new
                p.on_fill("s", f)
            done += 1
        assert p.qty == truth


class Gateway:
    def __init__(self):
        self.sent = []

    def send(self, price):
        self.sent.append(price)


def test_q36():
    ticks = [(t * 2.0, 100.0 + t) for t in range(5)]  # one tick every 2 s of market time, each above the level
    g = Gateway()
    live = rd_strategy.Throttled(g, 50.0)
    for _, price in ticks:  # replayed as fast as the machine runs: the wall clock barely moves
        live.on_tick(price)
    assert len(g.sent) == 1
    def replay():
        clock, g2 = rd_strategy_fixed.SimClock(), Gateway()
        s = rd_strategy_fixed.Throttled(clock, g2, 50.0)
        for t, price in ticks:
            clock.t = t
            s.on_tick(price)
        return g2.sent
    assert replay() == [100.0, 101.0, 102.0, 103.0, 104.0] and replay() == replay()


class FixedBook(rd_prop_book.Book):
    def add(self, oid, price, qty):
        assert oid not in self.orders
        super().add(oid, price, qty)

    def cancel(self, oid):
        price, qty = self.orders.pop(oid)
        self.levels[price] -= qty
        if self.levels[price] == 0:
            del self.levels[price]


def test_q37():
    rd_prop_book.test_add_then_best()
    rd_prop_book.test_cancel_lower()
    bad = rd_prop_check.check(rd_prop_book.Book)
    assert bad is not None and len(bad) == 2
    assert [op[0] for op in bad] == ["a", "c"] and bad[0][1] == bad[1][1]
    assert rd_prop_check.check(FixedBook, runs=1000) is None
    # that holds because the generator never re-adds a live id: without the guard, the lots of the first order are stranded
    b = FixedBook()
    rd_prop_book.Book.add(b, 1, 100, 5)
    rd_prop_book.Book.add(b, 1, 101, 5)
    assert b.levels == {100: 5, 101: 5} and b.orders == {1: (101, 5)}
    b.cancel(1)
    assert b.best() == 100 and not b.orders


def book_model(script, better):
    """A slow model of one side: price -> list of [id, qty]."""
    levels, out = {}, []
    live = set()
    def best():
        return better(levels) if levels else -1
    for line in script:
        p = line.split()
        if p[0] == "a":
            levels.setdefault(int(p[1]), []).append([int(p[2]), int(p[3])])
            live.add(int(p[2]))
            res = 0
        elif p[0] == "c":
            i = int(p[1])
            res = int(i in live)
            live.discard(i)
            for price in list(levels):
                levels[price] = [o for o in levels[price] if o[0] != i]
                if not levels[price]:
                    del levels[price]
        else:
            want, res = int(p[1]), 0
            while want and levels:
                b = better(levels)
                o = levels[b][0]
                n = min(o[1], want)
                o[1] -= n
                want -= n
                res += n
                if o[1] == 0:
                    live.discard(o[0])
                    levels[b].pop(0)
                    if not levels[b]:
                        del levels[b]
        out.append(f"{res} {best()}")
    return out


def test_q39():
    main = "book_main"
    a = gxx(main, ASAN, tag="_asan")
    # bug 1: a second order at a level reallocates the vector, and the first order's pointer dangles
    r = san(a, stdin="a 100 1 5\na 100 2 5\nc 1\n")
    assert "heap-use-after-free" in r.stderr and "cancel" in r.stderr
    # bug 2: the level is erased inside the range-for that is walking the map
    # ASan is silent here (_Rb_tree_increment lives in the uninstrumented libstdc++), so the debug containers show it
    assert san(a, stdin="a 100 1 5\na 101 2 5\nt 7\n").returncode == 0
    r = run(gxx(main, ["-std=c++20", "-O1", "-g", "-D_GLIBCXX_DEBUG"], tag="_dbg"), stdin="a 100 1 5\na 101 2 5\nt 7\n")
    assert r.returncode != 0 and "singular" in r.stderr
    # bug 3: on the bid side the worst price is taken first (the level is not erased, so nothing crashes)
    plain = gxx(main)
    out = run(plain, stdin="a 100 1 5\na 101 2 5\nt 3\n").stdout.splitlines()
    assert out[-1].split() == ["3", "100"]  # it filled at 100, and a buyer's bid of 101 should have gone first
    # and a cancel leaves an empty level behind, so the best price is one nobody is quoting
    assert run(plain, stdin="a 100 1 5\nc 1\n").stdout.splitlines()[-1].split() == ["1", "100"]
    # a take erases each spent level it visits, on the way to where it fills
    assert run(plain, stdin="a 100 1 5\nc 1\na 101 2 5\nt 3\n").stdout.splitlines()[-1].split() == ["3", "101"]
    # deeper in the book the empty entry stays, under a level that still has quantity
    assert run(plain, stdin="a 100 1 5\na 101 2 5\nc 2\nt 3\nt 2\n").stdout.splitlines()[-2:] == ["3 100", "2 101"]
    fixed_bid = gxx(main, [*ASAN, "-DFIXED", "-DBID"], tag="_fb")
    fixed_ask = gxx(main, [*ASAN, "-DFIXED"], tag="_fa")
    out = san(fixed_bid, stdin="a 100 1 5\na 101 2 5\nt 3\n").stdout.splitlines()
    assert out[-1].split() == ["3", "101"]
    rng = random.Random(39)
    for exe, better in ((fixed_ask, min), (fixed_bid, max)):
        for _ in range(30):
            script, nid = [], 1
            for _ in range(150):
                x = rng.random()
                if x < 0.5:
                    script.append(f"a {rng.randint(95, 105)} {nid} {rng.randint(1, 9)}")
                    nid += 1
                elif x < 0.75:
                    script.append(f"c {rng.randint(1, nid)}")
                else:
                    script.append(f"t {rng.randint(1, 12)}")
            r = san(exe, stdin="\n".join(script) + "\n")
            assert r.returncode == 0, r.stderr
            assert r.stdout.splitlines() == book_model(script, better)


def test_q40(tmp_path):
    day1, day2, bad = tmp_path / "d1.csv", tmp_path / "d2.csv", tmp_path / "bad.csv"
    day1.write_text("symbol,price,qty\nAAA,100,10\nAAA,102,30\n", encoding="utf-8")
    day2.write_text("symbol,price,qty\nAAA,200,10\n", encoding="utf-8")
    bad.write_text("symbol,price,qty\nAAA,100,10\nAAA,oops,5\nBBB,50,0\n", encoding="utf-8")
    rd_review.totals.clear()
    rd_review.load(str(day1))
    assert rd_review.vwap("AAA") == 101.5
    rd_review.load(str(day2))
    assert rd_review.vwap("AAA") == pytest.approx(121.2)  # day 2 alone is 200: the hidden global has mixed the days
    rd_review.totals.clear()
    with pytest.raises(ValueError):
        rd_review.load(str(bad))
    rd_review.totals.clear()
    (tmp_path / "zero.csv").write_text("symbol,price,qty\nAAA,100,10\nAAA,100,-10\n", encoding="utf-8")
    rd_review.load(str(tmp_path / "zero.csv"))
    with pytest.raises(ZeroDivisionError):
        rd_review.vwap("AAA")
    rd_review.totals.clear()
    assert sum([0.1] * 10) != 1.0
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rd_review.load(str(day1))
        import gc
        gc.collect()
    assert any(issubclass(w.category, ResourceWarning) for w in caught)
    rd_review.totals.clear()
    f = rd_review_fixed
    a, e = f.report(str(day1))
    assert a == {"AAA": 101.5} and e == []
    a, e = f.report(str(day2))
    assert a == {"AAA": 200}
    a, e = f.report(str(bad))
    assert a["AAA"] == 100 and a["BBB"] is None and len(e) == 1 and e[0][0] == 2
    # bad rows of every kind are counted, and the report survives them
    worse = tmp_path / "worse.csv"
    worse.write_text("symbol,price,qty\nAAA,100,10\nAAA,101\nAAA\nAAA,1/0,5\nAAA,oops,5\nBBB,50,2\n", encoding="utf-8")
    a, e = f.report(str(worse))
    assert a == {"AAA": 100, "BBB": 50} and [n for n, _ in e] == [2, 3, 4, 5]
    # a NUL byte stops the reader itself, on this Python
    nul = tmp_path / "nul.csv"
    nul.write_bytes(b"symbol,price,qty\nAAA,1\x00,5\n")
    if sys.version_info[:2] == (3, 10):
        with pytest.raises(csv.Error):
            f.report(str(nul))
    ts = [f.Trade("X", f.Fraction("0.1"), 1)] * 10
    assert f.vwaps(ts)["X"] == f.Fraction(1, 10)
    rng = random.Random(40)
    for _ in range(100):
        ts = [f.Trade(rng.choice("AB"), f.Fraction(rng.randint(90, 110)), rng.randint(1, 9)) for _ in range(rng.randint(1, 12))]
        got = f.vwaps(ts)
        rng.shuffle(ts)
        assert f.vwaps(ts) == got  # order does not matter
        assert f.vwaps(ts) == got  # and a second call on the same input changes nothing


def test_read_only_listing_really_raises():
    b = rd_read_only.Book()
    assert rd_read_only.top_up(b, 1, 5) == 5
    with pytest.raises(NotImplementedError):
        rd_read_only.top_up(rd_read_only.ReplayBook(), 1, 5)
