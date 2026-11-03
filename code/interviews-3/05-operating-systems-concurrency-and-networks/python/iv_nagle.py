"""Small writes, then a wait for the reply, as events. Times in ms; each trip takes rtt / 2.
The peer replies once it has every piece; until then it holds its ACK for delack ms."""
import heapq


def request_reply_ms(pieces, nagle, rtt=0.1, delack=40.0, quickack=False):
    trip = rtt / 2
    events, tie = [], 0

    def at(when, what, n=0):
        nonlocal tie
        tie += 1
        heapq.heappush(events, (when, tie, what, n))

    if nagle:                                # one piece flies; the rest wait for its ACK
        at(trip, "data", 1)
        held = pieces - 1
    else:
        for _ in range(pieces):
            at(trip, "data", 1)
        held = 0
    got = 0
    while events:
        now, _, what, n = heapq.heappop(events)
        if what == "data":
            got += n
            if got == pieces:
                at(now + trip, "reply")      # the reply carries the ACK
            elif quickack:
                at(now + trip, "ack")
            else:
                at(now + delack + trip, "ack")
        elif what == "ack" and held:
            at(now + trip, "data", held)
            held = 0
        elif what == "reply":
            return now
    raise RuntimeError("no reply")
