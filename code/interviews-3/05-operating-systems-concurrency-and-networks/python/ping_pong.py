import os
import resource

N = 1000
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})  # one core for both processes
to_child_r, to_child_w = os.pipe()
to_parent_r, to_parent_w = os.pipe()
pid = os.fork()
if pid == 0:
    for _ in range(N):
        os.read(to_child_r, 1)
        os.write(to_parent_w, b"x")
    os._exit(0)


def switches():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_nvcsw + usage.ru_nivcsw


before = switches()
for _ in range(N):
    os.write(to_child_w, b"x")
    os.read(to_parent_r, 1)
after = switches()
os.waitpid(pid, 0)
print(after - before)
