"""Chapter 17 -- TLS on loopback with Python's ssl module: a self-signed certificate, a server thread, full and
resumed handshakes, and round trips of small messages over TLS and over plain TCP."""
import socket
import ssl
import subprocess
import threading
import time


def make_cert(d):
    key, cert = f"{d}/key.pem", f"{d}/cert.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes",
                    "-keyout", key, "-out", cert, "-days", "1", "-subj", "/CN=localhost",
                    "-addext", "subjectAltName=DNS:localhost"], check=True, capture_output=True)
    return cert, key


class Server(threading.Thread):
    """Accepts connections forever; over each, sends one byte (so that the client receives its session tickets),
    then echoes whatever arrives."""

    def __init__(self, ctx):
        super().__init__(daemon=True)
        self.ctx = ctx
        self.sock = socket.create_server(("127.0.0.1", 0))
        self.port = self.sock.getsockname()[1]

    def run(self):
        while True:
            c, _ = self.sock.accept()
            threading.Thread(target=self.serve, args=(c,), daemon=True).start()

    def serve(self, c):
        try:
            s = self.ctx.wrap_socket(c, server_side=True) if self.ctx else c
            s.sendall(b"!")
            while True:
                b = s.recv(4096)
                if not b:
                    break
                s.sendall(b)
        except (OSError, ssl.SSLError):
            pass


def contexts(cert, key):
    srv = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    srv.minimum_version = ssl.TLSVersion.TLSv1_3
    srv.load_cert_chain(cert, key)
    cli = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    cli.minimum_version = ssl.TLSVersion.TLSv1_3
    cli.load_verify_locations(cert)
    return srv, cli


def handshake(cli, port, session=None):
    """Seconds from connect to the end of the handshake, whether the session was resumed, and the new session."""
    t = time.perf_counter()
    raw = socket.create_connection(("127.0.0.1", port))
    s = cli.wrap_socket(raw, server_hostname="localhost", session=session)
    dt = time.perf_counter() - t
    s.recv(1)                    # the server's byte: the session tickets have arrived with it
    reused, new = s.session_reused, s.session
    s.close()
    return dt, reused, new


def round_trips(sock, n, size=300):
    msg = b"x" * size
    out = []
    for _ in range(n):
        t = time.perf_counter()
        sock.sendall(msg)
        got = 0
        while got < size:
            got += len(sock.recv(4096))
        out.append(time.perf_counter() - t)
    return out
