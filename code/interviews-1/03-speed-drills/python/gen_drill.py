"""Generate a speed-arithmetic drill sheet and its key as LaTeX. Run: python gen_drill.py [sheet] [seed].

Every item comes from one family with a known shortcut, so the key can tell the reader which family they miss.
The chapter's test parses the printed LaTeX and recomputes every answer independently of this file.

Sheet 1 is 80 easy items, free answers. Sheet 2 is 50 harder items, free answers. Sheet 3 is 36 items that are too long
to work out in full, with four options each, where the point is to throw options away. Sheet 4 moves between fractions,
decimals and percentages. Sheet 5 is 90 plain items with no penalty, a test of pace. Sheet 6 is 36 harder items with
options. Sheet 7 is estimation, marked to within 5%. Sheet 8 is one-line algebra. Sheet 9 is powers, roots and logs.
Sheet 10 is the arithmetic of chance. Sheet 11 is 24 long items with a heavy penalty. Sheet 12 mixes everything.
"""
import math
import pathlib
import random
import sys
from fractions import Fraction as F

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = ROOT / "parts" / "interviews-1" / "generated"

SHORTCUTS = {
    "Adding and subtracting whole numbers": "Work from the left, hundreds first, and keep a running total.",
    "Adding and subtracting decimals": "Line up the decimal point in your head, or scale up by 100 and scale back.",
    "Times one digit": "Split the larger number, or round up and subtract when that is shorter: "
    "$389 \\times 7 = 400 \\times 7 - 11 \\times 7 = 2723$.",
    "Numbers with a shortcut": "$\\times 25$: times 100, then divide by 4. $\\times 15$: add half and times 10. "
    "$\\times 11$: times 10 and add itself. $\\times 99$: times 100 and subtract itself. "
    "$(n - d)(n + d) = n^2 - d^2$.",
    "Exact division": "$\\div 5$: double and divide by 10. $\\div 25$: times 4 and divide by 100. "
    "$\\div 12$ and $\\div 15$: divide by 3 first.",
    "Fractions": "Use the smallest common denominator, multiply across, cancel before you multiply. "
    "Answers are in lowest terms.",
    "Percentages": "Start from 10\\% and build up: $15\\%$ is $10\\% + 5\\%$, and $12.5\\%$ is one eighth. "
    "$p\\%$ of $n$ equals $n\\%$ of $p$.",
    "Decimal products": "Multiply the digits and count the places. Treat $0.25$, $0.75$, $1.5$ and $2.5$ as "
    "fractions: $\\tfrac14$, $\\tfrac34$, $\\tfrac32$, $\\tfrac52$.",
}

SHORTCUTS_2 = {
    "Adding and subtracting large numbers": "Round one number and correct: "
    "$8142 - 3678 = 8142 - 3700 + 22 = 4464$.",
    "Two digits times two digits": "Split one factor, as in "
    "$37 \\times 46 = 37 \\times 40 + 37 \\times 6 = 1480 + 222 = 1702$. "
    "If the factors are close, use the difference of squares instead.",
    "Squares": "$n^2 = (n - d)(n + d) + d^2$, with $d$ chosen to make one factor round: "
    "$48^2 = 50 \\times 46 + 4 = 2304$. A number ending in 5: $65^2$ is $6 \\times 7$ followed by 25.",
    "Near a round number": "$103 \\times 97 = 100^2 - 3^2$, and $998 \\times 6 = 6000 - 12$.",
    "Percentages of any number": "Take 1\\% or 10\\% and build up, or swap the two: "
    "$24\\%$ of 350 equals $350\\%$ of 24, which is 84.",
    "Fractions": "Use the smallest common denominator. To divide, multiply by the upside-down fraction, "
    "and cancel first.",
    "Decimal answers": "Know the eighths and sixteenths: "
    "$\\tfrac18 = 0.125$ and $\\tfrac1{16} = 0.0625$. "
    "To divide by 40, divide by 4 and then by 10.",
}

SHORTCUTS_3 = {
    "Three digits times two digits": "Do not finish the sum. Check the last digit, then the size, "
    "then the sum of the digits. "
    "For $378 \\times 46$, the last digit is that of $8 \\times 6$, and the size is near $400 \\times 45$.",
    "Squares and near-squares": "$67^2$ ends in 9, and is near $70 \\times 64$. "
    "$104 \\times 96$ is $10000 - 16$.",
    "Exact division": "Multiply back in your head: the quotient times the divisor must end in the right digit. "
    "Its size comes from rounding the divisor.",
    "Percentages": "$17\\%$ of 640 is $10\\% + 5\\% + 2\\%$, that is $64 + 32 + 12.8$.",
    "Decimal products": "Count the decimal places first. The options then differ only in digits you can test: "
    "$3.4 \\times 1.7$ has two places and ends in 8.",
    "Fractions of a number": "Divide by the bottom first, then multiply by the top. "
    "For $\\tfrac78$, take one eighth away.",
}


SHORTCUTS_4 = {
    "Fractions as percentages": "Know the eighths and the sixteenths. For a denominator of 20, 25 or 50, scale it "
    "up to 100: "
    "$\\tfrac{7}{25} = \\tfrac{28}{100}$. For 40, take half of the value over 20.",
    "Decimals as fractions": "Read the decimal over a power of 10, then cancel: "
    "$0.375$ is $\\tfrac{375}{1000}$, "
    "which is $\\tfrac38$. Most of them are "
    "multiples of $\\tfrac18$, $\\tfrac1{20}$, $\\tfrac1{25}$ or $\\tfrac1{40}$.",
    "Percentage change": "Add or subtract the percentage of the base, or multiply at once: "
    "$15\\%$ up is $\\times 1.15$, and $20\\%$ down is $\\times 0.8$.",
    "As a percentage of": "Cancel first, then scale to 100: $36$ of $120$ is $\\tfrac{3}{10}$, or $30\\%$.",
    "Percentages of any number": "Take 1\\% or 10\\% and build up, or swap the two: "
    "$p\\%$ of $n$ equals $n\\%$ of $p$.",
    "Fractions": "Use the smallest common denominator. To divide, multiply by the upside-down fraction, "
    "and cancel first.",
}

