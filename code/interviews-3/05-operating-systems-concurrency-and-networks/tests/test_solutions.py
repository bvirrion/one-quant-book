"""Operating systems, concurrency and networks: every printed program runs on this Linux, on loopback where it uses a network.

C++ builds with g++ 11.4, -std=c++20 -O2 -Wall -Wextra -Werror; sanitizers run under setarch -R, which this kernel needs. Models
of things a laptop cannot show (a scheduler, Nagle's algorithm, a lossy link) meet an independent check or a broken twin. A sleep
in a driver only gives another thread time to block; no test asserts a timing. Multicast needs a kernel that accepts a group on
lo, and skips with that reason if it does not.
"""
import concurrent.futures
import ctypes
import itertools
import os
import pathlib
import platform
import random
import re
import resource
import select
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from unittest import mock

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
CPP = HERE / "cpp"
PY = HERE / "python"
BUILD = HERE.parents[2] / "build" / "iv35"
BUILD.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PY))

import iv_arb  # noqa: E402
import iv_atomic_save  # noqa: E402
import iv_event_loop  # noqa: E402
import iv_framing  # noqa: E402
import iv_inversion  # noqa: E402
import iv_mcast_mac  # noqa: E402
import iv_nagle  # noqa: E402
import iv_page_walk  # noqa: E402
import iv_reliable  # noqa: E402
import iv_round_robin  # noqa: E402
import iv_waitfor  # noqa: E402
import iv_window  # noqa: E402

FLAGS = {
    "s": ["-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror"],
    "t": ["-std=c++20", "-O1", "-g", "-fsanitize=thread"],
}
PREBUILD = ("tls semaphore cow cow_huge malloc_mmap stack_depth sigpipe fork_lock robust futex_main rw_main shm_main "
            "shm_threads:t rw_main:t futex_main:t").split()
NONNUMERIC = {33: "A description of the kernel's receive path; its stages rest on the kernel documentation in the ledger"}


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


def run(spec, *args, **kw):
    return subprocess.run(["setarch", platform.machine(), "-R", str(exe(spec)), *args], capture_output=True, text=True,
                          timeout=kw.pop("timeout", 120), **kw)


