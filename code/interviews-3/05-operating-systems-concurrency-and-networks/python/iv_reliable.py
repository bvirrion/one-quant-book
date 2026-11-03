"""Selective repeat over a lossy link, in rounds. Each round the sender transmits every unacked packet in its window;
the link may lose, duplicate or reorder them, and ACKs may be lost too."""
import random


class Receiver:
    def __init__(self):
        self.next = 0
        self.held = {}
        self.delivered = []

    def on_packet(self, seq, body):
        if seq >= self.next:
            self.held[seq] = body
        while self.next in self.held:
            self.delivered.append(self.held.pop(self.next))
            self.next += 1
        return seq                           # acknowledge every packet, even a duplicate


def send_all(bodies, window=8, loss=0.0, seed=0, max_rounds=100000):
    """Returns (delivered, transmissions, largest window used), or raises TimeoutError."""
    rng = random.Random(seed)
    rx = Receiver()
    base, acked = 0, set()
    sent = widest = 0
    for _ in range(max_rounds):
        while base in acked:
            base += 1
        if base == len(bodies):
            return rx.delivered, sent, widest
        flight = [s for s in range(base, min(base + window, len(bodies))) if s not in acked]
        widest = max(widest, max(flight) - base + 1)
        rng.shuffle(flight)
        for seq in flight:
            sent += 1
            copies = 2 if rng.random() < 0.05 else 1
            for _ in range(copies):
                if rng.random() >= loss:
                    ack = rx.on_packet(seq, bodies[seq])
                    if rng.random() >= loss:
                        acked.add(ack)
    raise TimeoutError("link too lossy")
