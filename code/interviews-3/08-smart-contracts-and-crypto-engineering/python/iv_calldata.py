"""What a transaction's bytes cost: 16 gas for a non-zero byte, and 4 for a zero byte."""


def calldata_gas(data):
    return sum(16 if b else 4 for b in data)


def abi_transfer(to, amount):
    return bytes.fromhex("a9059cbb") + to.rjust(32, b"\0") + amount.to_bytes(32, "big")


def packed_transfer(to, amount):
    return b"\x01" + to + amount.to_bytes(12, "big").lstrip(b"\0")
