"""Numbers gate: every numerical answer printed in Book 12, chapter 16 (text and solutions). Fits five generators and
the GAN twice more (about two minutes on one core)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_gen as m  # noqa: E402


def test_data_and_garch():
    D = m.data()
    assert len(D["crashes"]) == 6 and len(D["r"]) == 7560
    mu, om, a, b, nu = m.garch_params()
    assert (round(a, 3), round(b, 3), round(nu, 1), round(a + b, 3)) == (0.079, 0.886, 3.6, 0.964)
    assert round(math.log(0.5) / math.log(a + b), 1) == 19.1


def test_judge():
    j = m.judge()
    got = {k: (sum(v["scorecard"].values()), round(v["c2st"], 3), round(v["tstr"][0], 3), round(v["tstr"][1], 2),
               round(v["tsts"][1], 2) if "tsts" in v else None, round(100 * v["close"], 1)) for k, v in j.items()}
    assert got == {"real": (6, 0.545, 0.078, 0.86, None, 5.0),
                   "block bootstrap": (6, 0.491, 0.062, 0.71, 1.19, 14.5),
                   "GARCH-t": (4, 0.539, -0.019, -0.10, -0.09, 5.7),
                   "VAE": (6, 0.619, 0.040, 0.76, 0.79, 5.1),
                   "GAN": (3, 0.749, 0.052, 0.52, 10.68, 11.2),
                   "diffusion": (4, 0.693, 0.030, 0.23, 1.45, 1.4)}
    assert (round(j["VAE"]["tstr sd"][1], 2), round(j["GARCH-t"]["tstr sd"][1], 2)) == (0.28, 0.65)
    f = {k: j[k]["facts"] for k in ("real", "VAE", "GAN", "diffusion")}
    assert (round(f["real"]["kurtosis"], 1), round(f["VAE"]["kurtosis"], 1), round(f["GAN"]["kurtosis"], 1),
            round(f["diffusion"]["kurtosis"], 1)) == (13.0, 11.1, 2.0, 4.0)
    assert (round(f["GAN"]["ac1"], 3), round(f["real"]["ac1"], 3)) == (0.099, 0.078)
    assert [k for k, v in j["GARCH-t"]["scorecard"].items() if not v] == ["leverage effect", "gain-loss asymmetry"]


def test_exercises():
    assert round(math.sqrt(0.25 / 4000), 4) == 0.0079 and round((0.62 - 0.5) / 0.0079) == 15
    assert round(0.01 / 0.0079, 1) == 1.3
    assert round(m.c2st_random_split(), 2) == 0.83
    g = {k: (round(a, 2), round(b, 3), round(c, 1)) for k, (a, b, c) in m.gan_steps().items()}
    assert g == {1000: (2.53, 0.884, 11.2), 8000: (2.49, 0.734, 9.9)}
