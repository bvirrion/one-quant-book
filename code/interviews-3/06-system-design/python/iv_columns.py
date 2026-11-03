"""A small tick store in Parquet, by date: how much does one column cost, and which files are read?"""
import pathlib
import tempfile

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

rng = np.random.default_rng(1)
with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    for day in ("2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"):
        n = 200_000
        table = pa.table({
            "ts": np.arange(n, dtype=np.int64) * 1000,
            "price": 10_000 + rng.integers(-50, 50, n),
            "qty": rng.integers(1, 1000, n),
            "side": rng.integers(0, 2, n),
        })
        (root / f"date={day}").mkdir()
        pq.write_table(table, root / f"date={day}" / "ticks.parquet")
    meta = pq.read_metadata(root / "date=2026-01-05" / "ticks.parquet").row_group(0)
    columns = [meta.column(i) for i in range(4)]
    sizes = {c.path_in_schema: c.total_compressed_size for c in columns}
    print(round(sizes["price"] / sum(sizes.values()), 2))
    glob = f"{root}/*/*.parquet"
    query = f"""SELECT avg(price) FROM read_parquet('{glob}', hive_partitioning=1)
                WHERE date = '2026-01-06'"""
    plan = duckdb.sql("EXPLAIN " + query).fetchall()[0][1]
    print("Projections: price" in plan, "Scanning Files: 1/4" in plan)
