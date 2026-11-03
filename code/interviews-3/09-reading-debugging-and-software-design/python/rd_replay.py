class Position:
    def __init__(self):
        self.qty = 0

    def on_fill(self, fill):
        self.qty += fill["qty"] if fill["side"] == "B" else -fill["qty"]


fills = [{"seq": 1, "side": "B", "qty": 100}, {"seq": 2, "side": "S", "qty": 30}]
p = Position()
for f in fills:
    p.on_fill(f)
for f in fills[-1:]:      # the connection dropped; on reconnect the last fill is resent
    p.on_fill(f)
print(p.qty)
