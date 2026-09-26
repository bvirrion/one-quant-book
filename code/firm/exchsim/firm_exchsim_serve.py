"""firm.exchsim live reference server in Python (slow; the C++20 server is the one to measure against).

    .venv/bin/python -m firm_exchsim serve --config cfg.json [--seconds N]      (from code/firm/exchsim)

Same configuration file and protocols as cpp/exchsim_server: SoupBinTCP 4.0 order entry over TCP (login with
credentials, sequenced replay on re-login, heartbeats), MoldUDP64 feed on lines A and B by UDP (multicast on
loopback, or unicast to dest_host with "multicast": false), TCP retransmission (20-byte MoldUDP64 request, answers
prefixed by a u16 length), drop-copy sessions, cancel on disconnect, and the input journal. Background journals and
faults are the C++ server's.

API (stable):
    Server(config: dict) ; .start() -> (oe_port, retrans_port) ; .serve_forever() ; .stop() ; .journal (bytes)
"""
from __future__ import annotations

import json
import select
import socket
import struct
import time

from firm_exchsim_codec import NT, decode, encode, journal_record, mold_packet
from firm_exchsim_engine import Engine

CTL = NT["ctl"]


def now_ns() -> int:
    return time.time_ns() % (86_400 * 1_000_000_000)


def soup(t: str, payload: bytes = b"") -> bytes:
    return struct.pack(">Hc", len(payload) + 1, t.encode()) + payload