def out(spec, *args):
    r = run(spec, *args)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def py(script, *args):
    r = subprocess.run([sys.executable, str(PY / f"{script}.py"), *args], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout.splitlines()


def variant(tag, main, header, edits, mode="s", timeout=120):
    """A copy of a program with an edited header: a broken model must fail where the real one passes."""
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
    return subprocess.run(["setarch", platform.machine(), "-R", str(where / "run")], capture_output=True, text=True, timeout=timeout)


def test_q1():
    assert py("fork_vs_thread") == ["after fork 0", "after thread 1"]


def test_q2():
    assert out("tls").strip() == "4000 1000 0"
    assembly = subprocess.run(["g++", "-std=c++20", "-O2", "-S", "-o", "-", str(CPP / "tls.cpp")], capture_output=True,
                              text=True, timeout=120).stdout
    assert "%fs:" in assembly                  # mine is reached through the thread's own segment register


def test_q3():
    assert py("zombie") == ["state Z", "code 7", "gone True"]


def test_q4():
    assert py("boundaries") == ["b'abc' b'de'", "b'abcde'"]


def test_q5():
    assert py("endian") == ["little", "04030201 01020304", "0x4030201"]

    def swapped(v):
        return int.from_bytes(v.to_bytes(4, "little"), "big")

    # the wrong order: exactly 2**24 for a value of one byte, and no more than that for any value
    assert swapped(100) == 100 * 2**24 and swapped(123456) == 1088553216 and swapped(123456) // 123456 == 8817
    assert all(swapped(v) == v << 24 for v in range(1, 256))
    rng = random.Random(5)
    samples = [*range(1, 70_000), *(rng.getrandbits(32) | 1 for _ in range(20_000))]
    assert max(swapped(v) / v for v in samples) == 2**24
    assert swapped(0x01020304) == 0x04030201 and swapped(swapped(123456)) == 123456   # a large value turns small as well


def test_q6():
    assert py("five_tuple") == ["True", "False", "b'a' b'b'"]
    low, high = (int(x) for x in pathlib.Path("/proc/sys/net/ipv4/ip_local_port_range").read_text().split())
    assert 10000 < high - low < 65536


def test_q7():
    assert out("semaphore").splitlines() == ["1110", "10"]


def test_q8():
    assert py("signals") == ["caught [15]", "refused", "-9"]


def test_q9():
    lines = out("cow").splitlines()
    m = re.fullmatch(r"child 2 at (\S+): sum 2000, read faults (\d+), write faults (\d+)", lines[0])
    assert m and lines[1] == f"parent 1 at {m.group(1)}"
    assert int(m.group(2)) < 50 and 2000 <= int(m.group(3)) < 2100


def test_q9_huge_pages():
    lines = out("cow_huge").splitlines()
    first, huge = int(lines[0].split()[-1]), int(lines[1].split()[-1])
    if huge == 0:
        pytest.skip("this kernel gave the range no huge pages")
    m = re.fullmatch(r"child sum 2000 read (\d+) write (\d+)", lines[2])
    assert first < 2000                         # huge pages cut the parent's first touch
    assert m and int(m.group(1)) < 50 and 2000 <= int(m.group(2)) < 2100    # and not the child's count


def test_q10():
    levels, offset = iv_page_walk.indices(0x7f1234567abc)
    assert levels == [254, 72, 418, 359] and offset == 0xabc
    rng = random.Random(1)
    for _ in range(1000):
        addr = rng.getrandbits(47)
        (a, b, c, d), off = iv_page_walk.indices(addr)
        assert (a << 39 | b << 30 | c << 21 | d << 12 | off) == addr and max(a, b, c, d) < 512
    assert iv_page_walk.table_bytes(1 << 30) == 515 * 4096 == 2109440
    assert iv_page_walk.table_bytes(1 << 30, page=1 << 21, levels=3) == 3 * 4096

    def slow(size, page, levels):
        """An independent count: walk every page and collect the distinct table prefixes it passes through."""
        shifts = (39, 30, 21, 12)[:levels]
        seen = set()
        for addr in range(0, size, page):
            for k in range(levels):
                seen.add((k, tuple((addr >> s) & 0x1FF for s in shifts[:k])))
        return len(seen) * 4096

    for size in (4096, 8192, 1 << 21, (1 << 21) + 4096, 3 << 21, 1 << 30, (1 << 30) + (1 << 21)):
        assert iv_page_walk.table_bytes(size) == slow(size, 4096, 4)
    assert iv_page_walk.table_bytes(4096) == 4 * 4096     # at the extreme, one page still needs a table per level
    assert iv_page_walk.table_bytes(1 << 30, page=1 << 21, levels=3) == slow(1 << 30, 1 << 21, 3)


def test_q11():
    assert out("malloc_mmap").splitlines() == ["heap mmap", "unmapped", "heap"]


def test_q12():
    first, second = [[int(x) for x in line.split()] for line in py("rss_vsz")]
    assert 1020 <= first[0] <= 1030 and abs(first[1]) <= 3
    assert abs(second[0]) <= 3 and 98 <= second[1] <= 106


def limited(stack_kib):
    def apply():
        resource.setrlimit(resource.RLIMIT_STACK, (stack_kib * 1024, resource.getrlimit(resource.RLIMIT_STACK)[1]))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    return apply


def test_q13():
    hard = resource.getrlimit(resource.RLIMIT_STACK)[1]
    if hard != resource.RLIM_INFINITY and hard < 262144 * 1024:
        pytest.skip("the hard stack limit here is below 256 MiB")
    ok = run("stack_depth", "1000", preexec_fn=limited(8192))
    assert ok.returncode == 0 and ok.stdout.strip() == "1000"
    assert run("stack_depth", "100000", preexec_fn=limited(8192)).returncode == -11
    big = run("stack_depth", "100000", preexec_fn=limited(262144))
    assert big.returncode == 0 and big.stdout.strip() == "100000"
    src = BUILD / "thread_stack.cpp"
    src.write_text("""#include <cstdio>
#include <pthread.h>
#include <thread>
int main() {
    std::thread([] {
        pthread_attr_t a; size_t n; pthread_getattr_np(pthread_self(), &a); pthread_attr_getstacksize(&a, &n);
        std::printf("%zu\\n", n);
    }).join();
}
""")
    bin_path = BUILD / "thread_stack"
    subprocess.run(["g++", "-std=c++20", "-pthread", str(src), "-o", str(bin_path)], check=True)
    r = subprocess.run([str(bin_path)], capture_output=True, text=True, preexec_fn=limited(8192))
    assert r.stdout.strip() == str(8192 * 1024)


def test_q14():
    assert 1000 <= int(py("ping_pong")[0]) <= 3000


def test_q15():
    rr = iv_round_robin.round_robin
    assert rr([8, 4, 1], 2) == [13, 9, 5]
    assert rr([8, 4, 1], 100) == [8, 12, 13]

    def by_ticks(bursts, q):
        """An independent model: one tick at a time, the queue rotated every q ticks."""
        left, done, queue, now = list(bursts), [0] * len(bursts), list(range(len(bursts))), 0
        while queue:
            i = queue.pop(0)
            for _ in range(q):
                now += 1
                left[i] -= 1
                if not left[i]:
                    done[i] = now
                    break
            if left[i]:
                queue.append(i)
        return done

    rng = random.Random(2)
    for _ in range(300):
        b = [rng.randint(1, 12) for _ in range(rng.randint(1, 6))]
        q = rng.randint(1, 15)
        assert rr(b, q) == by_ticks(b, q)
        assert max(rr(b, q)) == sum(b)
    assert (1 + 5 + 13) / 3 < (13 + 9 + 5) / 3 < (8 + 12 + 13) / 3

    def average(order):
        now = total = 0
        for b in order:
            now += b
            total += now
        return total / len(order)

    for _ in range(200):                       # no order beats shortest-first, by trying them all
        b = [rng.randint(1, 20) for _ in range(rng.randint(1, 6))]
        assert average(sorted(b)) == min(average(p) for p in itertools.permutations(b))


def test_q16():
    f = iv_waitfor.find_cycle
    assert sorted(f({"L1": "T1", "L2": "T2"}, {"T1": "L2", "T2": "L1"})) == ["T1", "T2"]
    assert f({"L1": "T1"}, {"T2": "L1"}) is None
    rng = random.Random(3)

    def reaches(graph, a, b):
        seen, stack = set(), [a]
        while stack:
            for n in graph.get(stack.pop(), []):
                if n == b:
                    return True
                if n not in seen:
                    seen.add(n)
                    stack.append(n)
        return False

    found = 0
    for _ in range(2000):
        threads = [f"T{i}" for i in range(rng.randint(1, 7))]
        locks = [f"L{i}" for i in range(rng.randint(1, 7))]
        holder = {lk: rng.choice(threads) for lk in locks if rng.random() < 0.8}
        waits = {t: rng.choice(locks) for t in threads if rng.random() < 0.7}
        graph = {t: [holder[lk]] for t, lk in waits.items() if lk in holder}
        expected = any(reaches(graph, t, t) for t in threads)
        cycle = f(holder, waits)
        assert (cycle is not None) == expected
        if cycle:
            found += 1
            assert all(holder[waits[a]] == b for a, b in zip(cycle, cycle[1:] + cycle[:1], strict=True))
    assert found > 100


def test_q17():
    assert py("mmap_file") == ["b'Saaa' b'Saaa' b'SPaa'", "b'SaTa' b'SaTa' b'SPaa'"]


def test_q18(tmp_path):
    path = tmp_path / "state.bin"
    path.write_bytes(b"old")
    calls = []
    real_fsync, real_replace = os.fsync, os.replace
    with mock.patch("os.fsync", lambda fd: (calls.append("fsync"), real_fsync(fd))[1]), \
            mock.patch("os.replace", lambda a, b: (calls.append("replace"), real_replace(a, b))[1]):
        iv_atomic_save.atomic_save(str(path), b"new")
    assert calls == ["fsync", "replace", "fsync"] and path.read_bytes() == b"new"
    # a crash before the rename leaves the old contents whole
    with mock.patch("os.replace", side_effect=KeyboardInterrupt), pytest.raises(KeyboardInterrupt):
        iv_atomic_save.atomic_save(str(path), b"newer")
    assert path.read_bytes() == b"new"


def test_q19():
    res, backwards = py("clocks")
    assert float(res) <= 1e-6 and backwards == "0"
    assert "[vdso]" in pathlib.Path("/proc/self/maps").read_text()


def test_q20():
    assert py("accept_later") == ["connected and sent", "b'early'"]


def test_q21():
    assert py("time_wait") == ["(True, 'EADDRINUSE')", "(True, 'EADDRINUSE')", "(True, 'bound')"]


def test_q22():
    w = iv_window
    assert w.bandwidth_delay_bytes(10e9, 1e-3) == 1.25e6
    assert w.steady_rate_bps(65535, 1e-3, 10e9) == pytest.approx(524.28e6)
    assert w.steady_rate_bps(1.25e6, 1e-3, 10e9) == pytest.approx(10e9)
    rng = random.Random(4)
    for _ in range(200):
        win, rtt, link = rng.randint(1000, 10**7), rng.uniform(1e-4, 0.2), rng.uniform(1e6, 1e11)
        total = w.simulate_bytes(win, rtt, link, 100.0)
        secs = int(100.0 / rtt) * rtt
        assert total * 8 / secs == pytest.approx(w.steady_rate_bps(win, rtt, link))


def test_q23():
    bodies = [bytes([i % 251]) * (i * 7 % 400) for i in range(300)]
    stream = b"".join(iv_framing.frame(b) for b in bodies)
    rng = random.Random(5)
    for _ in range(30):
        d, got, at = iv_framing.Deframer(), [], 0
        while at < len(stream):
            n = rng.randint(1, 50)
            got += d.feed(stream[at:at + n])
            at += n
        assert got == bodies and not d.buf
    with pytest.raises(ValueError):
        iv_framing.Deframer().feed(b"\xff\xff")
    # with no limit, a 2-byte length can hold the reader back by 65,535 bytes at most, and then delivers garbage
    with mock.patch.object(iv_framing, "MAX_BODY", 65535):
        d = iv_framing.Deframer()
        assert d.feed(b"\xff\xff" + iv_framing.frame(b"ok") + bytes(65535 - 5)) == []
        assert len(d.buf) == 65536
        assert d.feed(b"\0") == [iv_framing.frame(b"ok") + bytes(65535 - 4)] and not d.buf
    # a delete at the front only moves a bytearray's logical start: the first byte's address moves, and nothing is copied
    buf = bytearray(1_000_000)
    start = ctypes.addressof((ctypes.c_char * 1).from_buffer(buf))
    del buf[:10]
    assert ctypes.addressof((ctypes.c_char * 1).from_buffer(buf)) == start + 10
    d = iv_framing.Deframer()
    assert d.feed(iv_framing.frame(b"")) == [b""]              # an empty body is a message
    server = socket.create_server(("127.0.0.1", 0))
    client = socket.create_connection(server.getsockname())
    conn, _ = server.accept()
    threading.Thread(target=lambda: (client.sendall(stream), client.close())).start()
    d, got = iv_framing.Deframer(), []
    while chunk := conn.recv(97):
        got += d.feed(chunk)
    assert got == bodies


def test_q24():
    assert py("udp_trunc") == ["b'abcd' b'ij'", "65507", "Message too long"]
    assert 65535 - 20 - 8 == 65507


def test_q25():
    assert py("udp_drop") == ["8192", "sent 1000, no error", "True", "[True]"]


def test_q26():
    mac = iv_mcast_mac.group_mac
    assert mac("239.1.2.3") == "01:00:5e:01:02:03" == mac("224.1.2.3") == mac("239.129.2.3")
    assert mac("239.1.2.3") != mac("239.1.2.4")
    # every one of the 32 groups sharing the low 23 bits maps to one address, and no 33rd does
    base = 0xE0010203
    same = {base | (top << 23) for top in range(32)}
    assert len(same) == 32 and len({mac(str(socket.inet_ntoa(g.to_bytes(4, "big")))) for g in same}) == 1
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    assert s.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL) == 1
    assert s.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP) == 1
    joined = subprocess.run([sys.executable, str(PY / "mcast_join.py"), "join"], capture_output=True, text=True, timeout=20)
    if joined.stdout.strip() != "b'tick'":
        pytest.skip("this kernel does not deliver a multicast group on lo")
    assert py("mcast_join", "none") == ["nothing"]


