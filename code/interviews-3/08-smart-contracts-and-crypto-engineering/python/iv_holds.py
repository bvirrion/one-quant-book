"""An exchange's balances: an open order holds funds, so they cannot be spent twice."""


class Balances:
    def __init__(self):
        self.free = {}
        self.held = {}

    def deposit(self, who, amount):
        self.free[who] = self.free.get(who, 0) + amount

    def hold(self, who, amount):
        if amount <= 0 or self.free.get(who, 0) < amount:
            return False
        self.free[who] -= amount
        self.held[who] = self.held.get(who, 0) + amount
        return True

    def release(self, who, amount):
        self.held[who] -= amount
        self.free[who] += amount

    def settle(self, payer, payee, amount):
        """A trade pays from the payer's hold to the payee's free balance."""
        self.held[payer] -= amount
        self.free[payee] = self.free.get(payee, 0) + amount

    def withdraw(self, who, amount):
        if self.free.get(who, 0) < amount:
            return False
        self.free[who] -= amount
        return True
