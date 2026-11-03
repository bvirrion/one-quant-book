"""Drill sheets: parse each printed sheet and key, and recompute every answer without using the generator's answers."""
import math
import pathlib
import re
import sys
from fractions import Fraction as F

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[4]
GEN = ROOT / "parts" / "interviews-1" / "generated"
CHAPTER = ROOT / "parts" / "interviews-1" / "03-speed-drills.tex"
ANSWERS = ROOT / "parts" / "interviews-1" / "solutions" / "03-speed-drills.tex"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import gen_drill  # noqa: E402

NONNUMERIC = {}

NUM = r"\\frac\{(\d+)\}\{(\d+)\}|(\d+(?:\.\d+)?)"
# Sheet: (items, minutes, points for a right answer, points for a wrong one).
RULES = {
    1: (80, 8, 1, 2), 2: (50, 6, 1, 1), 3: (36, 6, 2, 1), 4: (54, 6, 1, 1), 5: (90, 7, 1, 0), 6: (36, 5, 3, 1),
    7: (30, 5, 1, 1), 8: (40, 5, 2, 1), 9: (45, 5, 2, 3), 10: (40, 6, 1, 1), 11: (24, 6, 1, 3), 12: (80, 8, 1, 2),
}


def number(token):
    m = re.fullmatch(NUM, token.strip())
    assert m, token
    return F(int(m.group(1)), int(m.group(2))) if m.group(1) else F(m.group(3))


def exact_root(n, k):
    r = round(n ** (1 / k))
    assert r**k == n, (n, k)
    return F(r)


def exact_log(base, n):
    k = 0
    while base**k < n:
        k += 1
    assert base**k == n, (base, n)
    return F(k)


HALF = r"\\left\(\\frac\{1\}\{2\}\\right\)"


def evaluate(expr):
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\\% \\text\{ of \} (\d+)", expr)
    if m:
        return F(m.group(1)) * int(m.group(2)) / 100
    m = re.fullmatch(r"(\d+)\^(?:\{(\d+)\}|(\d))", expr)
    if m:
        return F(int(m.group(1)) ** int(m.group(2) or m.group(3)))
    m = re.fullmatch(r"\\sqrt\{(\d+)\}", expr)
    if m:
        return exact_root(int(m.group(1)), 2)
    m = re.fullmatch(r"\\sqrt\[3\]\{(\d+)\}", expr)
    if m:
        return exact_root(int(m.group(1)), 3)
    m = re.fullmatch(r"\\log_\{(\d+)\} (\d+)", expr)
    if m:
        return exact_log(int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"(\d+)!", expr)
    if m:
        return F(math.factorial(int(m.group(1))))
    m = re.fullmatch(r"\\frac\{(\d+)!\}\{(\d+)!\}", expr)
    if m:
        return F(math.factorial(int(m.group(1))), math.factorial(int(m.group(2))))
    m = re.fullmatch(r"\\binom\{(\d+)\}\{(\d+)\}(?: / 2\^\{(\d+)\})?", expr)
    if m:
        return F(math.comb(int(m.group(1)), int(m.group(2))), 2 ** int(m.group(3) or 0))
    m = re.fullmatch(rf"(1 - )?{HALF}\^\{{(\d+)\}}", expr)
    if m:
        v = F(1, 2 ** int(m.group(2)))
        return 1 - v if m.group(1) else v
    m = re.fullmatch(r"\\frac\{(\d+)\}\{(\d+)\} \\text\{ as \\%\}", expr)
    if m:
        return F(100 * int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"(\d+\.\d+) \\text\{ as a fraction\}", expr)
    if m:
        return F(m.group(1))
    m = re.fullmatch(r"(\d+) ([+-]) (\d+(?:\.\d+)?)\\%", expr)
    if m:
        change = F(m.group(3)) / 100
        return int(m.group(1)) * (1 + change if m.group(2) == "+" else 1 - change)
    m = re.fullmatch(r"(\d+) \\text\{ as \\% of \} (\d+)", expr)
    if m:
        return F(100 * int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"(\d\.\d) \\times (\d+) - (\d\.\d) \\times (\d+)", expr)
    if m:
        return F(m.group(1)) * int(m.group(2)) - F(m.group(3)) * int(m.group(4))
    if expr.endswith(",\\ x"):
        return solve(expr)
    parts = re.fullmatch(rf"({NUM}) (\+|-|\\times|\\div) ({NUM})", expr)
    assert parts, expr
    a, op, b = number(parts.group(1)), parts.group(5), number(parts.group(6))
    return {"+": a + b, "-": a - b, "\\times": a * b, "\\div": a / b}[op]


