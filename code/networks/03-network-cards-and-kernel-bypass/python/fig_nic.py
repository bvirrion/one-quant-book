"""Chart CSV of chapter 3: the coalescing model's latency and CPU against the coalescing timer (model values)."""
import nw_nic as n

TIMERS = (0, 2, 4, 8, 16, 32, 64)


def main():
    n.FIG.mkdir(parents=True, exist_ok=True)
    rows = ["timer_us,lat_01,cpu_01,lat_05,cpu_05"]
    for u in TIMERS:
        m = 1 if u == 0 else 10_000                      # timer-driven: the frame count never binds
        a, b = n.coalesce(0.1, u, m), n.coalesce(0.5, u, m)
        ok = b['cpu'] < 1.0          # at 0.5 per us without coalescing the host saturates
        right = f"{b['mean_us']:.2f},{b['cpu']:.3f}" if ok else "nan,nan"
        rows.append(f"{u},{a['mean_us']:.2f},{a['cpu']:.3f},{right}")
    (n.FIG / "coalesce.csv").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
