"""The Ethernet address of an IPv4 group: 01:00:5e and the low 23 bits of the group."""
import ipaddress


def group_mac(group):
    low = int(ipaddress.IPv4Address(group)) & 0x7FFFFF
    return "01:00:5e:" + ":".join(f"{(low >> s) & 0xFF:02x}" for s in (16, 8, 0))
