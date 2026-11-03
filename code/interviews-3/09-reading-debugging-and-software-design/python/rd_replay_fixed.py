class Position:
    def __init__(self):
        self.qty = 0
        self.last_seq = {}        # session -> the highest sequence number applied

    def on_fill(self, session, fill):
        if fill["seq"] <= self.last_seq.get(session, 0):
            return                # already applied: a resend changes nothing
        if fill["seq"] != self.last_seq.get(session, 0) + 1:
            raise RuntimeError("gap: stop and recover before going on")
        self.qty += fill["qty"] if fill["side"] == "B" else -fill["qty"]
        self.last_seq[session] = fill["seq"]