SHORTCUTS_5 = {
    "Adding and subtracting": "Work from the left, and do not write the carries.",
    "Times tables to 19": "Split the teens: $17 \\times 8 = 80 + 56$.",
    "Times one digit": "Split the larger number, hundreds first.",
    "Doubling and halving": "Go digit by digit from the left. These should take no thought at all.",
    "Exact division": "Think of the times table backwards, and split a long number into easy parts: "
    "$476 \\div 7 = 420 \\div 7 + 56 \\div 7$.",
    "Easy percentages": "$10\\%$ moves the point, $20\\%$ doubles that, $25\\%$ is a quarter and $50\\%$ is a half.",
}

SHORTCUTS_6 = {
    "Three digits times two digits": "Test the last digit first, then the size.",
    "Squares and near-squares": "Check the last digit, then round. $(100 + d)(100 - d)$ is $10000 - d^2$.",
    "Long division": "Multiply back: the quotient's last digit times the divisor's last digit must give the "
    "last digit of the number.",
    "Percentages": "Build the percentage from 10\\%, 5\\% and 1\\%, and stop as soon as only one option is left.",
    "Decimal products": "Count the places, then test the last digit of the product.",
    "Fractions of a number": "Divide by the bottom first, then multiply by the top.",
}

SHORTCUTS_7 = {
    "Products": "Round one factor up and the other down, by about the same percentage: "
    "$38.7 \\times 41.2$ is close to $40 \\times 40$.",
    "Quotients": "Round the divisor to an easy number, then correct by the percentage you moved it.",
    "Square roots": "Write the number as a square times a small factor, and move the root by half of the "
    "percentage gap: $\\sqrt{5300}$ is about $70 + \\tfrac{400}{140}$.",
    "Compounding": "Take $1.05^{10} \\approx e^{0.5}$, and subtract a little, because the log of $1 + r$ is below $r$.",
    "Exponentials and logarithms": "Use $e^x \\approx 1 + x + \\tfrac{x^2}{2}$ for a small $x$. "
    "Build each logarithm from $\\ln 2$ and $\\ln 10$.",
    "Percentages": "Round the number, not the percentage, then move by the same small factor.",
}

SHORTCUTS_8 = {
    "Two steps": "Undo the addition, then the multiplication, in your head.",
    "Brackets": "Divide by the factor first, if it goes in, and leave the bracket alone.",
    "Both sides": "Gather the $x$ terms on one side, and the numbers on the other.",
    "With a fraction": "Clear the fraction by multiplying, or read $\\tfrac{12}{x} = 1.5$ as $x = \\tfrac{12}{1.5}$.",
    "Powers": "Know the squares up to 25 and the powers of 2 and 3.",
}

SHORTCUTS_9 = {
    "Powers of two": "$2^{10} = 1024$. From there, double or halve, or read $2^{13}$ as $8 \\times 1024$.",
    "Other powers": "Square, and multiply once more if you need to: $7^4 = 49^2$. "
    "$11^3 = 1331$ and $5^n$ is $10^n$ divided by $2^n$.",
    "Squares up to 29": "Use $n^2 = (n - d)(n + d) + d^2$, or simply know them.",
    "Square roots": "The size gives the tens digit, and the last digit leaves at most two choices for the units. "
    "Compare with the square of the number ending in 5.",
    "Cube roots": "Know the cubes up to 15. The last digit of a cube fixes the last digit of its root.",
    "Logarithms": "Rewrite the number as a power of the base: $\\log_2 4096$ is the power of two that makes 4096.",
    "Factorials": "Know them up to $9! = 362\\,880$. A ratio such as $\\tfrac{10!}{8!}$ is simply $10 \\times 9$.",
}

SHORTCUTS_10 = {
    "Binomial coefficients": "Cancel before you multiply: "
    "$\\binom{12}{3} = \\tfrac{12 \\cdot 11 \\cdot 10}{6} = 2 \\cdot 11 \\cdot 10$.",
    "Ratios of factorials": "Write only the factors that are left: $\\tfrac{7!}{5!} = 7 \\times 6$.",
    "Powers of a half": "$2^{-5} = \\tfrac{1}{32}$. The complement of $2^{-k}$ is $\\tfrac{2^k - 1}{2^k}$.",
    "Binomial chances": "Cancel the powers of two from the coefficient first, and give the result in lowest terms.",
    "Drawing in a row": "Cancel across before you multiply: "
    "$\\tfrac59 \\times \\tfrac48 = \\tfrac59 \\times \\tfrac12$.",
    "Expected values": "Multiply each chance by its amount, and keep the decimal point in place by treating "
    "$0.3$ as 3 tenths.",
}

SHORTCUTS_11 = {
    "Three digits times two digits": "Split the two-digit factor, and add carefully. Then check the last digit.",
    "Near the hundreds": "$104 \\times 297 = 104 \\times 300 - 104 \\times 3$.",
    "Squares near the hundreds": "$(100k + d)^2 = 10000k^2 + 200kd + d^2$, with $d$ small and perhaps negative.",
    "Long division": "Take off round multiples of the divisor, and keep a tally of the quotient.",
    "Decimal products": "Count the places, multiply as whole numbers, and check the size against a rounded sum.",
}

