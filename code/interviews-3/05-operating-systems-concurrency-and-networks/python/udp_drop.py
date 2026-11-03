import socket

r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
r.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
r.bind(("127.0.0.1", 0))
r.setblocking(False)
print(r.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for _ in range(1000):
    s.sendto(bytes(200), r.getsockname())
print("sent 1000, no error")
got = 0
try:
    while True:
        r.recv(200)
        got += 1
except BlockingIOError:
    pass
print(got < 1000)
port = f":{r.getsockname()[1]:04X} "
with open("/proc/net/udp") as f:
    print([int(row.split()[-1]) > 0 for row in f if port in row])
