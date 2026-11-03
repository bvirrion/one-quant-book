"""Replacing a file so that a crash leaves either the old contents or the new, never a mix."""
import os


def atomic_save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())                 # the new bytes are on disk
    os.replace(tmp, path)                    # the name moves in one step
    fd = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
    try:
        os.fsync(fd)                         # and the move itself is on disk
    finally:
        os.close(fd)
