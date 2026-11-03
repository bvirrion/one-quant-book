import os
import time


def state(pid):
    with open(f"/proc/{pid}/stat") as f:
        return f.read().rsplit(")", 1)[1].split()[0]


pid = os.fork()
if pid == 0:
    os._exit(7)
while state(pid) != "Z":
    time.sleep(0.001)
print("state", state(pid))
_, status = os.waitpid(pid, 0)
print("code", os.waitstatus_to_exitcode(status))
print("gone", not os.path.exists(f"/proc/{pid}"))
