"""Acceptance tests of firm.strathost (One Quant Book 15, chapter 12)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_strathost as S  # noqa: E402
from firm_binlog import journal_read  # noqa: E402


class Rec(S.HostedStrategy):
    def __init__(self):
        self.seen = []

    def on_book(self, ctx, top):
        self.seen.append("book")

    def on_fill(self, ctx, oid, qty, price):
        self.seen.append("fill")

    def on_timer(self, ctx, tag):
        self.seen.append("timer")


class Quoter(S.HostedStrategy):
    def __init__(self):
        self.mine = {}

    def on_book(self, ctx, top):
        b, _, a, _ = top
        live = set(ctx.working())
        self.mine = {o: sp for o, sp in self.mine.items() if o in live}
        have = set()
        for o, (side, px) in list(self.mine.items()):
            if px != (b if side == 1 else a):
                ctx.cancel(o)
                del self.mine[o]
            else:
                have.add(side)
        for side, px in ((1, b), (-1, a)):
            if side not in have and side * ctx.position < 300:
                self.mine[ctx.send(side, px, 100)] = (side, px)


class _Null:
    acked_only = False

    def send(self, *a):
        return 0

    def cancel(self, *a):
        pass

    def set_timer(self, *a):
        pass


def _host(defects):
    h = S.Host(Rec(), _Null(), defects)
    h.orders[0] = {"side": 1, "price": 1, "qty": 100, "filled": 0, "state": "live"}
    h.input(5, "timer", 1)
    h.input(5, "fill", 0, 100, 1)
    h.input(5, "book", 1, 100, 2, 100)
    h.flush()
    return h.s.seen


def test_event_model_orders_simultaneous_inputs():
    assert _host(S.FIXED) == ["book", "fill", "timer"]
    assert _host(S.Defects(arrival_order=True)) == ["timer", "fill", "book"]


def test_clean_parity_and_journal():
    prod = S.run_env("prod", Quoter(), 60.0, 3)
    sim = S.run_env("sim", Quoter(), 60.0, 3)
    rep = S.replay(prod.journal, Quoter(), S.FIXED, prod.start)
    assert len(prod.outputs) > 10 and S.compare(prod, sim).same and S.compare(prod, rep).same
    recs = journal_read(prod.journal)
    assert len(recs) == len(prod.inputs) and all(len(ev) == 48 for _, ev in recs)


def test_each_adapter_defect_diverges():
    prod_ok = S.run_env("sim", Quoter(), 60.0, 1)
    for d in ("arrival_order", "acked_working"):
        prod = S.run_env("prod", Quoter(), 60.0, 1, S.Defects(**{d: True}))
        assert not S.compare(prod, prod_ok).same, d


def test_machine_clock_and_exposure_cap():
    h = S.Host(Rec(), _Null(), S.FIXED)
    h.run.start, h.now = 1_000, 1_000 + 100 * 10**9
    assert S.machine_clock(h, None, 1.0)() == h.now and S.machine_clock(h, 0, 100.0)() == 10**9
    e = S.ProdEnv(Quoter(), S.Defects(acked_working=True))
    assert e.gw.max_long == 1_000 and e.acked_only


def test_sim_adapter_never_cancels_a_finished_order():
    e = S.SimEnv(Quoter(), S.FIXED)
    sent = []

    class Ctx:
        def cancel(self, cl):
            sent.append(cl)

    e.ctx, e.oid_cl, e.done = Ctx(), {0: 7, 1: 8}, {0}
    e.cancel(0)
    e.cancel(1)
    assert sent == [8]


def test_float_price_adapter_truncates():
    e = S.ProdEnv(Quoter(), S.Defects(float_prices=True))
    bid = e.price_in((999_900, 100, 1_000_000, 100))[0]
    assert bid == 99.99 and e.price_out(bid - 0.01) == 999_799          # not 999_800: a tick off the grid
    assert S.ProdEnv(Quoter(), S.FIXED).price_out(999_800) == 999_800
