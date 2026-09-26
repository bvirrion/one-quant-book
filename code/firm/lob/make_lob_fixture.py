"""Write the shared fixture of firm.lob: five simulated minutes of firm.tape messages and the level-2 state
(five levels a side) after every 25th message, which the C++20 and Rust twins must reproduce.

    .venv/bin/python code/firm/lob/make_lob_fixture.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
from firm_lob import MessageBook, apply_tape, l2_lines  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402


def main() -> None:
    tape = simulate(TapeConfig(seconds=300.0, news_at=None, seed=5))
    rows = ["kind,oid,side,price,qty"]
    rows += [f"{m['kind'].decode()},{m['oid']},{m['side']},{m['price']},{m['qty']}" for m in tape.msgs]
    (HERE / "data" / "fixture_msgs.csv").write_text("\n".join(rows) + "\n")
    out = []
    for i, book in enumerate(apply_tape(MessageBook(), tape.msgs)):
        if i % 25 == 24:
            out.append(f"# {i + 1}\n" + l2_lines(book, 5))
    (HERE / "data" / "fixture_l2.txt").write_text("\n".join(out) + "\n")
    print(len(tape.msgs), "messages,", len(out), "snapshots")


if __name__ == "__main__":
    main()
