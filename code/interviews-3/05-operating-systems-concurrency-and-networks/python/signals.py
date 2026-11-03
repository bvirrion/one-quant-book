import os
import signal
import time

got = []
signal.signal(signal.SIGTERM, lambda num, frame: got.append(num))
os.kill(os.getpid(), signal.SIGTERM)
print("caught", got)
try:
    signal.signal(signal.SIGKILL, lambda num, frame: None)
except OSError:
    print("refused")
pid = os.fork()
if pid == 0:
    time.sleep(60)
    os._exit(0)
os.kill(pid, signal.SIGKILL)
print(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]))
