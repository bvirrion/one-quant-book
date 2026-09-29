import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_industrymap as im  # noqa: E402


def E(sic="", fam=(), truth="market maker"):
    return im.Entity("x", 1, sic, frozenset(fam), truth)


def test_every_model_has_a_group_and_books():
    assert set(im.GROUP.values()) == {"principal trading", "investment manager", "bank", "infrastructure"}
    assert set(im.BOOKS) == set(im.MODELS)


def test_sic_rule():
    assert im.sic_class("6021") == "bank" and im.sic_class("") == im.UNKNOWN and im.sic_class("9999") == im.UNKNOWN


def test_forms_rule_and_fallback():
    assert im.forms_class({"broker-dealer", "13F"}) == "market maker"
    assert im.forms_class({"13F"}) == "systematic fund"
    assert im.forms_class({"issuer", "broker-dealer"}) == im.UNKNOWN
    assert im.combined(E("6021", {"issuer"})) == "bank"


def test_score_levels():
    es = [E(fam={"13F"}, truth="multi-manager platform"), E(fam={"broker-dealer"})]
    assert im.score(es, im.by_forms, "coarse") == (2, 2)
    assert im.score(es, im.by_forms, "fine") == (1, 2)
    c = im.confusion(es, im.by_sic)
    assert c[("investment manager", im.UNKNOWN)] == 1
