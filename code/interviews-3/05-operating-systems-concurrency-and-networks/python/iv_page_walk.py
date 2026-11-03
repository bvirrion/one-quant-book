"""Splitting an x86-64 virtual address under 4-level paging with 4 KiB pages."""


def indices(addr):
    offset = addr & 0xFFF
    levels = [(addr >> shift) & 0x1FF for shift in (39, 30, 21, 12)]
    return levels, offset


def table_bytes(mapped, page=4096, levels=4):
    """Bytes of tables to map `mapped` aligned bytes: a 4 KiB table per 512 entries below."""
    entries = (mapped + page - 1) // page
    tables = 0
    for _ in range(levels):
        entries = (entries + 511) // 512     # a table at this level is an entry one level up
        tables += entries
    return tables * 4096
