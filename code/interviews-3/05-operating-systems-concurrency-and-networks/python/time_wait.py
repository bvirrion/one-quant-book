import errno
import socket


def listener(port, reuse):
    s = socket.socket()
    if reuse:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.listen()
    return s


def restart(old_reuse, new_reuse):
    server = listener(0, old_reuse)
    port = server.getsockname()[1]
    client = socket.create_connection(("127.0.0.1", port))
    conn, _ = server.accept()
    conn.close()                             # the server side closes first
    client.recv(1)
    client.close()
    server.close()
    with open("/proc/net/tcp") as f:
        waiting = any(f":{port:04X} " in row and row.split()[3] == "06" for row in f)
    try:
        listener(port, new_reuse).close()
        return waiting, "bound"
    except OSError as e:
        return waiting, errno.errorcode[e.errno]


print(restart(False, False))
print(restart(False, True))
print(restart(True, True))
