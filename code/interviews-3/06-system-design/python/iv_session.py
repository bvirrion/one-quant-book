"""Resending after a reconnect: messages keep their numbers, and stale orders do not go."""


class Sender:
    def __init__(self, max_age):
        self.max_age = max_age
        self.sent = []                       # (sequence number, send time, kind, body)

    def send(self, now, kind, body):
        self.sent.append((len(self.sent) + 1, now, kind, body))
        return self.sent[-1]

    def resend(self, begin, now):
        out = []
        for seq, sent_at, kind, body in self.sent[begin - 1 :]:
            if kind == "order" and now - sent_at > self.max_age:
                out.append((seq, sent_at, "gap_fill", None))   # the number stands
            else:
                out.append((seq, sent_at, kind, body))
        return out


class Receiver:
    def __init__(self):
        self.expected = 1
        self.accepted = []

    def on_message(self, message):
        seq, _, kind, body = message
        if seq > self.expected:
            return self.expected             # ask for a resend from here
        if seq == self.expected:
            self.expected += 1
            if kind != "gap_fill":
                self.accepted.append(body)
        return None
