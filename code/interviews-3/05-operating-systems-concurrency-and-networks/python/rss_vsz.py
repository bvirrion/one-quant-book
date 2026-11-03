import mmap

MB = 1 << 20


def sizes():
    fields = {}
    with open("/proc/self/status") as f:
        for line in f:
            key, _, rest = line.partition(":")
            if key in ("VmSize", "VmRSS"):
                fields[key] = int(rest.split()[0]) // 1024
    return fields["VmSize"], fields["VmRSS"]


v0, r0 = sizes()
m = mmap.mmap(-1, 1024 * MB, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
v1, r1 = sizes()
for offset in range(0, 100 * MB, 4096):
    m[offset] = 1
v2, r2 = sizes()
print(v1 - v0, r1 - r0)
print(v2 - v1, r2 - r1)
