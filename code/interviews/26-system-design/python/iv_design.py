"""Book 18, chapter 26: the capacity estimates of the system-design answers (assumptions are arguments)."""


def feed_bytes_per_day(avg_msgs_per_s, seconds, msg_bytes):
    return avg_msgs_per_s * seconds * msg_bytes


def peak_bits_per_s(peak_msgs_per_s, msg_bytes, overhead_bytes=0):
    return peak_msgs_per_s * (msg_bytes + overhead_bytes) * 8


def book_memory(instruments, live_orders, order_bytes, levels_per_side, level_bytes):
    """Bytes for per-order records plus aggregated price levels on both sides."""
    return live_orders * order_bytes + instruments * 2 * levels_per_side * level_bytes


def risk_updates_per_s(accounts, positions_per_account, share_touched_per_tick, ticks_per_s):
    return accounts * positions_per_account * share_touched_per_tick * ticks_per_s


def symbols_per_shard(total_symbols, peak_msgs_per_s, per_shard_capacity, headroom):
    """Shards needed so that each runs at most `headroom` of its capacity, assuming symbols spread evenly."""
    shards = -(-peak_msgs_per_s // int(per_shard_capacity * headroom))
    return shards, -(-total_symbols // shards)
