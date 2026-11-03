import socket

r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
r.bind(("127.0.0.1", 0))
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b"abcdefgh", r.getsockname())
s.sendto(b"ij", r.getsockname())
print(r.recv(4), r.recv(4))
s.sendto(bytes(65507), r.getsockname())
print(len(r.recv(65535)))
try:
    s.sendto(bytes(65508), r.getsockname())
except OSError as e:
    print(e.strerror)