def test_q27():
    assert py("nonblock") == ["('EINPROGRESS', 0)", "('EINPROGRESS', 'ECONNREFUSED')"]


def test_q28():
    assert run("sigpipe").returncode == -13
    assert out("sigpipe", "x").strip() == "-1 Broken pipe"
    assert py("first_write") == ["3", "BrokenPipeError"]
    server = socket.create_server(("127.0.0.1", 0))
    client = socket.create_connection(server.getsockname())
    conn, _ = server.accept()
    conn.close()
    waiter = select.poll()
    waiter.register(client, 0)
    client.setblocking(False)
    deadline = time.monotonic() + 5
    readable = []
    while not readable and time.monotonic() < deadline:
        readable = select.select([client], [], [], 0.05)[0]  # the FIN alone makes it readable, before any send
    assert readable and client.recv(10) == b""
    assert waiter.poll(100) == []              # the poll in the listing does not stop for a FIN
    assert client.send(b"one") == 3
    assert waiter.poll(5000)[0][1] & (select.POLLHUP | select.POLLERR)   # it stops for the reset
    with pytest.raises(BrokenPipeError):
        client.send(b"two")
    assert signal.getsignal(signal.SIGPIPE) == signal.SIG_IGN      # Python itself ignores it, so the exception shows


def test_q29():
    sim = iv_inversion.simulate
    low, high = (1, 0, [("lock", 4)]), (3, 1, [("lock", 1), ("cpu", 1)])
    assert sim([low, high, (2, 2, [("cpu", 20)])])[1] == 26
    assert sim([low, high, (2, 2, [("cpu", 20)])], True)[1] == 6
    assert sim([low, high]) == sim([low, high], True) == [4, 6]
    # the delay grows with the middle task without inheritance, and does not with it
    for m in (1, 5, 50, 500):
        assert sim([low, high, (2, 2, [("cpu", m)])], True)[1] == 6
        assert sim([low, high, (2, 2, [("cpu", m)])])[1] == 6 + m
    rng = random.Random(6)
    for _ in range(200):
        hold, m, gap = rng.randint(1, 9), rng.randint(0, 40) + 1, rng.randint(1, 3)
        tasks = [(1, 0, [("lock", hold + gap)]), (3, gap, [("lock", 1)]), (2, gap, [("cpu", m)])]
        assert sim(tasks, True)[1] - gap <= hold + 1     # bounded by what is left of the critical section
        assert sim(tasks)[1] - gap == hold + 1 + m
        # total work never changes: the last completion is the sum of everything
        assert max(sim(tasks)) == max(sim(tasks, True)) == hold + gap + 1 + m