SHORTCUTS_12 = {
    "Adding and subtracting large numbers": "Round one number and correct.",
    "Two digits times two digits": "Split one factor, or use the difference of squares if the factors are close.",
    "Squares": "$n^2 = (n - d)(n + d) + d^2$.",
    "Near a round number": "$(100 + d)(100 - d) = 10000 - d^2$.",
    "Percentages": "Build from $10\\%$ and $1\\%$. For a change, multiply by $1 + r$.",
    "Fractions and decimals": "Know the eighths, sixteenths and fortieths. Cancel before you multiply.",
    "Conversions": "Scale a fraction to 100 for a percentage. Read a decimal over a power of 10 for a fraction.",
    "Powers and roots": "Know the powers of 2 up to $2^{16}$ and the squares up to 29.",
    "Binomial coefficients": "Cancel before you multiply.",
    "Algebra": "Undo each step in your head.",
}


def dec(x):
    """Print an exact finite decimal with the fewest places."""
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    places = 0
    while (x * 10**places).denominator != 1:
        places += 1
    return f"{float(x):.{places}f}"


def frac(x):
    return f"\\frac{{{x.numerator}}}{{{x.denominator}}}"


def whole(rng, n):
    for i in range(n):
        if i % 2:
            a, b = rng.randint(1102, 4890), rng.randint(123, 987)
            yield f"{a} - {b}", F(a - b)
        else:
            a, b = rng.randint(123, 987), rng.randint(123, 987)
            yield f"{a} + {b}", F(a + b)


def decimals(rng, n):
    for i in range(n):
        a, b = F(rng.randint(15, 195), 10), F(rng.randint(105, 995), 100)
        if i % 2 and a > b:
            yield f"{dec(a)} - {dec(b)}", a - b
        elif i % 2:
            yield f"{dec(b)} - {dec(a)}", b - a
        else:
            yield f"{dec(a)} + {dec(b)}", a + b


def one_digit(rng, n):
    for _ in range(n):
        a, b = rng.randint(23, 389), rng.randint(3, 9)
        yield f"{a} \\times {b}", F(a * b)


def shortcut(rng):
    for _ in range(3):
        a = rng.randint(12, 88)
        yield f"{a} \\times 25", F(a * 25)
    for _ in range(3):
        a = 2 * rng.randint(7, 44)
        yield f"{a} \\times 15", F(a * 15)
    for _ in range(2):
        a = rng.randint(23, 89)
        yield f"{a} \\times 11", F(a * 11)
    for _ in range(2):
        a = rng.randint(12, 49)
        yield f"{a} \\times 99", F(a * 99)
    for _ in range(2):
        m, d = 10 * rng.randint(2, 8), rng.randint(1, 4)
        yield f"{m - d} \\times {m + d}", F((m - d) * (m + d))


def division(rng):
    for _ in range(2):
        a = 5 * rng.randint(23, 197)
        yield f"{a} \\div 5", F(a, 5)
    for _ in range(2):
        a = 25 * rng.randint(7, 39)
        yield f"{a} \\div 25", F(a, 25)
    for _ in range(3):
        q = rng.randint(11, 45)
        yield f"{12 * q} \\div 12", F(q)
    for _ in range(3):
        q = rng.randint(12, 40)
        yield f"{15 * q} \\div 15", F(q)


def fractions(rng):
    pool = [F(a, b) for b in (2, 3, 4, 5, 6, 8, 10, 12) for a in range(1, b) if math.gcd(a, b) == 1]

    def pair():
        while True:
            x, y = rng.choice(pool), rng.choice(pool)
            if x != y and math.lcm(x.denominator, y.denominator) <= 24:
                return x, y

    for _ in range(5):
        x, y = pair()
        yield f"{frac(x)} + {frac(y)}", x + y
    for _ in range(2):
        x, y = pair()
        x, y = max(x, y), min(x, y)
        yield f"{frac(x)} - {frac(y)}", x - y
    for _ in range(3):
        x, y = pair()
        yield f"{frac(x)} \\times {frac(y)}", x * y


def percentages(rng, n):
    for _ in range(n):
        p, k = rng.choice((F(5), F(15), F(25, 2), F(20), F(30), F(40), F(75), F(35))), rng.randint(2, 24)
        m = 40 * k
        yield f"{dec(p)}\\% \\text{{ of }} {m}", p * m / 100


def products(rng):
    for _ in range(2):
        a, b = rng.randint(3, 9), rng.randint(2, 9)
        yield f"0.{a} \\times 0.{b}", F(a * b, 100)
    for c, k in ((F(3, 2), 2), (F(5, 2), 2), (F(1, 4), 4), (F(3, 4), 4)):
        a = k * rng.randint(6, 48)
        yield f"{dec(c)} \\times {a}", c * a


def build(seed):
    """Return 80 shuffled items (family, latex, answer), with no repeated expression."""
    rng = random.Random(seed)
    families = [
        ("Adding and subtracting whole numbers", whole(rng, 14)),
        ("Adding and subtracting decimals", decimals(rng, 8)),
        ("Times one digit", one_digit(rng, 10)),
        ("Numbers with a shortcut", shortcut(rng)),
        ("Exact division", division(rng)),
        ("Fractions", fractions(rng)),
        ("Percentages", percentages(rng, 10)),
        ("Decimal products", products(rng)),
    ]
    items = [(name, tex, ans) for name, gen in families for tex, ans in gen]
    if len({tex for _, tex, _ in items}) != len(items):
        raise ValueError("repeated item: choose another seed")
    rng.shuffle(items)
    return items


def big_sums(rng, n):
    for i in range(n):
        if i % 2:
            a, b = rng.randint(5012, 9876), rng.randint(1234, 4890)
            yield f"{a} - {b}", F(a - b)
        else:
            a, b = rng.randint(1234, 7890), rng.randint(1234, 7890)
            yield f"{a} + {b}", F(a + b)


