"""One thread, many clients: an epoll echo server for length-prefixed frames, with partial reads and writes."""
import select

from iv_framing import Deframer, frame


class Conn:
    def __init__(self, sock):
        self.sock = sock
        self.reader = Deframer()
        self.out = bytearray()
        self.eof = False                     # the peer has finished sending


def serve(listener, stop_after_clients):
    listener.setblocking(False)
    ep = select.epoll()
    ep.register(listener.fileno(), select.EPOLLIN)
    conns, closed = {}, 0
    while closed < stop_after_clients:
        for fd, event in ep.poll():
            if fd == listener.fileno():
                sock, _ = listener.accept()
                sock.setblocking(False)
                conns[sock.fileno()] = Conn(sock)
                ep.register(sock.fileno(), select.EPOLLIN)
                continue
            c = conns[fd]
            alive = True
            if event & (select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR):
                alive = read(c)
            if alive and flush(ep, fd, c):
                continue
            ep.unregister(fd)                # this client goes, and nobody else
            c.sock.close()
            del conns[fd]
            closed += 1
    ep.close()


def read(c):
    """Takes what has arrived. False if this connection must go."""
    try:
        data = c.sock.recv(65536)
        if not data:                         # it may still be reading our replies
            c.eof = True
        for body in c.reader.feed(data):
            c.out += frame(body)
    except BlockingIOError:
        pass
    except (OSError, ValueError):            # a reset, or a length above the limit
        return False
    return True


def flush(ep, fd, c):
    """Sends what the socket will take. False if this connection must go."""
    if c.out:
        try:
            del c.out[:c.sock.send(c.out)]   # may take only part
        except BlockingIOError:
            pass
        except OSError:                      # a reset: the replies have nowhere to go
            return False
    if c.eof and not c.out:
        return False
    ep.modify(fd, (0 if c.eof else select.EPOLLIN) | (select.EPOLLOUT if c.out else 0))
    return True
