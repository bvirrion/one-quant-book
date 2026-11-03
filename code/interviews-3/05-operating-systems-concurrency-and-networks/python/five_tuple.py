import socket

server = socket.create_server(("127.0.0.1", 0))
a = socket.create_connection(server.getsockname())
b = socket.create_connection(server.getsockname())
conn_a, _ = server.accept()
conn_b, _ = server.accept()
print(conn_a.getsockname() == conn_b.getsockname())
print(conn_a.getpeername() == conn_b.getpeername())
a.sendall(b"a")
b.sendall(b"b")
print(conn_a.recv(1), conn_b.recv(1))