def two_by_two(rng, n):
    for _ in range(n):
        a = rng.choice([x for x in range(23, 89) if x % 10])
        b = rng.choice([x for x in range(23, 89) if x % 10 and x != a])  # a x a would repeat a square on the sheet
        yield f"{a} \\times {b}", F(a * b)


def squares(rng, n):
    tail = [rng.choice((35, 45, 55)), rng.choice((65, 75, 85))]
    for a in rng.sample([x for x in range(31, 99) if x % 10], n - 2) + tail:
        yield f"{a}^2", F(a * a)


def near_round(rng):
    for _ in range(3):
        d = rng.randint(2, 9)
        yield f"{100 + d} \\times {100 - d}", F((100 + d) * (100 - d))
    for _ in range(2):
        d, k = rng.randint(2, 4), rng.randint(3, 9)
        yield f"{1000 - d} \\times {k}", F((1000 - d) * k)


def any_percent(rng, n):
    for _ in range(n):
        p = rng.choice((F(6), F(14), F(16), F(18), F(24), F(35, 2), F(45), F(55), F(65), F(85)))
        m = 10 * rng.choice([x for x in range(4, 48) if x != 10])
        if (p * m / 100).denominator in (1, 2, 4, 5, 10):
            yield f"{dec(p)}\\% \\text{{ of }} {m}", p * m / 100
        else:
            m = 40 * rng.randint(2, 12)
            yield f"{dec(p)}\\% \\text{{ of }} {m}", p * m / 100


def harder_fractions(rng):
    pool = [F(a, b) for b in (3, 4, 5, 6, 7, 8, 9, 12) for a in range(1, b) if math.gcd(a, b) == 1]

    def pair():
        while True:
            x, y = rng.choice(pool), rng.choice(pool)
            if x != y and math.lcm(x.denominator, y.denominator) <= 45:
                return x, y

    for _ in range(3):
        x, y = pair()
        yield f"{frac(x)} + {frac(y)}", x + y
    for _ in range(2):
        x, y = pair()
        x, y = max(x, y), min(x, y)
        yield f"{frac(x)} - {frac(y)}", x - y
    for _ in range(2):
        x, y = pair()
        yield f"{frac(x)} \\div {frac(y)}", x / y


def decimal_answers(rng):
    for a, b in rng.sample([(3, 8), (5, 8), (7, 8), (3, 16), (5, 16), (7, 16), (9, 16), (11, 16)], 4):
        yield f"{a} \\div {b}", F(a, b)
    a = rng.choice((7, 9, 11, 13, 17))
    yield f"{a} \\div 40", F(a, 40)
    a, b = rng.randint(11, 19), rng.randint(3, 9)
    yield f"{dec(F(a, 100))} \\times {dec(F(b, 10))}", F(a * b, 1000)
    a = rng.choice((14, 18, 22, 26, 34, 38))
    yield f"{dec(F(a, 10))} \\times 0.25", F(a, 40)


def build_2(seed):
    """Return 50 shuffled items (family, latex, answer), with no repeated expression."""
    rng = random.Random(seed)
    families = [
        ("Adding and subtracting large numbers", big_sums(rng, 8)),
        ("Two digits times two digits", two_by_two(rng, 10)),
        ("Squares", squares(rng, 6)),
        ("Near a round number", near_round(rng)),
        ("Percentages of any number", any_percent(rng, 7)),
        ("Fractions", harder_fractions(rng)),
        ("Decimal answers", decimal_answers(rng)),
    ]
    items = [(name, tex, ans) for name, gen in families for tex, ans in gen]
    if len({tex for _, tex, _ in items}) != len(items):
        raise ValueError("repeated item: choose another seed")
    rng.shuffle(items)
    return items


def three_by_two(rng, n):
    for _ in range(n):
        a, b = rng.randint(123, 987), rng.randint(23, 89)
        yield f"{a} \\times {b}", F(a * b)


def squares_mc(rng):
    for a in rng.sample([x for x in range(41, 99) if x % 10], 3):
        yield f"{a}^2", F(a * a)
    for _ in range(2):
        d = rng.randint(3, 9)
        yield f"{100 + d} \\times {100 - d}", F((100 + d) * (100 - d))


def long_division(rng, n):
    for _ in range(n):
        q, d = rng.randint(23, 97), rng.choice((13, 14, 16, 17, 18, 19, 21, 23, 24))
        yield f"{q * d} \\div {d}", F(q)


def percent_mc(rng, n):
    for _ in range(n):
        p, m = rng.choice((7, 13, 17, 19, 23, 27, 33, 37)), 10 * rng.randint(11, 89)
        yield f"{p}\\% \\text{{ of }} {m}", F(p * m, 100)


def decimal_mc(rng, n):
    for _ in range(n):
        a, b = rng.choice([x for x in range(12, 89) if x % 10]), rng.choice([x for x in range(12, 89) if x % 10])
        yield f"{dec(F(a, 10))} \\times {dec(F(b, 10))}", F(a * b, 100)


def fraction_of(rng):
    for x in rng.sample([F(3, 8), F(5, 8), F(7, 8), F(5, 6), F(7, 12), F(4, 9), F(5, 16), F(7, 16)], 5):
        m = x.denominator * rng.randint(11, 79)
        yield f"{frac(x)} \\times {m}", x * m


def places(x):
    n = 0
    while (x * 10**n).denominator != 1:
        n += 1
    return n


