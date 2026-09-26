"""The Python live server on loopback: login, an order, its report, and a retransmission."""
import pathlib
import socket
import struct
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from firm_exchsim_codec import NT, decode, encode, mold_parse, soup_encode, soup_parse  # noqa: E402
from firm_exchsim_serve import Server  # noqa: E402

CFG = {"engine": {"venue": "SIMX", "session": "SIMX      ", "engine_ns": 500,
                  "fees": {"unit": "share", "make": -2000, "take": 3000, "cross": 0},
                  "throttle": {"rate": 0, "burst": 0},
                  "instruments": [{"locate": 1, "symbol": "SIM1", "tick": 100, "lot": 100, "matching": "F",
                                   "start_price": 1_000_000}]},
       "multicast": False, "port_a": 0, "port_b": 0,
       "sessions": [{"username": "HF1", "password": "a", "firm": 1}]}


def recv_frames(sock, n, timeout=2.0):
    sock.settimeout(timeout)
    buf, out = b"", []
    while len(out) < n:
        buf += sock.recv(65536)
        frames, buf = soup_parse(buf)
        out += frames
    return out


def test_python_server_round_trip():
    srv = Server(CFG)
    oe, rt = srv.start()
    th = threading.Thread(target=srv.serve_forever, args=(5.0,))
    th.start()
    try:
        c = socket.create_connection(("127.0.0.1", oe))
        c.sendall(soup_encode("soup_client", NT["soup_client"]["L"]("HF1", "a", "", 0)))
        frames = recv_frames(c, 1)
        assert frames[0][0] == "A"
        o = NT["in"]["O"](1, 1, "B", 100, 999_900, "D", "Y", "N", 0, 0, 0, "N", 0)
        c.sendall(soup_encode("soup_client", NT["soup_client"]["U"](encode("in", o))))
        rep = [decode("out", p) for t, p in recv_frames(c, 2) if t == "S"]
        assert any(type(r).__name__ == "Out_A" and r.cl_ord_id == 1 for r in rep)
        r = socket.create_connection(("127.0.0.1", rt))
        r.sendall(struct.pack(">10sQH", b"SIMX      ", 1, 2))
        r.settimeout(2.0)
        data = r.recv(4096)
        _, seq, count, msgs = mold_parse(data[2:])
        assert seq == 1 and count == 2 and len(msgs) == 2
        r.close()
        c.close()
    finally:
        srv.running = False
        th.join()
        srv.stop()
    assert srv.journal and srv.engine.trades == []
