"""Chart CSVs of chapter 24: a London LP's quote staleness at each FX site for New York and Tokyo moves, and the share
of informed trade requests the LP's price check catches against the hold (model with stated route factors)."""
import nw_fx as n

OUT = n.ROOT / "figdata" / "networks" / "24-fx-connectivity"
LABEL = {"ld4": "LD4", "ny5": "NY5", "ny6": "NY6", "ty3": "TY3", "sg1": "SG1"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t = n.staleness_table()
    rows = ["x,site,ny,tokyo"] + [f"{i},{LABEL[v]},{t[('ny5', v)]:.2f},{t[('ty3', v)]:.2f}"
                                  for i, v in enumerate(n.VENUE_SITES)]
    (OUT / "staleness.csv").write_text("\n".join(rows) + "\n")
    c = n.caught_curves()
    rows = ["hold,equal,backbone"] + [f"{h},{a:.4f},{b:.4f}" for h, a, b in zip(n.HOLDS, c["equal"], c["backbone"],
                                                                                 strict=True)]
    (OUT / "caught.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
