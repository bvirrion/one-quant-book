"""Chapter 19 -- event files for the book-builder benchmark and the weekend problem's ladder arithmetic."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for c in ("bookbuilder", "feedhandler", "exchsim", "tape"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
sys.path.insert(0, str(ROOT / "code/low-latency/18-the-feed-handler/python"))
import firm_bookbuilder as bb  # noqa: E402
import make_book_fixtures as mk  # noqa: E402


def large_tick_events():
    """The simulator's minute from the open (chapter 18), clean stream, normalised: a one-tick-spread instrument."""
    import ll_feed
    _, _, clean, _ = ll_feed.minute()
    return mk.fh.Handler().run(mk.fh.merge(clean, b"", b"")).events


def small_tick_events(n=100_000, move=0.0):
    """Synthetic small-tick instrument (tick 1e-4 on a price of 100): orders up to 300 ticks from the mid; `move` is
    the fraction the mid drifts over the file (0.3: the stock that moved thirty percent)."""
    return mk.small_tick(n=n, seed=11, drift=move * 1_000_000 / n)


def recentrings_trend(move_ticks, width):
    """Recentrings on a steady move: one each time the price has travelled a quarter of the ladder."""
    return int(abs(move_ticks) // (width // 4))


expected_recentrings = bb.expected_recentrings
daily_sigma_ticks = bb.daily_sigma_ticks