def test_q30():
    assert out("rw_main").splitlines() == ["0 10000", "0", "1 10001"]
    r = run("rw_main:t")
    assert r.returncode == 0 and "data race" not in r.stderr
    bad = variant("rw_bad", "rw_main", "rwlock.hpp", [("!writing_ && waiting_writers_ == 0", "!writing_")])
    assert bad.stdout.splitlines()[1] == "1"              # a reader overtakes the waiting writer


def test_q31():
    assert out("futex_main").splitlines() == ["0 0", "400000", "2"]
    r = run("futex_main:t")
    assert r.returncode == 0 and "data race" not in r.stderr
    with pytest.raises(subprocess.TimeoutExpired):        # forget the waiters: the last sleeper never wakes
        variant("futex_bad", "futex_main", "futex_mutex.hpp",
                [("            c = state_.exchange(2, std::memory_order_acquire);\n        }",
                  "            c = state_.exchange(1, std::memory_order_acquire);\n        }")], timeout=8)


def test_q32():
    r = iv_nagle.request_reply_ms
    assert r(2, True) == pytest.approx(0.05 + 40 + 0.05 + 0.05 + 0.05)
    assert r(2, False) == pytest.approx(0.1)
    assert r(1, True) == pytest.approx(0.1)              # one write: nothing to hold back
    assert r(5, True) == pytest.approx(r(2, True))       # the rest leave together
    assert r(2, True, quickack=True) == pytest.approx(0.2)
    assert r(2, True, delack=0.0) == pytest.approx(0.2)  # at the extreme, no delay, only one extra round trip
    s = socket.socket()
    assert s.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY) == 0
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    assert s.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY) == 1


