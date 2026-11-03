import socket

receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver.bind(("127.0.0.1", 0))
sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sender.sendto(b"abc", receiver.getsockname())
sender.sendto(b"de", receiver.getsockname())
print(receiver.recv(100), receiver.recv(100))

server = socket.create_server(("127.0.0.1", 0))
client = socket.create_connection(server.getsockname())
conn, _ = server.accept()
client.sendall(b"abc")
client.sendall(b"de")
client.close()
chunks = []
while chunk := conn.recv(100):
    chunks.append(chunk)
print(b"".join(chunks))
