"""C++: every printed program is built under the chapter's rules and its output compared; bugs meet a sanitizer.

Each printed file builds with g++ 11.4, -std=c++20 -O2 -Wall -Wextra -Werror, except where a test says otherwise. Files with
a pragma on line 1 keep the warning off on purpose and are printed from line 2. A class written from scratch meets the standard
one on random operations in a driver that is not printed. Sanitizers run under setarch -R, which this kernel needs.
Question numbers appear here only as test_q<N> and NONNUMERIC keys. No test asserts a timing.
"""
import concurrent.futures
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
BUILD = HERE.parents[2] / "build" / "iv33"
BUILD.mkdir(parents=True, exist_ok=True)
FLAGS = {
    "s": ["-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror"],
    "a": ["-std=c++20", "-O1", "-g", "-fsanitize=address,undefined"],
    "t": ["-std=c++20", "-O1", "-g", "-fsanitize=thread"],
}
NONNUMERIC = {}
PREBUILD = """storage ref_rebind array_param promote vector_init member_order overload_zero remove_only accumulate_int
range_copy buffer_bad:a buffer_five buffer_five:a no_move vec_noexcept moved_from elision forwarding collapse sv_temp:a sv_cstr
cycle cycle:a cycle_fixed cycle_fixed:a unique_main unique_main:a make_shared_weak two_owners:a share_this vec_ref:a vec_bool
vec_bool_race:t stability emplace sort_le:a overflow_check overflow_check:a shift_abs shift_abs:a lifetime:a default_args sizes
concepts msg_variant variant_valueless key_hash naive_vec:a growth opt_main opt_main:a misaligned:a pool_main pool_main:a
arena_main arena_main:a pmr_use assign_bad:a assign_good:a aliasing max_dangle:a shared_race:t shared_copies:t bq_main bq_main:t
constexpr_table crtp vec_main vec_main:a rc_main:a rc_main:t fn_main fn_main:a var_main var_main:a expr_main expr_dangle:a
value_cpp max_dangle terminate choose""".split()