def test_q34():
    assert py("epoll_modes") == ["[1, 1, 1]", "[1, 0, 1]"]


def test_q35():
    assert out("fork_lock").splitlines() == ["parent threads 2", "child threads 1, try_lock 0", "parent try_lock 1"]


def test_q36():
    assert out("robust").splitlines() == ["EOWNERDEAD", "0"]
    assert out("robust", "plain").splitlines() == ["ETIMEDOUT"]


def test_q37():
    a = iv_arb.Arbiter(hold=2)
    assert [a.on_packet(s) for s in (1, 1, 3, 2, 3, 5, 6, 7, 8)] == [[1], [], [], [2, 3], [], [], [], [5, 6, 7], [8]]
    assert a.gaps == [(4, 4)]
    rng = random.Random(7)
    for _ in range(300):
        n, hold = rng.randint(1, 200), rng.randint(1, 20)
        a_line = [s for s in range(1, n + 1) if rng.random() > 0.15]
        b_line = [s for s in range(1, n + 1) if rng.random() > 0.15]
        merged, i, j = [], 0, 0
        while i < len(a_line) or j < len(b_line):        # the two lines interleave at random, each in order
            if j == len(b_line) or (i < len(a_line) and rng.random() < 0.5):
                merged.append(a_line[i])
                i += 1
            else:
                merged.append(b_line[j])
                j += 1
        arb = iv_arb.Arbiter(hold=hold)
        out_seq = [x for s in merged for x in arb.on_packet(s)]
        assert out_seq == sorted(set(out_seq))           # in order, and no duplicates
        declared = {x for lo, hi in arb.gaps for x in range(lo, hi + 1)}
        assert not declared & set(out_seq)
        lost_both = set(range(1, n + 1)) - set(a_line) - set(b_line)
        last = max(out_seq, default=0)
        assert {x for x in lost_both if x < last} <= declared   # a sequence lost on both lines is always reported
        assert set(out_seq) | declared == set(range(1, arb.next))   # all that was passed is delivered or reported
        assert len(arb.pending) <= hold and all(x > arb.next for x in arb.pending)
    # with hold large enough, one line's loss never becomes a gap when the other line has it
    b = iv_arb.Arbiter(hold=64)
    seen = []
    for s in [1, 3, 2, 5, 4, 6]:
        seen += b.on_packet(s)
    assert seen == [1, 2, 3, 4, 5, 6] and b.gaps == []