def side(tex, x):
    """Evaluate one side of a printed equation at x."""
    s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"((\1)/(\2))", tex)
    s = re.sub(r"(\d)x", r"\1*x", s)
    s = re.sub(r"(\d)\(", r"\1*(", s).replace("^", "**")
    s = re.sub(r"\d+(?:\.\d+)?", lambda m: f'F("{m.group(0)}")', s)
    return eval(s, {"F": F, "x": x})  # noqa: S307


def solve(expr):
    """The one positive whole x that satisfies a printed equation, found by trying every value."""
    left, right = expr[: -len(",\\ x")].split(" = ")
    found = [x for x in range(1, 500) if side(left, F(x)) == side(right, F(x))]
    assert len(found) == 1, (expr, found)
    return F(found[0])


def estimate(expr):
    """The true value of an estimation item, as a float."""
    m = re.fullmatch(r"([\d.]+) \\times ([\d.]+)", expr)
    if m:
        return float(m.group(1)) * float(m.group(2))
    m = re.fullmatch(r"(\d+) \\div (\d+)", expr)
    if m:
        return int(m.group(1)) / int(m.group(2))
    m = re.fullmatch(r"\\sqrt\{(\d+)\}", expr)
    if m:
        return math.sqrt(int(m.group(1)))
    m = re.fullmatch(r"([\d.]+)\^\{(\d+)\}", expr)
    if m:
        return float(m.group(1)) ** int(m.group(2))
    m = re.fullmatch(r"e\^\{([\d.]+)\}", expr)
    if m:
        return math.exp(float(m.group(1)))
    m = re.fullmatch(r"\\ln (\d+)", expr)
    if m:
        return math.log(int(m.group(1)))
    m = re.fullmatch(r"(\d+)\\% \\text\{ of \} (\d+)", expr)
    assert m, expr
    return int(m.group(1)) * int(m.group(2)) / 100


def read(name, macro):
    text = (GEN / name).read_text(encoding="utf-8")
    return {int(n): body for n, body in re.findall(rf"\\{macro}\{{(\d+)\}}\{{\$(.*?)\$\}}", text)}


def read_options(name):
    text = (GEN / name).read_text(encoding="utf-8")
    out = {}
    for n, options in re.findall(r"\\ivdrill\{(\d+)\}\{\$.*?\$\}\\ivoptions((?:\{[^{}]*\}){4})", text):
        out[int(n)] = re.findall(r"\{([^{}]*)\}", options)
    return out