def options_for(rng, ans):
    """Three wrong options: right last digit and a slip in the tens, wrong last digit nearby, and 10-30% away."""
    unit = F(1, 10 ** places(ans))
    a = int(ans / unit)
    slip = a + rng.choice((-1, 1)) * 10 * rng.randint(1, 9)
    if slip <= 0:
        slip = a + 10 * rng.randint(1, 9)
    near = a + rng.choice((-1, 1)) * rng.randint(1, 4)
    while near % 10 == a % 10 or near <= 0:
        near = a + rng.randint(1, 4)
    far = a + rng.choice((-1, 1)) * round(a * rng.uniform(0.12, 0.3))
    while far in (a, slip, near) or far <= 0:
        far += 1
    if len({a, slip, near, far}) != 4:
        raise ValueError("repeated option: choose another seed")
    wrong = [slip * unit, near * unit, far * unit]
    opts = [ans, *wrong]
    rng.shuffle(opts)
    return opts


def build_3(seed):
    """Return 36 shuffled items (family, latex, answer, options), with no repeated expression."""
    rng = random.Random(seed)
    families = [
        ("Three digits times two digits", three_by_two(rng, 8)),
        ("Squares and near-squares", squares_mc(rng)),
        ("Exact division", long_division(rng, 6)),
        ("Percentages", percent_mc(rng, 6)),
        ("Decimal products", decimal_mc(rng, 6)),
        ("Fractions of a number", fraction_of(rng)),
    ]
    items = [(name, tex, ans, options_for(rng, ans)) for name, gen in families for tex, ans in gen]
    if len({it[1] for it in items}) != len(items):
        raise ValueError("repeated item: choose another seed")
    rng.shuffle(items)
    return items


def as_percent(rng, n):
    pool = [(a, b) for b in (8, 16, 20, 25, 40, 50) for a in range(1, b) if math.gcd(a, b) == 1]
    for a, b in rng.sample(pool, n):
        yield f"\\frac{{{a}}}{{{b}}} \\text{{ as \\%}}", F(100 * a, b)


def as_fraction(rng, n):
    pool = [F(a, b) for b in (8, 20, 25, 40, 50, 125) for a in range(1, b) if math.gcd(a, b) == 1]
    for x in rng.sample(pool, n):
        yield f"{dec(x)} \\text{{ as a fraction}}", x


def percent_change(rng, n):
    for i in range(n):
        p = rng.choice((F(5), F(10), F(25, 2), F(15), F(20), F(25), F(30), F(40)))
        m = 40 * rng.randint(2, 24)
        sign, f = ("+", 1 + p / 100) if i % 2 else ("-", 1 - p / 100)
        yield f"{m} {sign} {dec(p)}\\%", m * f


def share_of(rng, n):
    for _ in range(n):
        whole = rng.choice((40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 500, 600, 800))
        p = 5 * rng.randint(1, 18)
        yield f"{whole * p // 100} \\text{{ as \\% of }} {whole}", F(p)


def fraction_mix(rng, add, sub, mul, div):
    pool = [F(a, b) for b in (3, 4, 5, 6, 7, 8, 9, 12) for a in range(1, b) if math.gcd(a, b) == 1]

    def pair():
        while True:
            x, y = rng.choice(pool), rng.choice(pool)
            if x != y and math.lcm(x.denominator, y.denominator) <= 36:
                return x, y

    for _ in range(add):
        x, y = pair()
        yield f"{frac(x)} + {frac(y)}", x + y
    for _ in range(sub):
        x, y = pair()
        x, y = max(x, y), min(x, y)
        yield f"{frac(x)} - {frac(y)}", x - y
    for _ in range(mul):
        x, y = pair()
        yield f"{frac(x)} \\times {frac(y)}", x * y
    for _ in range(div):
        x, y = pair()
        yield f"{frac(x)} \\div {frac(y)}", x / y


def build_4(seed):
    rng = random.Random(seed)
    return assemble(rng, [
        ("Fractions as percentages", as_percent(rng, 10)),
        ("Decimals as fractions", as_fraction(rng, 8)),
        ("Percentage change", percent_change(rng, 10)),
        ("As a percentage of", share_of(rng, 8)),
        ("Percentages of any number", any_percent(rng, 8)),
        ("Fractions", fraction_mix(rng, 4, 2, 2, 2)),
    ])


def assemble(rng, families):
    """Shuffle the items of the given families, and refuse a repeated expression."""
    items = [(name, tex, ans) for name, gen in families for tex, ans in gen]
    if len({tex for _, tex, _ in items}) != len(items):
        raise ValueError("repeated item: choose another seed")
    rng.shuffle(items)
    return items


def easy_sums(rng, n):
    for i in range(n):
        if i % 2:
            a, b = rng.randint(120, 998), rng.randint(14, 119)
            yield f"{a} - {b}", F(a - b)
        else:
            a, b = rng.randint(120, 998), rng.randint(14, 119)
            yield f"{a} + {b}", F(a + b)


def tables(rng, n):
    for a, b in rng.sample([(a, b) for a in range(12, 20) for b in range(3, 10)], n):
        yield f"{a} \\times {b}", F(a * b)


def doubling(rng, n):
    for i in range(n):
        a = 2 * rng.randint(61, 499)
        yield (f"{a} \\div 2", F(a, 2)) if i % 2 else (f"{a} \\times 2", F(2 * a))


def small_division(rng, n):
    for _ in range(n):
        q, d = rng.randint(12, 99), rng.randint(3, 9)
        yield f"{q * d} \\div {d}", F(q)


def easy_percent(rng, n):
    for _ in range(n):
        p, m = rng.choice((10, 20, 25, 50)), 20 * rng.randint(2, 30)
        yield f"{p}\\% \\text{{ of }} {m}", F(p * m, 100)


def build_5(seed):
    rng = random.Random(seed)
    return assemble(rng, [
        ("Adding and subtracting", easy_sums(rng, 20)),
        ("Times tables to 19", tables(rng, 25)),
        ("Times one digit", one_digit(rng, 15)),
        ("Doubling and halving", doubling(rng, 10)),
        ("Exact division", small_division(rng, 10)),
        ("Easy percentages", easy_percent(rng, 10)),
    ])


