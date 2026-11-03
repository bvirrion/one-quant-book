"""Withdrawals from one account: one nonce per request, for good. A fee bump keeps it."""


class Sender:
    def __init__(self):
        self.next_nonce = 0
        self.by_request = {}                 # request id -> nonce
        self.fee = {}                        # nonce -> current fee

    def submit(self, request, fee):
        """Returns the transaction to broadcast: (nonce, request, fee)."""
        if request not in self.by_request:
            self.by_request[request] = self.next_nonce
            self.next_nonce += 1
        nonce = self.by_request[request]
        self.fee[nonce] = max(fee, self.fee.get(nonce, 0))
        return nonce, request, self.fee[nonce]


class Chain:
    """Mines transactions in nonce order, one per nonce, if the fee meets the market."""

    def __init__(self):
        self.next_nonce = 0
        self.mined = []
        self.pool = {}

    def broadcast(self, tx):
        nonce, _, fee = tx
        if nonce >= self.next_nonce and fee > self.pool.get(nonce, (0, 0, -1))[2]:
            self.pool[nonce] = tx            # a replacement must pay more

    def mine(self, market_fee):
        while self.next_nonce in self.pool and self.pool[self.next_nonce][2] >= market_fee:
            self.mined.append(self.pool.pop(self.next_nonce))
            self.next_nonce += 1