def exe(spec):
    name, _, mode = spec.partition(":")
    mode = mode or "s"
    src = CPP / f"{name}.cpp"
    out = BUILD / f"{name}_{mode}"
    deps = [src, *CPP.glob("*.hpp")]
    if not out.exists() or out.stat().st_mtime < max(d.stat().st_mtime for d in deps):
        r = subprocess.run(["g++", *FLAGS[mode], "-pthread", "-I", str(CPP), str(src), "-o", str(out)],
                           capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stderr[:2000]
    return out


@pytest.fixture(scope="module", autouse=True)
def built():
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        list(pool.map(exe, PREBUILD))


def run(spec, *args, stdin=None):
    return subprocess.run(["setarch", platform.machine(), "-R", str(exe(spec)), *args], capture_output=True,
                          text=True, input=stdin, timeout=120)


def out(spec, *args):
    r = run(spec, *args)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def report(spec, *args):
    r = run(spec, *args)
    return r.returncode, r.stdout, r.stderr


def compiles(name, line):
    """Does the listing compile once `line` replaces its marker? Syntax only; warnings do not count."""
    text = (CPP / f"{name}.cpp").read_text()
    assert "// try each line here" in text
    path = BUILD / f"try_{name}.cpp"
    path.write_text(text.replace("// try each line here", line))
    r = subprocess.run(["g++", "-std=c++20", "-fsyntax-only", "-I", str(CPP), str(path)], capture_output=True, text=True, timeout=120)
    return r.returncode == 0


def test_q1():
    want = {"*p = 3;": False, "p = &b;": True, "*q = 3;": True, "q = &b;": False, "*r = 3;": False, "r = &b;": False}
    assert {line: compiles("ptr_const", line) for line in want} == want


def test_q2():
    assert out("storage").split() == "+global +static +auto -auto +auto -auto +heap end -static -global".split()


def test_q3():
    want = {"(void)S{}.x;": True, "(void)C{}.get();": True, "(void)C{}.x;": False, "(void)FromC{}.get();": True,
            "(void)FromS{}.x;": False}
    assert {line: compiles("class_struct", line) for line in want} == want


def test_q4():
    assert out("ref_rebind").splitlines() == ["2 3 2", "2 4 4"]


def test_q5():
    assert out("array_param").split() == ["40", "8", "10"]


def test_q6():
    assert out("promote").splitlines() == ["300 4", "44", "A 65 65"]
    assert (200 + 100) % 256 == 44
    warns = lambda *f: subprocess.run(["g++", "-std=c++20", "-Wall", "-Wextra", *f, "-c", str(CPP / "promote.cpp"), "-o", str(BUILD / "promote_w.o")],  # noqa: E731
                                      capture_output=True, text=True).stderr
    assert "warning" not in warns() and "warning" not in warns("-Wconversion") and "warning" in warns("-Wconversion", "-Warith-conversion")


def test_q7():
    assert out("vector_init").splitlines() == ["3 2 3 1", "1 3 0 3"]


def test_q8():
    assert out("member_order").split() == "+a +b body -b -a".split()


def test_q9():
    assert out("overload_zero").split() == "int pointer pointer pointer int".split()


def test_q10():
    assert out("remove_only").splitlines() == ["5: 1 2 3 0 3", "3"]


def test_q11():
    assert out("accumulate_int").split() == ["0", "1.8"]
    assert int(int(0 + 0.6) + 0.6) == 0
    # the same trap on long values: each step is computed in long and cut down to int, modulo 2^32 in C++20
    r = snippet("acc_long", """#include <iostream>
#include <numeric>
#include <vector>
int main() {
    std::vector<long> v{3'000'000'000L, 1L};
    std::cout << std::accumulate(v.begin(), v.end(), 0) << " " << std::accumulate(v.begin(), v.end(), 0L) << "\\n";
}
""", "-Wall", "-Wextra", "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=undefined")
    assert r.returncode == 0 and r.stdout.split() == [str(3_000_000_001 - 2**32), "3000000001"]  # and no signed overflow reported


def test_q12():
    assert out("range_copy").splitlines() == ["1 2", "10 20", "10 7"]


def test_q13():
    code, _, err = report("buffer_bad:a")
    assert code != 0 and "heap-use-after-free" in err
    assert out("buffer_five").split() == ["2", "0", "5", "0"] and out("buffer_five:a").split() == ["2", "0", "5", "0"]


def test_q14():
    assert out("no_move").splitlines() == ["0 1", "1 0"]
    # an empty destructor stops a type being trivially copyable, which changes how it is passed
    path = BUILD / "snip_triv.cpp"
    path.write_text("""#include <type_traits>
struct A { int x; };
struct B { int x; ~B() {} };
static_assert(std::is_trivially_copyable_v<A> && !std::is_trivially_copyable_v<B>);
int fa(A a) { return a.x; }
int fb(B b) { return b.x; }
""")
    text = asm(path)
    assert "%edi" in body(text, "_Z2fa1A") and "(%rdi)" in body(text, "_Z2fb1B")


def test_q15():
    assert out("vec_noexcept").splitlines() == ["0 copies, 7 moves", "7 copies, 0 moves"]
    assert 1 + 2 + 4 == 7


def test_q16():
    assert out("moved_from").splitlines() == ["0 40", "3", "1 1", "1 5", "new!"]


def test_q17():
    assert out("elision").splitlines() == ["plain: 0 copies, 0 moves", "forced: 0 copies, 1 moves", "either: 1 copies, 0 moves"]
    # the warning the pragma keeps off is real
    text = (CPP / "elision.cpp").read_text().replace('#pragma GCC diagnostic ignored "-Wpessimizing-move"', "")
    path = BUILD / "try_elision.cpp"
    path.write_text(text)
    r = subprocess.run(["g++", "-std=c++20", "-Wall", "-c", "-o", os.devnull, str(path)], capture_output=True, text=True)
    assert "pessimizing-move" in r.stderr


def test_q18():
    assert out("forwarding").split() == "copy copy copy move move".split()
    def forwards(arg):
        path = BUILD / "try_forward.cpp"
        path.write_text("""#include <utility>
void take(void (*)(int)) {}
void plain(int) {}
void over(int) {}
void over(double) {}
template <class T> void good(T&& x) { take(std::forward<T>(x)); }
int main() { good(ARG); }
""".replace("ARG", arg))
        return subprocess.run(["g++", "-std=c++20", "-fsyntax-only", str(path)], capture_output=True).returncode == 0
    assert forwards("plain") and not forwards("over") and not forwards("{1, 2}")


def test_q19():
    assert out("collapse").splitlines() == ["T is a reference", "T is a value", "T is a reference"]
    want = {"std::vector<int> l; g(l);": False, "int&& q = i; (void)q;": False, "int&& q = 1; (void)q;": True}
    assert {line: compiles("collapse", line) for line in want} == want


def test_q20():
    code, _, err = report("sv_temp:a")
    assert code != 0 and "heap-use-after-free" in err


def test_q21():
    assert out("sv_cstr").splitlines() == ["4 12", "4"]


def test_q22():
    assert out("cycle").strip() == "2 2"
    code, stdout, err = report("cycle:a")
    assert code != 0 and "LeakSanitizer" in err and "freed" not in stdout and "64 byte(s) leaked" in err
    fixed = out("cycle_fixed").splitlines()
    assert fixed == ["1 2", "alive 2", "freed", "freed", "1 1"] and out("cycle_fixed:a").splitlines() == fixed


def test_q23():
    assert out("unique_main").strip() == "20000 0" and out("unique_main:a").strip() == "20000 0"
    # the wrong answer's self-move: one delete, and a null pointer left, not a dangling one
    r = snippet("selfmove", """#include <iostream>
#include <utility>
struct D { static inline int gone = 0; ~D() { ++gone; } };
struct U {
    D* p_;
    U& operator=(U&& o) noexcept { delete p_; p_ = o.p_; o.p_ = nullptr; return *this; }
};
int main() {
    U u{new D};
    u = std::move(u);
    std::cout << D::gone << " " << (u.p_ == nullptr) << "\\n";
}
""", "-Wno-self-move")
    assert r.stdout.split() == ["1", "1"]


def test_q24():
    assert out("make_shared_weak").splitlines() == [
        "destroyed", "new: 1 frees while the weak_ptr lives", "new: 2 frees after",
        "destroyed", "make_shared: 0 frees while the weak_ptr lives", "make_shared: 1 frees after"]


def test_q25():
    code, _, err = report("two_owners:a")
    assert code != 0 and "double-free" in err
    assert out("share_this").splitlines() == ["2 2", "bad_weak_ptr"]


def test_q26():
    code, _, err = report("vec_ref:a")
    assert code != 0 and "heap-use-after-free" in err
    text = (CPP / "vec_ref.cpp").read_text().replace("std::vector<int> v{1, 2, 3};", "std::vector<int> v{1, 2, 3};\n    v.reserve(4);")
    build = BUILD / "tmp_vec_ref.cpp"
    build.write_text(text)
    bin_path = BUILD / "tmp_vec_ref"
    subprocess.run(["g++", *FLAGS["a"], str(build), "-o", str(bin_path)], check=True, capture_output=True)
    r = subprocess.run(["setarch", platform.machine(), "-R", str(bin_path)], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "9"


def test_q27():
    assert out("vec_bool").strip() == "0 1 1"
    want = {"bool& b = v[0]; (void)b;": False, "auto& b = v[0]; (void)b;": False, "bool b = v[0]; (void)b;": True}
    assert {line: compiles("vec_bool", line) for line in want} == want
    assert "data race" not in report("vec_bool_race:t")[2]
    assert "data race" in report("vec_bool_race:t", "bool")[2]


def test_q28():
    assert out("stability").splitlines() == ["1 1", "1", "0"]


def test_q29():
    assert out("emplace").split() == ["1", "1", "1000000"]
    assert not compiles("emplace", "rows.push_back(1000000);")
    assert compiles("emplace", "rows.push_back({1000000});")


def test_q30():
    code, _, err = report("sort_le:a")
    assert code != 0 and "AddressSanitizer" in err
    plain_asan = BUILD / "sort_le_asan"  # AddressSanitizer alone, as the stem asks: UBSan's checks change the report
    subprocess.run(["g++", "-std=c++20", "-O1", "-g", "-fsanitize=address", str(CPP / "sort_le.cpp"), "-o", str(plain_asan)], check=True, capture_output=True)
    r = subprocess.run(["setarch", platform.machine(), "-R", str(plain_asan)], capture_output=True, text=True)
    assert r.returncode != 0 and "AddressSanitizer: heap-buffer-overflow" in r.stderr and "READ of size 4" in r.stderr and "__unguarded_partition" in r.stderr
    text = (CPP / "sort_le.cpp").read_text().replace("a <= b", "a < b")
    build = BUILD / "tmp_sort.cpp"
    build.write_text(text)
    subprocess.run(["g++", *FLAGS["a"], str(build), "-o", str(BUILD / "tmp_sort")], check=True, capture_output=True)
    r = subprocess.run(["setarch", platform.machine(), "-R", str(BUILD / "tmp_sort")], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "100"


def test_q31():
    assert out("overflow_check").strip() == "0 1"
    o0 = BUILD / "overflow_o0"
    subprocess.run(["g++", "-std=c++20", "-O0", str(CPP / "overflow_check.cpp"), "-o", str(o0)], check=True)
    assert subprocess.run([str(o0)], capture_output=True, text=True).stdout.strip() == "0 1"  # the rewrite happens at -O0 too
    code, stdout, err = report("overflow_check:a")
    assert "signed integer overflow" in err and stdout.strip() == "1 1" and code == 0
    bin_path = BUILD / "overflow_wrapv"
    subprocess.run(["g++", "-std=c++20", "-O2", "-fwrapv", str(CPP / "overflow_check.cpp"), "-o", str(bin_path)], check=True)
    assert subprocess.run([str(bin_path)], capture_output=True, text=True).stdout.strip() == "1 1"
    path = BUILD / "builtin_add.cpp"
    path.write_text("bool check(int a, int b, int* r) { return __builtin_add_overflow(a, b, r); }\n")
    assert "seto" in body(asm(path), "_Z5checkiiPi")


def test_q32():
    lines = out("shift_abs").split()
    assert lines == ["-2147483648", "2", "-2147483648", "4294967295"]
    _, _, err = report("shift_abs:a")
    assert "shift exponent 33 is too large" in err and "negation of -2147483648" in err
    assert err.count("runtime error") == 2
    trap = snippet("idiv", """#include <climits>
#include <iostream>
int main() { volatile int a = INT_MIN, b = -1; std::cout << a / b << "\\n"; }
""")
    assert trap.returncode == -8


def test_q33():
    code, _, err = report("lifetime:a")
    assert code != 0 and "stack-use-after-scope" in err
    assert re.search(r"lifetime\.cpp:1[0-9]", err) and "#1" in err


def test_q34():
    assert out("default_args").splitlines() == ["Derived 1", "Derived 2", "Base::g(int)", "Derived::g(double)"]


def test_q35():
    assert out("sizes").splitlines() == ["1 8 4 8 4", "8 8 16", "16 32 32 24"]


def test_q36():
    t = CPP / "tmpl"
    obj = BUILD / "link_q36"
    obj.mkdir(exist_ok=True)
    link = subprocess.run(["g++", "-std=c++20", "-I", str(t), str(t / "main.cpp"), str(t / "sum.cpp"), "-o", str(obj / "a")],
                          capture_output=True, text=True)
    assert link.returncode != 0 and "undefined reference" in link.stderr
    extra = obj / "sum_inst.cpp"
    extra.write_text((t / "sum.cpp").read_text() + "\ntemplate int total(const std::vector<int>&);\n")
    ok = subprocess.run(["g++", "-std=c++20", "-I", str(t), str(t / "main.cpp"), str(extra), "-o", str(obj / "b")], capture_output=True, text=True)
    assert ok.returncode == 0 and subprocess.run([str(obj / "b")], capture_output=True, text=True).stdout.strip() == "6"
    (obj / "m2.cpp").write_text((t / "main.cpp").read_text().replace("std::vector<int>{1, 2, 3}", "std::vector<long>{1, 2, 3}"))
    other = subprocess.run(["g++", "-std=c++20", "-I", str(t), str(obj / "m2.cpp"), str(extra), "-o", str(obj / "c")], capture_output=True, text=True)
    assert other.returncode != 0  # an instantiation for int does not serve long


def test_q37():
    assert out("concepts").splitlines() == ["integer real integer", "10"]
    assert not compiles("concepts", 'kind("a");') and not compiles("concepts", "notional(1, 2);")
    path = BUILD / "try_concepts.cpp"
    path.write_text((CPP / "concepts.cpp").read_text().replace("// try each line here", "notional(1, 2);"))
    r = subprocess.run(["g++", "-std=c++20", "-fsyntax-only", str(path)], capture_output=True, text=True)
    assert "constraints not satisfied" in r.stderr or "required" in r.stderr


def test_q38():
    assert out("msg_variant").splitlines() == ["300 2 24", "1", "bad access", "0 1"]
    assert out("variant_valueless").strip() == "1 1"
    source = (CPP / "variant_valueless.cpp").read_text()
    assert snippet("never_valueless", source.replace("std::string s;", "int s;")).stdout.strip() == "0 0"


def test_q39():
    assert out("key_hash").split() == ["50", "4"]
    # a masked table: multiplying moves information only upward, so the low bits see only the venue, and the top bits see both
    mask = 2**64 - 1
    mixed = [(((s << 32) | v) * 0x9E3779B97F4A7C15) & mask for s in range(100) for v in range(50)]
    assert len({h & 0xFFF for h in mixed}) == 50 and len({h >> 52 for h in mixed}) > 3000
    assert not compiles_no_hash()


def compiles_no_hash():
    path = BUILD / "try_nohash.cpp"
    path.write_text("#include <unordered_map>\nstruct K { int a; bool operator==(const K&) const = default; };\n"
                    "int main() { std::unordered_map<K, int> m; m[K{1}] = 1; }\n")
    return subprocess.run(["g++", "-std=c++20", "-fsyntax-only", str(path)], capture_output=True).returncode == 0


DOTNET = shutil.which("dotnet") or str(pathlib.Path.home() / ".dotnet" / "dotnet")
HAS_DOTNET = pathlib.Path(DOTNET).exists()


@pytest.mark.skipif(not HAS_DOTNET, reason="needs the .NET SDK")
def test_q40():
    where = BUILD / "cs_boxing"
    shutil.rmtree(where, ignore_errors=True)
    shutil.copytree(CPP.parent / "csharp" / "Boxing", where)
    env = {**os.environ, "DOTNET_NOLOGO": "1", "DOTNET_CLI_TELEMETRY_OPTOUT": "1"}
    b = subprocess.run([DOTNET, "build", "-c", "Release", "-o", "out"], cwd=where, capture_output=True, text=True, env=env, timeout=200)
    assert b.returncode == 0, b.stdout
    r = subprocess.run([DOTNET, str(where / "out" / "Boxing.dll")], capture_output=True, text=True, timeout=60, env=env)
    assert r.stdout.splitlines() == ["2 1", "2 3", "2", "False True"]
    assert out("value_cpp").strip() == "3 1 9"




def variant(tag, main, header, edits, mode="s"):
    """Run a copy of a program whose header has been edited: a broken model must fail where the real one passes."""
    where = BUILD / tag
    where.mkdir(exist_ok=True)
    text = (CPP / header).read_text()
    for old, new in edits:
        assert old in text
        text = text.replace(old, new)
    (where / header).write_text(text)
    shutil.copy(CPP / f"{main}.cpp", where)
    subprocess.run(["g++", *FLAGS[mode], "-pthread", f"{main}.cpp", "-o", "run"], cwd=where, check=True,
                   capture_output=True, timeout=300)
    return subprocess.run(["setarch", platform.machine(), "-R", str(where / "run")], capture_output=True, text=True, timeout=120)


def snippet(tag, text, *flags):
    """Compile and run a small program; returns the completed process."""
    path = BUILD / f"snip_{tag}.cpp"
    path.write_text(text)
    bin_path = BUILD / f"snip_{tag}"
    subprocess.run(["g++", "-std=c++20", "-O2", *flags, str(path), "-o", str(bin_path)], check=True, capture_output=True, timeout=200)
    return subprocess.run([str(bin_path)], capture_output=True, text=True, timeout=60)


def asm(path, *flags):
    r = subprocess.run(["g++", "-std=c++20", "-O2", *flags, "-S", str(path), "-o", "-"], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return r.stdout


def body(assembly, name):
    start = assembly.index(f"{name}:")
    return assembly[start:assembly.index(".cfi_endproc", start)]


def test_q41():
    lines = out("growth").splitlines()
    assert lines[0].split() == [str(2 ** k) for k in range(11)] and lines[1] == "1023"
    code, _, err = report("naive_vec:a")
    assert code != 0 and "heap-use-after-free" in err

    def moves(grow, n=1000):
        cap = size = total = 0
        for _ in range(n):
            if size == cap:
                total += size
                cap = grow(cap)
            size += 1
        return total

    assert moves(lambda c: c * 2 or 1) == 1023 == sum(2**k for k in range(10)) and moves(lambda c: c + 16) == 31248
    assert moves(lambda c: c + 16, 2000) > 3.9 * moves(lambda c: c + 16, 1000)  # quadratic in n
    # with factor 2 the freed blocks never hold the next one; with 1.5 the sixth block fits in the first four
    sizes = [1.5 ** k for k in range(6)]
    assert sum(sizes[:4]) == pytest.approx(8.125) and sizes[5] == pytest.approx(7.59375) and sizes[5] <= sum(sizes[:4])
    assert all(sum(sizes[:k - 1]) < sizes[k] for k in range(1, 5))
    assert all(sum(2 ** i for i in range(k - 1)) < 2 ** k for k in range(1, 60))
    # the total moves for factor f tend to n / (f - 1): twice as many at 1.5 as at 2
    n = 1 << 20

    def total(f):
        cap, t = 1.0, 0.0
        while cap < n:
            t += cap
            cap *= f
        return t / cap

    assert total(2) == pytest.approx(1.0, rel=0.01) and total(1.5) == pytest.approx(2.0, rel=0.01)


def test_q42():
    assert out("opt_main").strip() == "0 0" and out("opt_main:a").strip() == "0 0"
    code, stdout, err = report("misaligned:a")
    assert "store to misaligned address" in err and "load of misaligned address" in err and stdout.strip() == "1.5" and code == 0
    # the flag set before the constructor runs: a throwing constructor leaves a dead object to destroy
    bad = variant("opt_bad", "opt_main", "opt.hpp", [
        ("T* p = ::new (static_cast<void*>(buf_)) T(std::forward<A>(a)...);\n        has_ = true;",
         "has_ = true;\n        T* p = ::new (static_cast<void*>(buf_)) T(std::forward<A>(a)...);")])
    assert bad.returncode != 0 or bad.stdout.strip() != "0 0"


def test_q43():
    assert out("pool_main").splitlines() == ["0 1", "0 0"] and out("pool_main:a").splitlines() == ["0 1", "0 0"]
    assert "g() % 8 == 0" in (CPP / "pool_main.cpp").read_text()  # one creation attempt in about 8 throws
    bad = variant("pool_bad", "pool_main", "pool.hpp", [
        ("free_ = s->next;                         // read now: the object overwrites it\n", ""),
        ("return ::new (static_cast<void*>(s->bytes)) T(std::forward<A>(a)...);",
         "T* p = ::new (static_cast<void*>(s->bytes)) T(std::forward<A>(a)...);\n            free_ = s->next;\n            return p;"),
        ("s->next = free_;                     // a failed constructor loses no slot\n            free_ = s;\n", "")])
    assert "exhaustion" in bad.stdout and bad.returncode == 1


def test_q44():
    assert out("arena_main").splitlines() == ["0 4950 2475.0 0", "1"] and out("arena_main:a").splitlines() == ["0 4950 2475.0 0", "1"]


def test_q45():
    assert out("pmr_use").splitlines() == ["1020 400", "1 0", "bad_alloc"]
    assert sum(2 ** k for k in range(8)) * 4 == 1020
    r = snippet("pmr_copy", """#include <iostream>
#include <memory_resource>
#include <vector>
int main() {
    char buf[1024];
    std::pmr::monotonic_buffer_resource mono(buf, sizeof buf);
    std::pmr::vector<int> a(&mono);
    a.push_back(1);
    std::pmr::vector<int> b = a;
    std::cout << (a.get_allocator().resource() == &mono) << (b.get_allocator().resource() == &mono)
              << (b.get_allocator().resource() == std::pmr::get_default_resource()) << "\\n";
}
""")
    assert r.stdout.strip() == "101"


def test_q46():
    code, stdout, err = report("assign_bad:a")
    assert code == 0 and stdout.strip() == "0" and "Sanitizer" not in err
    code, stdout, err = report("assign_bad:a", "fail")
    assert code != 0 and "attempting double-free" in err
    assert out("assign_good:a").splitlines() == ["7", "caught 7", "8"]


def test_q47():
    assert out("aliasing").splitlines() == ["1", "3f800000"]
    bin_path = BUILD / "alias_off"
    subprocess.run(["g++", "-std=c++20", "-O2", "-fno-strict-aliasing", str(CPP / "aliasing.cpp"), "-o", str(bin_path)], check=True)
    assert subprocess.run([str(bin_path)], capture_output=True, text=True).stdout.splitlines()[0] == "0"
    path = BUILD / "memcpy_read.cpp"
    path.write_text("#include <cstdint>\n#include <cstring>\n"
                    "std::uint32_t read_u32(const char* p) { std::uint32_t v; std::memcpy(&v, p, 4); return v; }\n")
    code = body(asm(path), "_Z8read_u32PKc")
    assert "\tcall" not in code and "movl\t(%rdi), %eax" in code


def test_q48():
    plain = asm(CPP / "nullcheck.cpp")
    assert "test" not in body(plain, "_Z8read_badPi") and "test" in body(plain, "_Z9read_goodPi")
    assert "test" in body(asm(CPP / "nullcheck.cpp", "-fno-delete-null-pointer-checks"), "_Z8read_badPi")


def test_q49():
    code, _, err = report("max_dangle:a")
    assert code != 0 and "stack-use-after-scope" in err and "max_dangle.cpp:6" in err
    assert out("max_dangle:a", "x", "y", "z").strip() == "4"
    r = subprocess.run(["g++", "-std=c++20", "-Wall", "-Wextra", "-Werror", "-c", "-o", os.devnull, str(CPP / "max_dangle.cpp")], capture_output=True)
    assert r.returncode == 0
    path = BUILD / "max_mixed.cpp"
    path.write_text("#include <algorithm>\nauto x = std::max(1, 2.0);\n")
    assert subprocess.run(["g++", "-std=c++20", "-fsyntax-only", str(path)], capture_output=True).returncode != 0


def test_q50():
    assert "data race" in report("shared_race:t", "A")[2]
    code, stdout, err = report("shared_race:t", "B")
    assert code == 0 and stdout.strip() == "1" and "data race" not in err
    code, stdout, err = report("shared_copies:t")
    assert code == 0 and stdout.strip() == "1 5" and "data race" not in err
    path = BUILD / "atomic_sp.cpp"
    path.write_text("#include <atomic>\n#include <memory>\nstd::atomic<std::shared_ptr<int>> a;\n")
    assert subprocess.run(["g++", "-std=c++20", "-fsyntax-only", str(path)], capture_output=True).returncode != 0
    assert "_Sp_locker" in pathlib.Path("/usr/include/c++/11/bits/shared_ptr_atomic.h").read_text()


def test_q51():
    assert out("bq_main").splitlines() == ["9000 27009000 0 0", "0 1 0"]
    assert out("bq_main:t").splitlines() == ["9000 27009000 0 0", "0 1 0"]
    assert sum(range(1, 3001)) * (1 + 2 + 3) == 27009000


def test_q52():
    cases = [(n, k) for n in range(76) for k in range(n + 2)]
    r = run("choose", stdin="\n".join(f"{n} {k}" for n, k in cases))
    answers = r.stdout.split()
    assert len(answers) == len(cases)
    overflows = []
    for (n, k), a in zip(cases, answers, strict=True):
        exact = math.comb(n, k)
        if exact >= 2 ** 64:
            assert a == "overflow"
            overflows.append((n, k))
        else:
            assert a == str(exact)
    assert min(overflows) == (68, 31) and math.comb(68, 31) > 2 ** 64 > math.comb(67, 33)
    top = 2 ** 64 - 1
    assert run("choose", stdin=f"{top} 1\n{top} 0\n{top} {top}\n{top} 2\n0 1\n").stdout.split() == [str(top), "1", "1", "overflow", "0"]
    assert math.factorial(20) < 2 ** 64 < math.factorial(21)


def test_q53():
    for arg, text in (("noexcept", "from noexcept"), ("destructor", "from destructor")):
        r = run("terminate", arg)
        assert r.returncode == -6 and "terminate called" in r.stderr and text in r.stderr and "caught" not in r.stdout
    assert out("terminate", "plain").strip() == "caught plain"
    source = (CPP / "terminate.cpp").read_text()
    allowed = snippet("noexcept_false", source.replace("~Closer() {", "~Closer() noexcept(false) {").replace("int main(int, char** argv) {", "int main() {\n    const char* argv[] = {\"p\", \"destructor\"};"))
    assert allowed.stdout.strip() == "caught from destructor"
    during = snippet("two", """#include <iostream>
#include <stdexcept>
struct Closer { ~Closer() noexcept(false) { throw std::runtime_error("second"); } };
int main() {
    try { Closer c; throw std::runtime_error("first"); }
    catch (const std::exception& e) { std::cout << e.what() << "\\n"; }
}
""")
    assert during.returncode == -6 and during.stdout == ""


def test_q54():
    assert out("crtp").strip() == "62"
    assert (10 + 1) * 2 + (10 + 1) * 2 + (10 - 1) * 2 == 62
    code = asm(CPP / "crtp.cpp")
    assert "\tcall" not in body(code, "_Z11static_callR4Momol") and "call\t*" in body(code, "_Z12virtual_callR6IStratl")
    source = (CPP / "crtp.cpp").read_text()
    path = BUILD / "crtp_missing.cpp"
    path.write_text(source.replace("long signal(long px) { return px + 1; }\n};\n\nstruct IStrat", "};\n\nstruct IStrat"))
    r = subprocess.run(["g++", "-std=c++20", "-fsyntax-only", str(path)], capture_output=True, text=True)
    assert r.returncode != 0 and "signal" in r.stderr
    assert "virtual" not in source.split("struct IStrat")[0]


def test_q55():
    assert out("constexpr_table").strip() == "42 2 42 1000"
    want = {"int e = always(argc); (void)e;": False, "constexpr int f = twice(argc); (void)f;": False,
            "constexpr int o = twice(2000000000); (void)o;": False, "int d = twice(argc); (void)d;": True,
            "int e = always(4); (void)e;": True}
    assert {line: compiles("constexpr_table", line) for line in want} == want
    path = BUILD / "table_no_guard.cpp"
    path.write_text((CPP / "constexpr_table.cpp").read_text().replace("if (i + 1 < t.size()) x *= 10;", "x *= 10;"))
    r = subprocess.run(["g++", "-std=c++20", "-fsyntax-only", str(path)], capture_output=True, text=True)
    assert r.returncode != 0 and "overflow" in r.stderr


def test_q56():
    assert out("vec_main").strip() == "0 41 40 39" and out("vec_main:a").strip() == "0 41 40 39"
    bad = variant("vec_bad", "vec_main", "vec.hpp", [("std::is_nothrow_move_constructible_v<T>\n                      || !std::is_copy_constructible_v<T>", "true")])
    assert bad.returncode != 0 or bad.stdout.strip() != "0 41 40 39"


def test_q57():
    assert out("rc_main:a").strip() == "0"
    code, stdout, err = report("rc_main:t")
    assert code == 0 and stdout.strip() == "0" and "data race" not in err
    for _ in range(5):
        relaxed = variant("rc_relaxed", "rc_main", "rc.hpp", [("std::memory_order_acq_rel", "std::memory_order_relaxed")], "t")
        if "data race" in relaxed.stderr:
            break
    assert "data race" in relaxed.stderr


def test_q58():
    want = ["0 1 20 18", "0 9", "7", "0"]
    assert out("fn_main").splitlines() == want and out("fn_main:a").splitlines() == want
    assert 1 + 2 + 3 + 4 + 10 == 20 and 8 + 10 == 18
    # a vector moves a type it cannot copy even when that move may throw, and a throw then leaves elements moved out
    path = BUILD / "vec_throwing_move.cpp"
    path.write_text("""#include "fn.hpp"
#include <cstdio>
#include <type_traits>
#include <vector>
struct T {
    int v;
    static inline int left = -1;
    explicit T(int x) : v(x) {}
    T(const T&) = delete;
    T(T&& o) : v(o.v) { if (left == 0) throw 1; if (left > 0) --left; o.v = -1; }
};
static_assert(std::is_nothrow_move_constructible_v<Fn<int()>> && !std::is_copy_constructible_v<Fn<int()>>);
int main() {
    std::vector<T> a;
    a.reserve(4);
    for (int i = 0; i < 4; ++i) a.emplace_back(i);
    T::left = 2;
    try { a.emplace_back(9); } catch (int) {}
    int moved_out = 0;
    for (auto& t : a) moved_out += t.v == -1;
    std::printf("%zu %d\\n", a.size(), moved_out);
}
""")
    binary = BUILD / "vec_throwing_move"
    subprocess.run(["g++", *FLAGS["s"], "-I", str(CPP), str(path), "-o", str(binary)], check=True, capture_output=True, timeout=120)
    assert subprocess.run([str(binary)], capture_output=True, text=True, timeout=20).stdout.split() == ["4", "2"]


def test_q59():
    assert out("var_main").strip() == "0 0 1" and out("var_main:a").strip() == "0 0 1"
    bad = variant("var_bad", "var_main", "var.hpp", [("        destroy();                               // if the constructor throws: valueless\n", "")])
    assert bad.returncode != 0 or bad.stdout.strip() != "0 0 1"
    # a type not in the list: the compile-fail test on the printed header, and what the header does without the assert
    misuse = """#include "var.hpp"
#include <string>
int main() {
    Var<int, char> v;
    v.emplace<std::string>(40, 'x');
    return int(v.index());
}
"""
    path = BUILD / "try_var.cpp"
    path.write_text(misuse)
    r = subprocess.run(["g++", "-std=c++20", "-fsyntax-only", "-I", str(CPP), str(path)], capture_output=True, text=True)
    assert r.returncode != 0 and "T is not in the list" in r.stderr
    path.write_text(misuse.replace("v.emplace<std::string>(40, 'x');", "if (v.get_if<std::string>()) return 1;"))
    r = subprocess.run(["g++", "-std=c++20", "-fsyntax-only", "-I", str(CPP), str(path)], capture_output=True, text=True)
    assert r.returncode != 0 and "T is not in the list" in r.stderr
    where = BUILD / "var_noassert"
    where.mkdir(exist_ok=True)
    header = (CPP / "var.hpp").read_text()
    line = '        static_assert((std::is_same_v<T, Ts> || ...), "T is not in the list");\n'
    assert line in header
    (where / "var.hpp").write_text(header.replace(line, ""))
    (where / "m.cpp").write_text(misuse)
    subprocess.run(["g++", "-std=c++20", "-O1", "-g", "-fsanitize=address", "-w", "m.cpp", "-o", "run"], cwd=where, check=True, capture_output=True, timeout=120)
    r = subprocess.run(["setarch", platform.machine(), "-R", str(where / "run")], capture_output=True, text=True, timeout=60)
    assert r.returncode != 0 and "stack-buffer-overflow" in r.stderr


def test_q60():
    assert out("expr_main").strip() == "0 2"
    code, _, err = report("expr_dangle:a")
    assert code != 0 and "stack-use-after-scope" in err
    fixed = variant("expr_fix", "expr_dangle", "expr.hpp", [
        ("#include <vector>\n", "#include <type_traits>\n#include <vector>\n\nclass Vector;\n"),
        ("const L& l;                                 // references: cheap, and the trap\n    const R& r;",
         "std::conditional_t<std::is_same_v<L, Vector>, const L&, L> l;\n    std::conditional_t<std::is_same_v<R, Vector>, const R&, R> r;")], "a")
    assert fixed.returncode == 0 and fixed.stdout.strip() == "6"