def hard_division(rng, n):
    for _ in range(n):
        q, d = rng.randint(23, 97), rng.choice((27, 29, 31, 34, 37, 38, 41, 43, 47))
        yield f"{q * d} \\div {d}", F(q)


def build_6(seed):
    rng = random.Random(seed)
    families = [
        ("Three digits times two digits", three_by_two(rng, 7)),
        ("Squares and near-squares", squares_mc(rng)),
        ("Long division", hard_division(rng, 7)),
        ("Percentages", percent_mc(rng, 6)),
        ("Decimal products", decimal_mc(rng, 6)),
        ("Fractions of a number", fraction_of(rng)),
    ]
    items = [(name, tex, ans, options_for(rng, ans)) for name, gen in families for tex, ans in gen]
    if len({it[1] for it in items}) != len(items):
        raise ValueError("repeated item: choose another seed")
    rng.shuffle(items)
    return items


def sig3(x):
    """Round to three significant figures, as an exact value."""
    return F(str(float(f"{x:.3g}")))


def est_products(rng, n):
    for _ in range(n):
        a, b = F(rng.randint(112, 899), 10), F(rng.randint(112, 899), 10)
        yield f"{dec(a)} \\times {dec(b)}", sig3(float(a * b))


def est_quotients(rng, n):
    for _ in range(n):
        a, b = rng.randint(1203, 9876), rng.randint(113, 887)
        yield f"{a} \\div {b}", sig3(a / b)


def est_roots(rng, n):
    for a in rng.sample(range(310, 9700), n):
        yield f"\\sqrt{{{a}}}", sig3(math.sqrt(a))


def est_compound(rng, n):
    pool = [(r, k) for r in ("1.02", "1.03", "1.04", "1.05", "1.06", "1.08", "1.1") for k in (5, 10, 12, 20)]
    for r, k in rng.sample(pool, n):
        yield f"{r}^{{{k}}}", sig3(float(r) ** k)


def est_explog(rng):
    for x in rng.sample(("0.1", "0.2", "0.3", "0.5", "1.5", "2.5"), 2):
        yield f"e^{{{x}}}", sig3(math.exp(float(x)))
    for x in rng.sample((5, 8, 20, 50, 200, 500), 2):
        yield f"\\ln {x}", sig3(math.log(x))


def est_percent(rng, n):
    for _ in range(n):
        p, m = rng.choice((7, 13, 17, 22, 33, 48)), rng.randint(312, 8765)
        yield f"{p}\\% \\text{{ of }} {m}", sig3(p * m / 100)


def build_7(seed):
    rng = random.Random(seed)
    return assemble(rng, [
        ("Products", est_products(rng, 6)),
        ("Quotients", est_quotients(rng, 6)),
        ("Square roots", est_roots(rng, 5)),
        ("Compounding", est_compound(rng, 5)),
        ("Exponentials and logarithms", est_explog(rng)),
        ("Percentages", est_percent(rng, 4)),
    ])


def two_steps(rng, n):
    for i in range(n):
        a, x = rng.randint(2, 12), rng.randint(3, 25)
        b = rng.randint(1, a * x - 1)
        yield (f"{a}x - {b} = {a * x - b},\\ x", F(x)) if i % 2 else (f"{a}x + {b} = {a * x + b},\\ x", F(x))


def brackets(rng, n):
    for i in range(n):
        a, x = rng.randint(2, 9), rng.randint(4, 20)
        b = rng.randint(1, x - 1)
        yield (f"{a}(x - {b}) = {a * (x - b)},\\ x", F(x)) if i % 2 else (f"{a}(x + {b}) = {a * (x + b)},\\ x", F(x))


def both_sides(rng, n):
    for _ in range(n):
        c, g, x = rng.randint(2, 6), rng.randint(2, 6), rng.randint(3, 15)
        b = rng.randint(1, g * x - 1)
        yield f"{c + g}x - {b} = {c}x + {g * x - b},\\ x", F(x)


def with_fraction(rng):
    for _ in range(6):
        d, q, b = rng.randint(3, 9), rng.randint(3, 12), rng.randint(1, 9)
        yield f"\\frac{{x}}{{{d}}} - {b} = {q},\\ x", F(d * (q + b))
    for n, x, r in rng.sample([(12, 8, "1.5"), (18, 12, "1.5"), (15, 6, "2.5"), (5, 20, "0.25"), (9, 12, "0.75")], 2):
        yield f"\\frac{{{n}}}{{x}} = {r},\\ x", F(x)


def powers_x(rng):
    for x in rng.sample(range(13, 26), 3):
        yield f"x^2 = {x * x},\\ x", F(x)
    for b, x in rng.sample([(2, 6), (2, 9), (2, 11), (3, 4), (3, 5), (5, 3), (5, 4)], 3):
        yield f"{b}^x = {b**x},\\ x", F(x)


def build_8(seed):
    rng = random.Random(seed)
    return assemble(rng, [
        ("Two steps", two_steps(rng, 10)),
        ("Brackets", brackets(rng, 8)),
        ("Both sides", both_sides(rng, 8)),
        ("With a fraction", with_fraction(rng)),
        ("Powers", powers_x(rng)),
    ])


def powers_two(rng, n):
    for k in rng.sample(range(7, 17), n):
        yield f"2^{{{k}}}", F(2**k)


def powers_other(rng, n):
    pool = [(3, k) for k in range(4, 9)] + [(5, k) for k in range(3, 7)]
    pool += [(7, 3), (7, 4), (11, 3), (11, 4), (6, 3), (6, 4), (12, 3), (13, 3), (15, 3)]
    for b, k in rng.sample(pool, n):
        yield f"{b}^{{{k}}}", F(b**k)


