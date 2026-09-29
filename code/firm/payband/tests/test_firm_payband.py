import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_payband as pb  # noqa: E402


def scale(cap=None):
    return pb.Scale("t", {"1": pb.Band("1", 100.0, 200.0)}, {"X": 0.5}, cap)


def test_locality_and_cap():
    assert pb.at(scale(), 1, "X") == (150.0, 300.0)
    assert pb.at(scale(250.0), 1, "X") == (150.0, 250.0)


def test_overlap():
    assert pb.overlap((0, 10), (5, 15)) == 0.5 and pb.overlap((20, 30), (5, 15)) == 0.0


def test_load(tmp_path):
    b, loc = tmp_path / "b.csv", tmp_path / "l.csv"
    b.write_text("grade,min,max\n14,1,2\n")
    loc.write_text("station,rate_pct\nNY,10\n")
    s = pb.load_scale("x", b, loc, 5)
    assert s.bands["14"].hi == 2 and abs(s.locality["NY"] - 0.1) < 1e-12