def check_common(sheet):
    """The same checks on every sheet: numbering, families, the printed rules, the pace and the skip threshold."""
    count, minutes, right, wrong = RULES[sheet]
    items, key = read(f"drill-sheet-{sheet}-items.tex", "ivdrill"), read(f"drill-sheet-{sheet}-key.tex", "ivkey")
    assert sorted(items) == sorted(key) == list(range(1, count + 1))
    families = (GEN / f"drill-sheet-{sheet}-families.tex").read_text(encoding="utf-8")
    listed = [int(x) for row in re.findall(r"\\ivfamily\{[^}]*\}\{([\d, ]+)\}", families) for x in row.split(",")]
    assert sorted(listed) == list(range(1, count + 1))
    # The stem prints the same rules that the test holds.
    stem = CHAPTER.read_text(encoding="utf-8")
    assert f"\\textbf{{Sheet {sheet}.}} You have {minutes} minutes for these {count} items" in stem
    rule = f"You score $+{right}$ for a right answer, $-{wrong}$ for a wrong one and 0 for a blank"
    if wrong == 0:
        rule = f"You score $+{right}$ for a right answer and 0 for a wrong one or a blank"
    assert rule in stem.split(f"\\textbf{{Sheet {sheet}.}}")[1]
    # A guess that is right with probability p is worth zero at p = wrong / (right + wrong).
    p = F(wrong, right + wrong)
    assert p * right - (1 - p) * wrong == 0
    assert len(set(items.values())) == count
    # The same sum never appears twice in another form: a x b as b x a, or a x a as a squared.
    same = [re.sub(r"(\d+) \\times \1\b", r"\1^2", v) for v in items.values()]
    same = ["*".join(sorted(v.split(" \\times "))) for v in same]
    assert len(set(same)) == count
    return items, key, p


def check_free(sheet):
    items, key, p = check_common(sheet)
    for n, expr in items.items():
        assert number(key[n]) == evaluate(expr), (n, expr, key[n])
        assert number(key[n]) > 0
        # An item in decimals is keyed in decimals: the stems ask for a decimal in full.
        if "." in expr and "as a fraction" not in expr and "\\frac" not in expr:
            assert "\\frac" not in key[n], (sheet, n, expr, key[n])
    # A fraction answer is printed in lowest terms.
    for n, shown in key.items():
        m = re.fullmatch(r"\\frac\{(\d+)\}\{(\d+)\}", shown)
        if m:
            assert F(int(m.group(1)), int(m.group(2))).numerator == int(m.group(1)), n
    return p


def test_q1():
    assert check_free(1) == F(2, 3)
    # Six seconds an item, and the guessing threshold printed in the answer.
    assert 8 * 60 / 80 == 6
    # The printed comparison of careful and careless sheets.
    assert 60 - 2 * 0 == 60 and 75 - 2 * 8 == 59
    # Printed shortcut example.
    assert 400 * 7 - 11 * 7 == 389 * 7 == 2723


def test_q2():
    assert check_free(2) == F(1, 2)
    # 7.2 seconds an item.
    assert F(6 * 60, 50) == F(36, 5)
    # The printed comparison: 30 right and 2 wrong against 40 right and 12 wrong.
    assert 30 - 2 == 28 and 40 - 12 == 28
    # Printed shortcut examples.
    assert 8142 - 3700 + 22 == 8142 - 3678 == 4464
    assert 37 * 40 + 37 * 6 == 1480 + 222 == 37 * 46 == 1702
    assert 50 * 46 + 4 == 48**2 == 2304
    assert 6 * 7 == 42 and 65**2 == 4225
    assert 103 * 97 == 100**2 - 3**2 == 9991
    assert 998 * 6 == 6000 - 12
    assert F(24, 100) * 350 == 84 == F(350, 100) * 24
    assert F(1, 8) == F(125, 1000) and F(1, 16) == F(625, 10000)


def check_choice(sheet):
    items, key, p = check_common(sheet)
    options = read_options(f"drill-sheet-{sheet}-items.tex")
    assert sorted(options) == sorted(items)
    size_slips = 0
    for n, expr in items.items():
        right = evaluate(expr)
        values = [number(o) for o in options[n]]
        assert len(set(values)) == 4
        assert values.count(right) == 1, (n, expr, values)
        m = re.fullmatch(r"\\mathrm\{([A-D])\}\\;(\S+)", key[n])
        assert m, key[n]
        assert values["ABCD".index(m.group(1))] == right and number(m.group(2)) == right, n
        # Every option is printed to a common last place, and the wrong options are of the three printed kinds.
        unit = F(1, 10 ** gen_drill.places(right))
        wrong = [int(v / unit) for v in values if v != right]
        a = int(right / unit)
        assert all((v * 10 ** gen_drill.places(right)).denominator == 1 for v in values)
        kinds = {"slip": 0, "near": 0, "far": 0}
        for w in wrong:
            if abs(w - a) <= 4 and w % 10 != a % 10:
                kinds["near"] += 1
            elif abs(w - a) <= 90 and w % 10 == a % 10:
                kinds["slip"] += 1
            else:
                kinds["far"] += 1
        assert kinds["near"] >= 1 and kinds["slip"] >= 1, (n, expr, values)
        size_slips += kinds["far"]
    assert size_slips >= 0.8 * len(items)
    return p