def squares_29(rng, n):
    for a in rng.sample([x for x in range(13, 30) if x != 20], n):
        yield f"{a}^{{2}}", F(a * a)


def square_roots(rng, n):
    for a in rng.sample([x for x in range(32, 100) if x % 10], n):
        yield f"\\sqrt{{{a * a}}}", F(a)


def cube_roots(rng, n):
    for a in rng.sample(range(3, 16), n):
        yield f"\\sqrt[3]{{{a**3}}}", F(a)


def logs(rng, n):
    pool = [(2, k) for k in range(5, 15)] + [(3, k) for k in range(3, 7)] + [(5, k) for k in (3, 4)]
    pool += [(10, k) for k in range(3, 7)]
    for b, k in rng.sample(pool, n):
        yield f"\\log_{{{b}}} {b**k}", F(k)


def factorials(rng, n):
    for a in rng.sample(range(4, 10), n):
        yield f"{a}!", F(math.factorial(a))
    yield "\\frac{10!}{8!}", F(90)


def build_9(seed):
    rng = random.Random(seed)
    return assemble(rng, [
        ("Powers of two", powers_two(rng, 6)),
        ("Other powers", powers_other(rng, 9)),
        ("Squares up to 29", squares_29(rng, 7)),
        ("Square roots", square_roots(rng, 8)),
        ("Cube roots", cube_roots(rng, 5)),
        ("Logarithms", logs(rng, 5)),
        ("Factorials", factorials(rng, 4)),
    ])


def binomials(rng, n):
    for a, b in rng.sample([(a, b) for a in range(6, 14) for b in range(2, 6) if 2 * b <= a], n):
        yield f"\\binom{{{a}}}{{{b}}}", F(math.comb(a, b))


def factorial_ratios(rng, n):
    for a, g in rng.sample([(a, g) for a in range(6, 15) for g in (2, 3) if a - g >= 4], n):
        yield f"\\frac{{{a}!}}{{{a - g}!}}", F(math.factorial(a), math.factorial(a - g))


def half_powers(rng):
    half = "\\left(\\frac{1}{2}\\right)"
    ks = rng.sample(range(4, 11), 6)
    for k in ks[:3]:
        yield f"{half}^{{{k}}}", F(1, 2**k)
    for k in ks[3:]:
        yield f"1 - {half}^{{{k}}}", 1 - F(1, 2**k)


def binomial_chances(rng, n):
    for a, b in rng.sample([(a, b) for a in range(4, 10) for b in range(1, 5) if 2 * b <= a], n):
        yield f"\\binom{{{a}}}{{{b}}} / 2^{{{a}}}", F(math.comb(a, b), 2**a)


def drawing(rng, n):
    for top, bottom in rng.sample([(a, b) for b in range(6, 14) for a in range(2, b - 1)], n):
        yield (
            f"\\frac{{{top}}}{{{bottom}}} \\times \\frac{{{top - 1}}}{{{bottom - 1}}}",
            F(top * (top - 1), bottom * (bottom - 1)),
        )


def expected_values(rng, n):
    for _ in range(n):
        while True:
            p, w, c = rng.randint(1, 9), 10 * rng.randint(1, 9), 5 * rng.randint(1, 6)
            if p * w > (10 - p) * c:
                break
        ans = F(p * w - (10 - p) * c, 10)
        yield f"0.{p} \\times {w} - 0.{10 - p} \\times {c}", ans


def build_10(seed):
    rng = random.Random(seed)
    return assemble(rng, [
        ("Binomial coefficients", binomials(rng, 10)),
        ("Ratios of factorials", factorial_ratios(rng, 4)),
        ("Powers of a half", half_powers(rng)),
        ("Binomial chances", binomial_chances(rng, 6)),
        ("Drawing in a row", drawing(rng, 6)),
        ("Expected values", expected_values(rng, 8)),
    ])


def near_hundreds(rng, n):
    for _ in range(n):
        a, b = rng.randint(101, 109), 100 * rng.randint(2, 9) + rng.choice((-3, -2, -1, 1, 2, 3))
        yield f"{a} \\times {b}", F(a * b)


def squares_three(rng, n):
    pool = [100 * k + d for k in range(1, 10) for d in (-4, -3, -2, -1, 1, 2, 3, 4)]
    for a in rng.sample(pool, n):
        yield f"{a}^{{2}}", F(a * a)


def long_three(rng, n):
    for _ in range(n):
        q, d = rng.randint(123, 489), rng.randint(13, 49)
        yield f"{q * d} \\div {d}", F(q)


def long_decimals(rng, n):
    for _ in range(n):
        a, b = F(rng.randint(23, 89), 10), F(rng.randint(113, 487), 10)
        yield f"{dec(a)} \\times {dec(b)}", a * b


def build_11(seed):
    rng = random.Random(seed)
    return assemble(rng, [
        ("Three digits times two digits", three_by_two(rng, 8)),
        ("Near the hundreds", near_hundreds(rng, 4)),
        ("Squares near the hundreds", squares_three(rng, 4)),
        ("Long division", long_three(rng, 4)),
        ("Decimal products", long_decimals(rng, 4)),
    ])


