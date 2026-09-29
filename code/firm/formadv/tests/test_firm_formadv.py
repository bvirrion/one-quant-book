import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_formadv as fa  # noqa: E402

HEAD = ",".join(f'"{c}"' for c in fa.COLS.values())
CSV = HEAD + "\n" + "\n".join([
    '"1","A","100","40","1,000,000,000","Y","3","900,000,000","01/02/2026"',
    '"2","B","10","5","100,000,000","N","","","01/02/2026"',
    '"3","C","20","","300,000,000","Y","1","300,000,000","01/02/2026"'])


def test_read_filters_hedge_advisers():
    a = fa.read(io.StringIO(CSV))
    assert [x.name for x in a] == ["A", "C"] and a[0].raum == 1e9 and a[1].advisory is None
    assert len(fa.read(io.StringIO(CSV), hedge_only=False)) == 3


def test_per_head_and_quantiles():
    a = fa.read(io.StringIO(CSV))
    p = fa.per_head(a[0])
    assert p["raum_per_employee"] == 1e7 and p["raum_per_advisory"] == 2.5e7 and p["advisory_share"] == 0.4
    assert fa.per_head(a[1])["advisory_share"] is None
    assert fa.quantiles([1, 2, 3, None], (0.5,)) == [2.0]


def test_concentration():
    top, h = fa.concentration([50, 30, 20, None], k=1)
    assert abs(top - 0.5) < 1e-12 and abs(h - (2500 + 900 + 400)) < 1e-9


def test_old_file_without_hedge_columns():
    old = '"Organization CRD#","Primary Business Name","5A","5B(1)","5F(2)(c)","Latest ADV Filing Date"\n"9","Z","5","2","50","x"'
    import pytest
    with pytest.raises(ValueError):
        fa.read(io.StringIO(old))
    (a,) = fa.read(io.StringIO(old), hedge_only=False)
    assert a.employees == 5 and a.pf_gav is None and a.n_hedge is None
