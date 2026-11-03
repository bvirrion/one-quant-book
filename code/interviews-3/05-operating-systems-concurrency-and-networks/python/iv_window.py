"""A window protocol: what one round trip can carry, and a round-by-round model of it."""


def bandwidth_delay_bytes(link_bps, rtt_s):
    return link_bps * rtt_s / 8


def steady_rate_bps(window_bytes, rtt_s, link_bps):
    return min(window_bytes * 8 / rtt_s, link_bps)


def simulate_bytes(window_bytes, rtt_s, link_bps, seconds):
    """Each round trip sends one window, capped by what the link carries in one round trip."""
    per_round = min(window_bytes, link_bps * rtt_s / 8)
    return per_round * int(seconds / rtt_s)
