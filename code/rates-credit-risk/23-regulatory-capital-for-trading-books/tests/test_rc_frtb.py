"""Tutorial of Book 6, chapter 23: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_frtb as m


def test_internal_model_below_standardised_and_stress_above_current():
    im = m.internal_models()
    assert im["es_stressed"]["all"] > im["es_current"]["all"]
    assert im["capital"] < m.standardised()["capital"]
