"""Chart CSVs of chapter 8: the latency model against the clock, and the candidates' points (model)."""
import nw_servers as s

OUT = s.ROOT / "figdata" / "networks" / "08-servers"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ["ghz,phi100,phi60,phi30"] + [",".join(f"{x:.1f}" if i else f"{x}" for i, x in enumerate(r))
                                          for r in s.curve()]
    (OUT / "model.csv").write_text("\n".join(rows) + "\n")
    rows = ["label,ghz,ns"] + [f"{r['name'].replace(',', '')},{r['hot_ghz']},{r['hot_ns']:.1f}" for r in s.table()]
    (OUT / "candidates.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
