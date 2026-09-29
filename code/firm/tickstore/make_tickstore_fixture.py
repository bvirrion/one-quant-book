"""Regenerate code/firm/tickstore/data/: two small flat files (versions 1 and 2) from a short simulated session and the
expected per-instrument summary the C++ and Rust readers must reproduce. Deterministic."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
for c in ("tickcap", "feedhandler", "exchsim", "bookbuilder", "pit"):
    sys.path.insert(0, str(HERE.parent / c))
sys.path.insert(0, str(HERE))
import make_recorded_day  # noqa: E402
from firm_tickcap import arbitrate, normalise, read_capture  # noqa: E402
from firm_tickstore import FlatWriter, flat_open, upgrade  # noqa: E402


def main():
    with tempfile.TemporaryDirectory() as d:
        make_recorded_day.run(0.003, 2, seed=7, out=pathlib.Path(d))
        a, b = (pathlib.Path(d) / "day_line_A.rec").read_bytes(), (pathlib.Path(d) / "day_line_B.rec").read_bytes()
    rec = normalise(arbitrate([read_capture(a), read_capture(b)])[0])[:600]
    out = HERE / "data"
    out.mkdir(exist_ok=True)
    lines = []
    for version in (1, 2):
        name = f"fixture_v{version}.flat"
        w = FlatWriter(out / name, version)
        w.append(upgrade(rec, 2) if version == 2 else rec)
        w.close()
        _, r = flat_open(out / name)
        for loc in sorted(set(int(x) for x in r["locate"])):
            m = r["locate"] == loc
            ex = m & (r["kind"] == ord("E"))
            lines.append(f"{name} {loc} {int(m.sum())} {int(r['qty'][ex].sum())} {int(r['seq'][m].max())}")
    (out / "fixture_expected.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
