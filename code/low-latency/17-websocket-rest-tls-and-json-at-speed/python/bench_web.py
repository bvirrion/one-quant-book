"""Chapter 17 measured data (not a fig_*.py): the costs of one websocket order on this laptop.
C++ (ll_web_bench.cpp, OpenSSL for the TLS record and the library HMAC): frame decode and encode, depth decode by
structural index and by a tree-building parser, HMAC-SHA-256 four ways, AES-128-GCM seal and open of a 300-byte record.
Python (ssl on loopback): full and resumed TLS 1.3 handshakes, round trips of 300 bytes over TLS and plain TCP; the
Python reference's depth decoding and signing. Outputs measured_web.csv (key, ns) and measured_tls.csv (key, us)."""
import hashlib
import hmac
import pathlib
import socket
import statistics
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(ROOT / "code/firm/wsclient"))
import firm_ubench as u  # noqa: E402
import firm_wsclient as ws  # noqa: E402
import ll_tls as T  # noqa: E402

OUT = ROOT / "figdata/low-latency/17-websocket-rest-tls-and-json-at-speed"
SRC = "code/low-latency/17-websocket-rest-tls-and-json-at-speed/cpp/ll_web_bench.cpp"
N = 300


def cpp():
    src = HERE.parent / "cpp/ll_web_bench.cpp"
    exe = HERE.parent / "cpp/bin/ll_web_bench"
    exe.parent.mkdir(exist_ok=True)
    subprocess.run(["g++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-Wno-deprecated-declarations",
                    f"-I{src.parent}", f"-I{ROOT / 'code/firm/ubench/cpp'}", f"-I{ROOT / 'code/firm/wsclient/cpp'}",
                    str(src), "-o", str(exe), "-lcrypto"], check=True, cwd=ROOT)
    return [x.split(",") for x in u.run(exe, cpus=6).strip().splitlines()[1:]]


def median_ns(f, n):
    ts = []
    for _ in range(9):
        t = time.perf_counter_ns()
        for i in range(n):
            f(i)
        ts.append((time.perf_counter_ns() - t) / n)
    return statistics.median(ts)


def python_costs():
    ups = (ROOT / "code/firm/wsclient/data/depth_updates.jsonl").read_text().splitlines()
    secret = "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
    payload = ("symbol=BTCUSDT&side=BUY&type=LIMIT&timeInForce=GTC&quantity=0.01&price=64123.25&recvWindow=5000"
               "&timestamp=1758800000123")
    s = ws.Signer(secret)
    msg, key = b"x" * 300, b"\x01\x02\x03\x04"
    wire = ws.encode_frame(msg, mask_key=key)
    return [["py_frame_decode", f"{median_ns(lambda i: ws.decode_frame(wire), 2000):.1f}"],
            ["py_frame_encode", f"{median_ns(lambda i: ws.encode_frame(msg, mask_key=key), 2000):.1f}"],
            ["py_depth", f"{median_ns(lambda i: ws.decode_depth(ups[i]), len(ups)):.1f}"],
            ["py_sign_precomputed", f"{median_ns(lambda i: s.sign(payload), 2000):.1f}"],
            ["py_sign_rekey", f"{median_ns(lambda i: hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest(), 2000):.1f}"]]  # noqa: E501


def tls():
    with tempfile.TemporaryDirectory() as d:
        srv_ctx, cli = T.contexts(*T.make_cert(d))
        tls_srv, plain_srv = T.Server(srv_ctx), T.Server(None)
        tls_srv.start()
        plain_srv.start()
        full = [T.handshake(cli, tls_srv.port)[0] for _ in range(N)]
        _, _, sess = T.handshake(cli, tls_srv.port)
        res, reused = [], 0
        for _ in range(N):
            dt, r, sess = T.handshake(cli, tls_srv.port, sess)
            res.append(dt)
            reused += r
        raw = socket.create_connection(("127.0.0.1", tls_srv.port))
        raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s = cli.wrap_socket(raw, server_hostname="localhost")
        s.recv(1)
        rt_tls = T.round_trips(s, 5000)
        p = socket.create_connection(("127.0.0.1", plain_srv.port))
        p.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        p.recv(1)
        rt_plain = T.round_trips(p, 5000)
    us = 1e6
    return [["handshake_full", f"{statistics.median(full) * us:.1f}"],
            ["handshake_resumed", f"{statistics.median(res) * us:.1f}"],
            ["rtt_tls", f"{statistics.median(rt_tls) * us:.1f}"],
            ["rtt_plain", f"{statistics.median(rt_plain) * us:.1f}"]], reused


def budget(web, tls_rows):
    """One order: the depth update that triggers it is received (TLS record opened, frame decoded, JSON decoded) and
    the order is sent (signed, framed and masked, TLS record sealed); CPU time of each step in microseconds, for the
    C++ components and for the Python reference. Python's per-record TLS cost is a quarter of the extra round-trip
    time over TLS (four record operations per round trip)."""
    w = {k: float(v) / 1000 for k, v in web}
    t = {k: float(v) for k, v in tls_rows}
    py_rec = (t["rtt_tls"] - t["rtt_plain"]) / 4
    return [["cpp", w["aead_open"], w["frame_decode"], w["depth_index"], w["sign_openssl_pre"], w["frame_encode"],
             w["aead_seal"]],
            ["python", py_rec, w["py_frame_decode"], w["py_depth"], w["py_sign_precomputed"], w["py_frame_encode"],
             py_rec]]


def main():
    meta = dict(cpus="6 (C++); Python unpinned", source=SRC, openssl=subprocess.run(
        ["openssl", "version"], capture_output=True, text=True).stdout.strip(),
                python=sys.version.split()[0])
    web = cpp() + python_costs()
    u.write_measured(OUT / "measured_web.csv", ["key", "ns"], web, **meta)
    rows, reused = tls()
    assert reused == N, f"only {reused} of {N} handshakes resumed"
    u.write_measured(OUT / "measured_tls.csv", ["key", "us"], rows, resumed=f"{reused}/{N}", **meta)
    b = [[r[0], *(f"{x:.3f}" for x in r[1:])] for r in budget(web, rows)]
    u.write_measured(OUT / "measured_budget.csv", ["path", "tls_open", "frame_decode", "json", "sign",
                                                   "frame_encode", "tls_seal"], b, **meta)
    steps = ["tls_open", "frame_decode", "json", "sign", "frame_encode", "tls_seal"]
    u.write_measured(OUT / "measured_budget_steps.csv", ["step", "cpp", "python"],
                     [[s, b[0][i + 1], b[1][i + 1]] for i, s in enumerate(steps)], **meta)


if __name__ == "__main__":
    main()
