"""Crediting deposits after N confirmations, on a chain that can reorganise."""


class Deposits:
    def __init__(self, confirmations):
        self.need = confirmations
        self.blocks = {}                     # block hash -> (parent hash, height, deposits)
        self.head = None
        self.credited = {}                   # deposit id -> amount
        self.alarms = []

    def on_block(self, block, parent, height, deposits):
        self.blocks[block] = (parent, height, deposits)
        if self.head is None or height > self.blocks[self.head][1]:
            self.head = block
        self._settle()

    def _settle(self):
        safe = set()
        block, depth = self.head, 1
        while block in self.blocks:
            parent, _, deposits = self.blocks[block]
            if depth >= self.need:
                for deposit_id, amount in deposits:
                    safe.add(deposit_id)
                    self.credited.setdefault(deposit_id, amount)   # once only
            elif any(d in self.credited for d, _ in deposits):
                safe.update(d for d, _ in deposits)
            block, depth = parent, depth + 1
        for deposit_id in set(self.credited) - safe:
            self.alarms.append(deposit_id)   # credited, and now not on the best chain
            del self.credited[deposit_id]