def serve_watched(server, clients):
    """Runs the server on a thread and keeps any exception, so that a server that died is seen and not just silent."""
    died = []

    def body():
        try:
            iv_event_loop.serve(server, clients)
        except BaseException as e:      # noqa: BLE001
            died.append(e)

    thread = threading.Thread(target=body, daemon=True)
    thread.start()
    return thread, died


def small_buffers_server():
    """A listener's buffer sizes pass to what it accepts, so the kernel cannot take all the replies and hide the queue."""
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
    server.bind(("127.0.0.1", 0))
    server.listen(16)
    return server


def small_buffers_client(addr):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    s.connect(addr)
    return s


def test_q38():
    server = small_buffers_server()
    addr = server.getsockname()
    peak = [0]
    real_flush = iv_event_loop.flush

    def watched(ep, fd, c):
        alive = real_flush(ep, fd, c)
        peak[0] = max(peak[0], len(c.out))
        return alive

    failures = []

    def client(seed):
        rng = random.Random(seed)
        bodies = [bytes([seed]) * rng.randint(0, 4000) for _ in range(300)]
        stream = b"".join(iv_framing.frame(b) for b in bodies)
        s = small_buffers_client(addr)

        def writer():
            at = 0
            while at < len(stream):              # chopped at random; the reader lags, so the server must queue
                n = rng.randint(1, 20000)
                s.sendall(stream[at:at + n])
                at += n
            s.shutdown(socket.SHUT_WR)           # a half-close: finished sending, and still reading

        threading.Thread(target=writer, daemon=True).start()
        d, got = iv_framing.Deframer(), []
        while len(got) < len(bodies):
            chunk = s.recv(1000)
            if not chunk:
                break
            got += d.feed(chunk)
        s.close()
        if got != bodies:
            failures.append(seed)

    with mock.patch.object(iv_event_loop, "flush", watched):
        thread, died = serve_watched(server, 8)
        clients = [threading.Thread(target=client, args=(k + 1,)) for k in range(8)]
        for c in clients:
            c.start()
        for c in clients:
            c.join(timeout=60)
        assert not failures and not any(c.is_alive() for c in clients)
        thread.join(timeout=20)
    assert not thread.is_alive() and not died
    assert peak[0] > 100_000                    # the replies really did queue in out


