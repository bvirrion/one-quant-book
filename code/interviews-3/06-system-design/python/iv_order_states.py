"""An order as the sending side sees it. Events come from the venue, except cancel_req."""
OPEN, PENDING_NEW, PENDING_CANCEL = "open", "pending_new", "pending_cancel"
FILLED, CANCELLED, REJECTED = "filled", "cancelled", "rejected"
FINAL = {FILLED, CANCELLED, REJECTED}


class Order:
    def __init__(self, qty):
        self.qty, self.filled, self.state = qty, 0, PENDING_NEW

    def on(self, event, n=0):
        if self.state in FINAL:
            if event == "cancel_rej":        # our cancel crossed the last fill: expected
                return self.state
            raise ValueError(f"{event} after {self.state}")
        if event == "ack" and self.state == PENDING_NEW:
            self.state = OPEN
        elif event == "reject" and self.state == PENDING_NEW:
            self.state = REJECTED
        elif event == "fill" and self.state != PENDING_NEW:
            if self.filled + n > self.qty:
                raise ValueError("overfill")
            self.filled += n
            if self.filled == self.qty:
                self.state = FILLED
        elif event == "cancel_req" and self.state == OPEN:
            self.state = PENDING_CANCEL
        elif event == "cancel_ack" and self.state != PENDING_NEW:
            self.state = CANCELLED           # the venue may also cancel unasked, in a halt
        elif event == "cancel_rej" and self.state == PENDING_CANCEL:
            self.state = OPEN                # still working
        else:
            raise ValueError(f"{event} in {self.state}")
        return self.state
