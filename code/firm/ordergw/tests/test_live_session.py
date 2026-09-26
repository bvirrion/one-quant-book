"""firm.ordergw against Book 10's live Python server on loopback: login, orders through the gateway, a lost connection
(cancel on disconnect), a new login that replays what was missed, and the drop copy reconciled with zero breaks."""
import pathlib
import socket
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "exchsim"))
import firm_ordergw as gw  # noqa: E402
from firm_exchsim_codec import NT, decode, encode  # noqa: E402
from firm_exchsim_serve import Server  # noqa: E402

CFG = {"engine": {"venue": "SIMX", "session": "SIMX      ", "engine_ns": 500,
                  "fees": {"unit": "share", "make": -2000, "take": 3000, "cross": 0},
                  "throttle": {"rate": 0, "burst": 0},
                  "instruments": [{"locate": 1, "symbol": "SIM1", "tick": 100, "lot": 100, "matching": "F",
                                   "start_price": 1_000_000}]},
       "multicast": False, "port_a": 0, "port_b": 0,
       "sessions": [{"username": "HF1", "password": "a", "firm": 1},
                    {"username": "HF1DC", "password": "b", "firm": 1, "drop_copy": True},
                    {"username": "MM2", "password": "c", "firm": 2}]}


class Client:
    def __init__(self, port, user, pw):
        self.port, self.s = port, gw.Session(user, pw)
        self.buf, self.sock = b"", None

    def connect(self):
        self.sock = socket.create_connection(("127.0.0.1", self.port))
        self.sock.sendall(self.s.login(time.monotonic_ns()))
        return self.read(0)

    def read(self, n, timeout=2.0):
        """Reads frames until the login is accepted and n sequenced messages have arrived."""
        self.sock.settimeout(timeout)
        got = []
        while not self.s.logged_in or len(got) < n:
            self.buf += self.sock.recv(65536)
            fr, self.buf = gw.frames(self.buf)
            for typ, payload in fr:
                app = self.s.on_frame(time.monotonic_ns(), typ, payload)
                if app is not None:
                    got.append(decode("out", app))
        return got

    def drop(self):
        self.sock.close()
        self.s.disconnected()


def apply(g, reports):
    for r in reports:
        k = type(r).__name__[-1]
        g.on_report(0, k, r.cl_ord_id, qty=getattr(r, "qty", 0), price=getattr(r, "price", 0),
                    leaves=getattr(r, "leaves", 0), reason=getattr(r, "reason", ""),
                    new_cl=getattr(r, "new_cl_ord_id", 0))


def to_wire(msg):
    _, cl, side, qty, price = msg
    return encode("in", NT["in"]["O"](cl, 1, side, qty, price, "D", "Y", "N", 0, 0, 0, "N", 0))


def test_session_cancel_on_disconnect_replay_and_drop_copy():
    srv = Server(CFG)
    oe, _ = srv.start()
    th = threading.Thread(target=srv.serve_forever, args=(8.0,))
    th.start()
    try:
        hf, dc, mm = Client(oe, "HF1", "a"), Client(oe, "HF1DC", "b"), Client(oe, "MM2", "c")
        for c in (hf, dc, mm):
            c.connect()
        g = gw.Gateway(max_long=300)
        for cl, price in ((1, 999_900), (2, 999_800), (3, 999_700)):
            kind, msg = g.new(0, cl, "B", 100, price)
            assert kind == "send"
            hf.sock.sendall(hf.s.send(0, to_wire(msg)))
        apply(g, hf.read(3))
        assert g.new(0, 4, "B", 100, 999_600) == ("refused", "exposure")   # 300 working: the limit is reached
        # a seller takes the best bid: order 1 fills; the report reaches us and the drop copy
        mm.sock.sendall(mm.s.send(0, encode("in", NT["in"]["O"](9, 1, "S", 100, 0, "I", "Y", "N", 0, 0, 0, "N", 0))))
        apply(g, hf.read(1))
        assert g.position == 100 and g.orders[1].state == "filled"
        # the connection is lost: the venue cancels orders 2 and 3 (reason D) while we are away
        seen = hf.s.next_seq
        hf.drop()
        time.sleep(0.3)
        assert g.worst_long() == 300                 # until we hear otherwise, the two orders may still fill
        reps = hf.connect() or hf.read(2)
        assert hf.s.logins == 2 and hf.s.next_seq == seen + 2
        assert sorted((type(r).__name__[-1], r.reason) for r in reps) == [("C", "D"), ("C", "D")]
        apply(g, reps)
        assert g.worst_long() == 100 and {o.state for cl, o in g.orders.items() if cl != 1} == {"cancelled"}
        drop = [(type(r).__name__[-1], r.cl_ord_id, getattr(r, "qty", 0)) for r in dc.read(3)]
        assert gw.reconcile(g, drop) == []
        for c in (hf, dc, mm):
            c.drop()
    finally:
        srv.running = False
        th.join()
        srv.stop()
