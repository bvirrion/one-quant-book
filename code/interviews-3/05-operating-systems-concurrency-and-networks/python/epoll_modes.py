import select
import socket


def events(mode):
    a, b = socket.socketpair()
    b.setblocking(False)
    ep = select.epoll()
    ep.register(b.fileno(), select.EPOLLIN | mode)
    seen = []
    a.send(b"0123456789")
    seen.append(len(ep.poll(0)))
    b.recv(4)                                # six bytes are still unread
    seen.append(len(ep.poll(0)))
    a.send(b"x")
    seen.append(len(ep.poll(0)))
    return seen


print(events(0))
print(events(select.EPOLLET))
