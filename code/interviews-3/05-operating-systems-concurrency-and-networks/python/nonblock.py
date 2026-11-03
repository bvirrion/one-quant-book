import errno
import select
import socket

server = socket.create_server(("127.0.0.1", 0))
port = server.getsockname()[1]


def connect(p):
    s = socket.socket()
    s.setblocking(False)
    code = s.connect_ex(("127.0.0.1", p))
    select.select([], [s], [], 2)
    late = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
    return errno.errorcode.get(code, code), errno.errorcode.get(late, 0)


print(connect(port))
server.close()
print(connect(port))
