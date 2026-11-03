import mmap
import os
import tempfile

with tempfile.TemporaryFile() as f:
    f.write(b"aaaa")
    f.flush()
    fd = f.fileno()
    shared = mmap.mmap(fd, 4, flags=mmap.MAP_SHARED)
    private = mmap.mmap(fd, 4, flags=mmap.MAP_PRIVATE)
    shared[0:1] = b"S"
    private[1:2] = b"P"
    print(os.pread(fd, 4, 0), shared[:4], private[:4])
    shared[2:3] = b"T"
    print(os.pread(fd, 4, 0), shared[:4], private[:4])