def test_q38_bad_clients():
    """A client that closes without reading, and one that sends a length above the limit, end themselves alone."""
    for _ in range(3):
        server = small_buffers_server()
        addr = server.getsockname()
        thread, died = serve_watched(server, 3)

        rude = small_buffers_client(addr)
        rude.sendall(iv_framing.frame(b"x" * 4000) * 100)
        select.select([rude], [], [], 10)         # replies are waiting, unread, so this close sends a reset
        rude.close()

        liar = socket.create_connection(addr)
        liar.sendall(b"\xff\xff")
        liar.settimeout(10)
        try:
            assert liar.recv(10) == b""           # the server closes this client
        except ConnectionError:
            pass
        liar.close()

        good = socket.create_connection(addr)
        good.settimeout(10)
        good.sendall(iv_framing.frame(b"still here"))
        d, got = iv_framing.Deframer(), []
        while not got:
            got = d.feed(good.recv(1000))
        assert got == [b"still here"]
        good.close()
        thread.join(timeout=20)
        assert not died and not thread.is_alive()

    class Gone:
        """A socket whose peer's machine went silent: an error that is not a ConnectionError."""

        def send(self, data):
            raise TimeoutError(110, "timed out")

        def recv(self, n):
            raise TimeoutError(110, "timed out")

    c = iv_event_loop.Conn(Gone())
    c.out += b"pending"
    assert iv_event_loop.flush(None, 0, c) is False and iv_event_loop.read(c) is False


def test_q39():
    bodies = list(range(200))
    for loss in (0.0, 0.1, 0.5, 0.8):
        for seed in range(5):
            got, sent, widest = iv_reliable.send_all(bodies, window=8, loss=loss, seed=seed)
            assert got == bodies and widest <= 8 and sent >= len(bodies)
    assert iv_reliable.send_all(bodies, loss=0.0, seed=1)[1] == 200    # nothing lost, nothing resent
    assert iv_reliable.send_all(bodies, window=1, loss=0.0, seed=1)[2] == 1
    with pytest.raises(TimeoutError):
        iv_reliable.send_all(bodies, loss=1.0, max_rounds=100)
    # more loss costs more transmissions
    cost = [sum(iv_reliable.send_all(bodies, loss=x, seed=s)[1] for s in range(8)) for x in (0.0, 0.3, 0.6)]
    assert cost[0] < cost[1] < cost[2]
    # the receiver alone: an early packet waits, and a duplicate is acknowledged and not delivered twice
    rx = iv_reliable.Receiver()
    rx.on_packet(1, "b")
    assert rx.delivered == []
    rx.on_packet(0, "a")
    assert rx.delivered == ["a", "b"]
    assert rx.on_packet(0, "a") == 0 and rx.delivered == ["a", "b"] and not rx.held


def test_q40():
    assert out("shm_main").strip() == "0 9 1"
    r = run("shm_threads:t")
    assert r.returncode == 0 and r.stdout.strip() == "0" and "data race" not in r.stderr
    bad = variant("shm_bad", "shm_threads", "shm_ring.hpp",
                  [("head.store(h + 1, std::memory_order_release);", "head.store(h + 1, std::memory_order_relaxed);"),
                   ("t == head.load(std::memory_order_acquire)", "t == head.load(std::memory_order_relaxed)")], "t")
    assert "data race" in bad.stderr
