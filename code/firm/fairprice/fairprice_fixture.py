"""Writes data/fixture_*.csv: three sources' observations from a short firm.tape run and the Python filter's output,
replayed by cpp/ and rust/."""
import pathlib
import sys
from dataclasses import replace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
import firm_fairprice as fp  # noqa: E402
import firm_tape as ft  # noqa: E402

Q, R = 0.05, (0.10, 0.12, 0.15)


def events():
    cfg = replace(ft.TapeConfig(), seconds=120.0, news_at=None, seed=5)
    a, b = ft.simulate_pair(cfg, 0.5)
    c = ft.simulate(replace(cfg, seed=17))
    rows = []
    for k, tp in enumerate((a, b, c)):
        top = tp.top[tp.n_open - 1:]
        mid = 0.5 * (top["bid"] + top["ask"])
        rows += [(float(t), k, float(m)) for t, m in zip(top["t"], mid, strict=True)]
    rows.sort(key=lambda r: (r[0], r[1]))
    return rows[:3000]


if __name__ == "__main__":
    ev = events()
    f = fp.FairFilter(Q, R)
    out = []
    for t, s, y in ev:
        out.append((f.update(t, s, y), f.p))
    d = HERE / "data"
    (d / "fixture_params.csv").write_text("q,r0,r1,r2\n" + ",".join(repr(x) for x in (Q, *R)) + "\n")
    (d / "fixture_events.csv").write_text("t,src,y\n" + "".join(f"{t!r},{s},{y!r}\n" for t, s, y in ev))
    (d / "fixture_expected.csv").write_text("x,p\n" + "".join(f"{x!r},{p!r}\n" for x, p in out))
    print(len(ev), "events")
