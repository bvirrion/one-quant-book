import socket

server = socket.create_server(("127.0.0.1", 0), backlog=5)
client = socket.create_connection(server.getsockname())
client.sendall(b"early")
print("connected and sent")
conn, _ = server.accept()
print(conn.recv(100))
