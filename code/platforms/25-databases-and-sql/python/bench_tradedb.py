"""Chapter 25 measured data (not a fig_*.py): three queries on the week's 500,008 trades in SQLite without an index,
with each of two indexes, and in DuckDB; answers checked equal between engines first. Median of five runs each.
Writes measured_queries.csv (+ .meta). Run on a quiet machine."""
import pathlib
import statistics
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import pl_tradedb as P  # noqa: E402

OUT = ROOT / "figdata/platforms/25-databases-and-sql"


def timed(run, n=5):
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        out = run()
        ts.append(time.perf_counter() - t)
    return statistics.median(ts), out


def norm(rows):
    return sorted(tuple(round(x, 2) if isinstance(x, float) else x for x in r) for r in rows)


def main():
    r = P.report()
    conn = r["conn"]
    rows, answers = [], {}
    for name, ddl in P.INDEXES.items():
        for stmt in ddl:
            conn.execute(stmt)
        for q, sql in P.QUERIES.items():
            sec, out = timed(lambda sql=sql: conn.execute(sql).fetchall())
            answers.setdefault(q, norm(out))
            assert norm(out) == answers[q], (name, q)
            plan = " / ".join(P.D.plan(conn, sql)).replace(",", ";")
            rows.append([P.ENGINE_LABELS[name], q, f"{1e3 * sec:.2f}", plan])
        for stmt in ddl:
            conn.execute("DROP INDEX " + stmt.split()[2])
    duck = P.D.to_duckdb(conn, ["trades", "accounts", "instruments"])
    for q, sql in P.QUERIES.items():
        sec, out = timed(lambda sql=sql: duck.execute(sql).fetchall())
        assert norm(out) == answers[q], ("duckdb", q)
        rows.append(["DuckDB", q, f"{1e3 * sec:.2f}", "columnar scan"])
    u.write_measured(OUT / "measured_queries.csv", ["engine", "query", "ms", "plan"], rows,
                     source="code/platforms/25-databases-and-sql/python/bench_tradedb.py",
                     timer="median of five runs, in one process, database in memory; DuckDB threads=1")


if __name__ == "__main__":
    main()
