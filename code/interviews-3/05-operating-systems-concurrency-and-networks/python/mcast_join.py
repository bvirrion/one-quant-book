import socket
import struct
import sys

GROUP, PORT = "239.1.2.3", 0
join = sys.argv[1] == "join"
r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
r.bind(("", PORT))
port = r.getsockname()[1]
if join:
    want = struct.pack("4s4s", socket.inet_aton(GROUP), socket.inet_aton("127.0.0.1"))
    r.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, want)
r.settimeout(0.3)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton("127.0.0.1"))
s.sendto(b"tick", (GROUP, port))
try:
    print(r.recv(100))
except TimeoutError:
    print("nothing")
