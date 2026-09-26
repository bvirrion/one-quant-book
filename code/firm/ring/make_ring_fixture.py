"""Write data/ring_image.bin: the byte image of an SPSC ring (capacity 8, slots of 64 bytes) after "msg-0".."msg-4"
were written and two were read, laid out from the specification in cpp/firm_ring.hpp, independently of the C++ and
Rust code, which must both reproduce it byte for byte."""
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
CAP, SLOT, HEADER = 8, 64, 192


def image():
    b = bytearray(HEADER + CAP * SLOT)
    struct.pack_into("<QIIQ", b, 0, int.from_bytes(b"FIRMRING", "little"), 1, SLOT, CAP)
    struct.pack_into("<Q", b, 64, 5)     # write sequence
    struct.pack_into("<Q", b, 128, 2)    # read sequence
    for k in range(5):
        msg = f"msg-{k}".encode()
        struct.pack_into("<I", b, HEADER + k * SLOT, len(msg))
        b[HEADER + k * SLOT + 4:HEADER + k * SLOT + 4 + len(msg)] = msg
    return bytes(b)


def main():
    (HERE / "data/ring_image.bin").write_bytes(image())


if __name__ == "__main__":
    main()
