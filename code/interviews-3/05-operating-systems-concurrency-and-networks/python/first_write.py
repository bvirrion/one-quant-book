import select
import socket

server = socket.create_server(("127.0.0.1", 0))
client = socket.create_connection(server.getsockname())
conn, _ = server.accept()
conn.close()
print(client.send(b"one"))
waiter = select.poll()
waiter.register(client, 0)                   # only an error or a hang-up wakes it
waiter.poll(2000)                            # so this waits for the peer's reset
try:
    client.send(b"two")
except OSError as e:
    print(type(e).__name__)
