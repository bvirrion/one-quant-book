import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_ubench as u


def test_quantiles_nearest_rank():
    x = list(range(1, 101))
    assert u.quantiles(x, [0.0, 0.5, 0.99, 1.0]) == [1, 51, 100, 100]


def test_machine_and_measured(tmp_path):
    m = u.machine()
    assert m["logical_cpus"] >= 1 and "date" in m
    p = tmp_path / "measured_x.csv"
    u.write_measured(p, ["a", "b"], [[1, 2]], flags="-O2")
    assert u.read_csv(p) == [{"a": "1", "b": "2"}]
    meta = (tmp_path / "measured_x.csv.meta").read_text()
    assert "flags: -O2" in meta and "isolated_cores: none" in meta


def test_compile_and_run():
    exe = u.compile_cpp(u.ROOT / "code/firm/ubench/cpp/firm_ubench_test.cpp")
    assert "ubench ok" in u.run(exe)