def build_12(seed):
    rng = random.Random(seed)

    def percents():
        yield from any_percent(rng, 7)
        yield from percent_change(rng, 5)

    def fractions_decimals():
        yield from fraction_mix(rng, 1, 0, 0, 1)
        yield from decimal_answers(rng)

    def conversions():
        yield from as_percent(rng, 2)
        yield from as_fraction(rng, 2)

    def powers():
        yield from powers_two(rng, 3)
        yield from powers_other(rng, 2)
        yield from square_roots(rng, 3)
        yield from cube_roots(rng, 2)

    def algebra():
        yield from two_steps(rng, 2)
        yield from both_sides(rng, 2)

    return assemble(rng, [
        ("Adding and subtracting large numbers", big_sums(rng, 11)),
        ("Two digits times two digits", two_by_two(rng, 13)),
        ("Squares", squares(rng, 6)),
        ("Near a round number", near_round(rng)),
        ("Percentages", percents()),
        ("Fractions and decimals", fractions_decimals()),
        ("Conversions", conversions()),
        ("Powers and roots", powers()),
        ("Binomial coefficients", binomials(rng, 6)),
        ("Algebra", algebra()),
    ])


def answer_tex(x):
    return frac(x) if x.denominator not in (1, 2, 4, 5, 8, 10, 16, 20, 25, 40, 50, 80, 100, 1000) else dec(x)


def is_fraction_item(tex):
    return "\\frac" in tex or "\\binom" in tex or "as a fraction" in tex


def shown_answer(tex, ans):
    """How the key prints an answer: a percentage as a decimal, a fractional item as a fraction."""
    if "as \\%" in tex:
        return dec(ans)
    return frac(ans) if is_fraction_item(tex) and ans.denominator != 1 else answer_tex(ans)


def render(items, cols, row_tex):
    rows = math.ceil(len(items) / cols)
    lines = []
    for r in range(rows):
        cells = [row_tex(r + c * rows) if r + c * rows < len(items) else "" for c in range(cols)]
        lines.append(" & ".join(cells) + r" \\")
    return lines


BUILDERS = {
    1: build, 2: build_2, 4: build_4, 5: build_5, 7: build_7,
    8: build_8, 9: build_9, 10: build_10, 11: build_11, 12: build_12,
}
CHOICE = {3: build_3, 6: build_6}
TIPS = {
    1: SHORTCUTS, 2: SHORTCUTS_2, 3: SHORTCUTS_3, 4: SHORTCUTS_4, 5: SHORTCUTS_5, 6: SHORTCUTS_6, 7: SHORTCUTS_7,
    8: SHORTCUTS_8, 9: SHORTCUTS_9, 10: SHORTCUTS_10, 11: SHORTCUTS_11, 12: SHORTCUTS_12,
}
SEEDS = {n: 20261101 + n for n in range(1, 13)} | {5: 20261206, 12: 20289613}
HEAD = "% Generated by code/interviews-1/03-speed-drills/python/gen_drill.py. Do not edit.\n"


def write_families(sheet, items):
    rows = []
    for name, tip in TIPS[sheet].items():
        numbers = sorted(i + 1 for i, it in enumerate(items) if it[0] == name)
        rows.append(f"\\ivfamily{{{name}}}{{{', '.join(map(str, numbers))}}}{{{tip}}}")
    (OUT / f"drill-sheet-{sheet}-families.tex").write_text(HEAD + "\n".join(rows) + "\n", encoding="utf-8")


def write_free(sheet, seed):
    """A sheet of free answers."""
    items = BUILDERS[sheet](seed)

    def item_cell(i):
        return f"\\ivdrill{{{i + 1}}}{{${items[i][1]}$}}"

    def key_cell(i):
        _, tex, ans = items[i]
        plain_decimal = "." in tex and "\\frac" not in tex and "as a fraction" not in tex
        shown = dec(ans) if sheet == 7 or plain_decimal else shown_answer(tex, ans)
        # Two fractions in neighbouring rows touch without a little more height.
        strut = "\\rule[-9.5pt]{0pt}{23pt}" if "\\frac" in shown else ""
        return f"\\ivkey{{{i + 1}}}{{${shown}$}}{strut}"

    OUT.mkdir(exist_ok=True)
    (OUT / f"drill-sheet-{sheet}-items.tex").write_text(
        HEAD + "\\begin{ivdrillsheet}\n" + "\n".join(render(items, 3, item_cell)) + "\n\\end{ivdrillsheet}\n",
        encoding="utf-8",
    )
    (OUT / f"drill-sheet-{sheet}-key.tex").write_text(
        HEAD + "\\begin{ivdrillkey}\n" + "\n".join(render(items, 5, key_cell)) + "\n\\end{ivdrillkey}\n",
        encoding="utf-8",
    )
    write_families(sheet, items)


def write_choice(sheet, seed):
    """A sheet of multiple-choice items: options A to D in each cell, and the key gives the letter and the value."""
    items = CHOICE[sheet](seed)

    def item_cell(i):
        shown = "}{".join(dec(o) for o in items[i][3])
        return f"\\ivdrill{{{i + 1}}}{{${items[i][1]}$}}\\ivoptions{{{shown}}}"

    def key_cell(i):
        _, _, ans, opts = items[i]
        return f"\\ivkey{{{i + 1}}}{{$\\mathrm{{{'ABCD'[opts.index(ans)]}}}\\;{dec(ans)}$}}"

    OUT.mkdir(exist_ok=True)
    (OUT / f"drill-sheet-{sheet}-items.tex").write_text(
        HEAD + "\\begin{ivdrillsheet}\n" + "\n".join(render(items, 3, item_cell)) + "\n\\end{ivdrillsheet}\n",
        encoding="utf-8",
    )
    (OUT / f"drill-sheet-{sheet}-key.tex").write_text(
        HEAD + "\\begin{ivdrillkey}\n" + "\n".join(render(items, 5, key_cell)) + "\n\\end{ivdrillkey}\n",
        encoding="utf-8",
    )
    write_families(sheet, items)


def write(sheet, seed):
    (write_choice if sheet in CHOICE else write_free)(sheet, seed)


if __name__ == "__main__":
    number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    write(number, int(sys.argv[2]) if len(sys.argv) > 2 else SEEDS[number])