def test_q3():
    assert check_choice(3) == F(1, 3)
    # Ten seconds an item.
    assert 6 * 60 / 36 == 10
    # Blind guessing over 4, 3 and 2 options, at +2 and -1.
    guess = {k: F(1, k) * 2 - (1 - F(1, k)) for k in (4, 3, 2)}
    assert guess == {4: -F(1, 4), 3: F(0), 2: F(1, 2)}
    # The printed comparison: 20 right and 16 blank against 24 right and 12 wrong.
    assert 20 * 2 == 40 and 24 * 2 - 12 == 36
    # Printed shortcut examples.
    assert (8 * 6) % 10 == (378 * 46) % 10 == 8
    assert 400 * 45 == 18000 and abs(378 * 46 - 18000) < 1000
    assert 70 * 64 == 4480 and 67**2 % 10 == 9 and 67**2 == 70 * 64 + 9
    assert 104 * 96 == 10000 - 16
    assert F(17, 100) * 640 == F(64) + 32 + F(128, 10)
    assert F(34, 10) * F(17, 10) == F(578, 100) and 4 * 7 % 10 == 8


def test_q4():
    assert check_free(4) == F(1, 2)
    assert 6 * 60 / 54 < 7
    # Printed shortcuts and the follow-up.
    assert F(7, 25) == F(28, 100) and F(375, 1000) == F(3, 8) and F(36, 120) == F(3, 10)
    assert [100 * F(k, 8) for k in (1, 3, 5, 7)] == [F(25, 2), F(75, 2), F(125, 2), F(175, 2)]
    assert F(3, 16) * 100 == F(75, 4)


def test_q5():
    assert check_free(5) == 0
    assert 7 * 60 / 90 < 5
    assert 90 - 12 == 78
    assert 17 * 8 == 80 + 56 and 476 / 7 == 420 / 7 + 56 / 7
    # 70 right and none wrong against 78 right and 12 wrong, under every sheet's scoring.
    for right, wrong in ((r, w) for _, _, r, w in RULES.values()):
        assert (78 * right - 12 * wrong < 70 * right) == (wrong >= right)
    assert 78 - 2 * 12 == 54


def test_q6():
    assert check_choice(6) == F(1, 4)
    assert round(5 * 60 / 36) == 8
    guess = {k: F(3, k) - (1 - F(1, k)) for k in (4, 3, 2)}
    assert guess == {4: F(0), 3: F(1, 3), 2: F(1)}
    assert 36 * guess[3] == 12


def test_q7():
    items, key, p = check_common(7)
    assert p == F(1, 2)
    for n, expr in items.items():
        true = estimate(expr)
        shown = float(number(key[n]))
        # The key is the true value to three significant figures.
        assert shown == float(f"{true:.3g}"), (n, expr, shown)
    assert 5 * 60 / 30 == 10
    # The printed comparison.
    assert round(38.7 * 41.2, 2) == 1594.44
    assert round(100 * (1600 / 1594.44 - 1), 2) == 0.35
    assert round(100 * (40 * 45 / (38.7 * 42.6) - 1)) == 9
    # Printed shortcuts.
    assert abs(math.sqrt(5300) - (70 + 400 / 140)) < 0.1
    assert 1.05**10 < math.exp(0.5)