class Server:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.engine = Engine(cfg["engine"])
        self.session = cfg["engine"].get("session", cfg["engine"]["venue"]).ljust(10)[:10]
        self.conns = [dict(conf=s, sid=i + 1, sock=None, buf=b"", sent=[], logged=False)
                      for i, s in enumerate(cfg.get("sessions", []))]
        self.journal = b""
        self.feed_seq = 0
        self.window: list[bytes] = []
        self.rt_clients: list[socket.socket] = []
        self.running = True

    def start(self) -> tuple[int, int]:
        bind = self.cfg.get("bind", "127.0.0.1")
        self.oe = socket.create_server((bind, self.cfg.get("oe_port", 0)))
        self.rt = socket.create_server((bind, self.cfg.get("retrans_port", 0)))
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.cfg.get("multicast", True):
            self.udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton("127.0.0.1"))
            self.udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
            self.udp.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        if self.cfg.get("open_now", True):
            for ev in "OSQ":
                self._input(0, encode("ctl", CTL["S"](ev)))
            self._input(0, encode("ctl", CTL["P"](0, "T", "OPEN")))
        return self.oe.getsockname()[1], self.rt.getsockname()[1]

    # -- engine --------------------------------------------------------------------------------------------------
    def _input(self, session: int, payload: bytes) -> None:
        t = now_ns()
        self.journal += journal_record(t, session, payload)
        feed, reps = self.engine.process_bytes(t, session, payload)
        if feed:
            enc = [encode("feed", m) for m in feed]
            first = self.feed_seq + 1
            self.feed_seq += len(enc)
            self.window = (self.window + enc)[-self.cfg.get("window", 100_000):]
            chunk, size = [], 0
            for e in enc:
                if chunk and size + 2 + len(e) > 1380:
                    self._send(mold_packet(self.session, first, chunk))
                    first += len(chunk)
                    chunk, size = [], 0
                chunk.append(e)
                size += 2 + len(e)
            if chunk:
                self._send(mold_packet(self.session, first, chunk))
        for sid, r in reps:
            frame = soup("S", encode("out", r))
            c = self.conns[sid - 1]
            self._deliver(c, frame)
            if type(r).__name__[-1] in "EC":
                for dc in self.conns:
                    if dc["conf"].get("drop_copy") and dc["conf"].get("firm") == c["conf"].get("firm"):
                        self._deliver(dc, frame)

    def _send(self, pkt: bytes) -> None:
        host = self.cfg.get("group", "239.192.10.1") if self.cfg.get("multicast", True) else self.cfg.get(
            "dest_host", "127.0.0.1")
        for port in (self.cfg.get("port_a", 0), self.cfg.get("port_b", 0)):
            if port:
                self.udp.sendto(pkt, (host, port))

    def _deliver(self, c: dict, frame: bytes) -> None:
        c["sent"].append(frame)
        if c["sock"] is not None:
            try:
                c["sock"].sendall(frame)
            except OSError:
                self._disconnect(c)

    # -- sessions ------------------------------------------------------------------------------------------------
    def _login(self, sock: socket.socket) -> None:
        data = b""
        while len(data) < 49:
            part = sock.recv(49 - len(data))
            if not part:
                sock.close()
                return
            data += part
        m = decode("soup_client", data[2:])
        c = next((x for x in self.conns if x["conf"]["username"] == m.username
                  and x["conf"].get("password", "") == m.password), None)
        if c is None or c["sock"] is not None:
            sock.sendall(soup("J", b"A" if c is None else b"S"))
            sock.close()
            return
        c["sock"], c["buf"] = sock, b""
        nxt = len(c["sent"]) + 1
        start = m.seq or nxt
        sock.sendall(soup("A", self.session.encode() + str(start).rjust(20).encode()))
        for f in c["sent"][start - 1:]:
            sock.sendall(f)
        if not c["logged"] and not c["conf"].get("drop_copy"):
            self._input(0, encode("ctl", CTL["L"](c["sid"], c["conf"].get("firm", 1),
                                                  "Y" if c["conf"].get("cod", True) else "N")))
            c["logged"] = True

    def _disconnect(self, c: dict) -> None:
        if c["sock"] is not None:
            c["sock"].close()
            c["sock"] = None
        if c["logged"]:
            self._input(0, encode("ctl", CTL["D"](c["sid"])))
            c["logged"] = False

    def _read(self, c: dict) -> None:
        try:
            data = c["sock"].recv(65536)
        except OSError:
            data = b""
        if not data:
            self._disconnect(c)
            return
        c["buf"] += data
        while len(c["buf"]) >= 2:
            (n,) = struct.unpack_from(">H", c["buf"])
            if len(c["buf"]) < 2 + n:
                break
            t, payload, c["buf"] = chr(c["buf"][2]), c["buf"][3:2 + n], c["buf"][2 + n:]
            if t == "U" and not c["conf"].get("drop_copy"):
                self._input(c["sid"], payload)
            elif t == "O":
                c["sock"].sendall(soup("Z"))
                self._disconnect(c)
                return

    def _retransmit(self, sock: socket.socket) -> None:
        req = sock.recv(20)
        if len(req) != 20:
            sock.close()
            self.rt_clients.remove(sock)
            return
        _, seq, count = struct.unpack(">10sQH", req)
        lo = max(1, self.feed_seq - len(self.window) + 1)
        if not lo <= seq <= self.feed_seq:
            pkt = mold_packet(self.session, seq, [])
            sock.sendall(struct.pack(">H", len(pkt)) + pkt)
            return
        count = min(count, self.cfg.get("max_retransmit", 1000), self.feed_seq - seq + 1)
        pkt = mold_packet(self.session, seq, self.window[seq - lo:seq - lo + count])
        sock.sendall(struct.pack(">H", len(pkt)) + pkt)

    def serve_forever(self, seconds: float = 0.0) -> None:
        end = time.time() + seconds if seconds else None
        hb = time.time() + 1.0
        while self.running and (end is None or time.time() < end):
            socks = [self.oe, self.rt] + [c["sock"] for c in self.conns if c["sock"] is not None] + self.rt_clients
            ready, _, _ = select.select(socks, [], [], 0.05)
            for s in ready:
                if s is self.oe:
                    conn, _ = self.oe.accept()
                    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    self._login(conn)
                elif s is self.rt:
                    self.rt_clients.append(self.rt.accept()[0])
                elif s in self.rt_clients:
                    self._retransmit(s)
                else:
                    c = next(x for x in self.conns if x["sock"] is s)
                    self._read(c)
            if time.time() >= hb:
                hb = time.time() + 1.0
                for c in self.conns:
                    if c["sock"] is not None:
                        c["sock"].sendall(soup("H"))

    def stop(self) -> None:
        self.running = False
        for c in self.conns:
            if c["sock"] is not None:
                c["sock"].close()
        for s in (self.oe, self.rt, self.udp, *self.rt_clients):
            s.close()


def serve(config_path: str, seconds: float = 0.0) -> None:
    srv = Server(json.loads(open(config_path).read()))
    oe, rt = srv.start()
    print(f"firm_exchsim serve: order entry tcp/{oe}, retransmission tcp/{rt}", flush=True)
    try:
        srv.serve_forever(seconds)
    except KeyboardInterrupt:
        pass
    srv.stop()
