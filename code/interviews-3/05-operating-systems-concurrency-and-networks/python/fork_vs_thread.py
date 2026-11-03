import os
import threading

count = 0


def bump():
    global count
    count += 1


pid = os.fork()
if pid == 0:
    bump()
    os._exit(0)
os.waitpid(pid, 0)
print("after fork", count)

t = threading.Thread(target=bump)
t.start()
t.join()
print("after thread", count)