def test_q8():
    assert check_free(8) == F(1, 3)
    assert number("7") == 7
    items = read("drill-sheet-8-items.tex", "ivdrill")
    key = read("drill-sheet-8-key.tex", "ivkey")
    assert all(number(key[n]).denominator == 1 for n in items)
    assert 5 * 60 / 40 == 7.5
    assert 7 * 6 - 9 == 3 * 6 + 15 == 33
    assert 5 * (9 - 2) == 35 and F(12) / F(3, 2) == 8
    # Every answer is whole, so a fraction has no chance of being right: writing it costs 1 for certain.
    assert 3 * F(0) - 1 == -1


def test_q9():
    assert check_free(9) == F(3, 5)
    key = read("drill-sheet-9-key.tex", "ivkey")
    assert all(number(v).denominator == 1 for v in key.values())
    assert 5 * 60 / 45 < 7
    assert 8 * 1024 == 2**13 == 8192 and 49**2 == 7**4 and 11**3 == 1331 and 10**3 / 2**3 == 5**3
    assert math.factorial(9) == 362880 and math.factorial(10) / math.factorial(8) == 90 and 2**12 == 4096
    assert 2**16 == 65536
    # The sheet needs cubes up to 15, as both the family line and the follow-up say.
    items = read("drill-sheet-9-items.tex", "ivdrill")
    roots = [exact_root(int(m.group(1)), 3) for v in items.values() if (m := re.fullmatch(r"\\sqrt\[3\]\{(\d+)\}", v))]
    cubes = [F(int(m.group(1))) for v in items.values() if (m := re.fullmatch(r"(\d+)\^3", v))]
    assert max(roots + cubes) > 12 and max(roots + cubes) <= 15
    text = ANSWERS.read_text(encoding="utf-8")
    assert "the cubes up to 15" in text and "the cubes up to 12" not in text


def test_q10():
    assert check_free(10) == F(1, 2)
    assert 6 * 60 / 40 == 9
    assert 12 * 11 * 10 == 1320 and 1320 / 6 == 220 == 2 * 11 * 10 == math.comb(12, 3)
    assert math.factorial(7) / math.factorial(5) == 7 * 6
    assert F(5, 9) * F(4, 8) == F(5, 9) * F(1, 2)
    assert math.comb(9, 2) == 36 and F(36 * 10, 3) == 120 == math.comb(10, 3)


def test_q11():
    assert check_free(11) == F(3, 4)
    assert 6 * 60 / 24 == 15
    assert 20 - 3 * 4 == 8
    assert 104 * 297 == 104 * 300 - 104 * 3
    assert 378 * 46 == 17388 and sum(map(int, "17388")) == 27
    assert sum(map(int, "378")) % 9 == 0 and sum(map(int, "46")) % 9 == 1
    for k, d in ((1, 3), (9, -4)):
        assert (100 * k + d) ** 2 == 10000 * k * k + 200 * k * d + d * d


def test_q12():
    assert check_free(12) == F(2, 3)
    assert RULES[12] == RULES[1]
    assert 8 * 60 / 80 == 6
    assert 50 == 50 - 2 * 0 and 65 - 2 * 10 == 45


@pytest.mark.parametrize("sheet", list(RULES))
def test_generated_files_match_the_generator(sheet, tmp_path, monkeypatch):
    monkeypatch.setattr(gen_drill, "OUT", tmp_path)
    gen_drill.write(sheet, gen_drill.SEEDS[sheet])
    written = list(tmp_path.iterdir())
    assert len(written) == 3
    for path in written:
        assert path.read_text(encoding="utf-8") == (GEN / path.name).read_text(encoding="utf-8")


def test_answers_input_every_sheet():
    answers = ANSWERS.read_text(encoding="utf-8")
    for sheet in RULES:
        assert f"generated/drill-sheet-{sheet}-key" in answers
        assert f"generated/drill-sheet-{sheet}-families" in answers
