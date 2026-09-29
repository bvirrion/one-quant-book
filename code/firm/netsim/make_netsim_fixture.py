"""Write data/fixture_egress.csv: a bursty stream through a small egress buffer, and the Python reference's
departures (dropped = -1). The C++20 twin must reproduce it (cpp/firm_netsim_test.cpp)."""
import pathlib

import firm_netsim as ns

HERE = pathlib.Path(__file__).resolve().parent


def main():
    t = ns.bursty_arrivals(2_000_000, 0.005, 20, 60, seed=3)
    f = [ns.frame_bytes(40 + (i * 37) % 300) for i in range(len(t))]
    r = ns.egress(t, f, 10.0, 20_000)
    rows = ["gbps,buffer,max_backlog,n_dropped", f"10.0,20000,{r.max_backlog:.6f},{r.n_dropped}",
            "t_ns,frame,depart_ns"]
    rows += [f"{a},{b},{d:.3f}" for a, b, d in zip(t.tolist(), f, r.depart_ns.tolist(), strict=True)]
    (HERE / "data" / "fixture_egress.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
