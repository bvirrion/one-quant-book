"""Which files a book is made of, and in which order.

The order matters: a term is never linked in a chapter that comes *before* the
chapter defining it. Within one year the two-digit filename prefix would do, but
a book spans several years (Book 1 has nine), and grade-3/01 and grade-9/01 are
both "chapter 01". So the sequence is read from the book's own entry file, which
is the same order the reader meets the chapters in.
"""
import os
import re

ENTRY = {
    1: "one_quant_book_01_markets_1.tex",
    2: "one_quant_book_02_markets_2.tex",
    3: "one_quant_book_03_markets_3.tex",
    4: "one_quant_book_04_methods.tex",
    5: "one_quant_book_05_derivatives.tex",
    6: "one_quant_book_06_rates_credit_risk.tex",
    7: "one_quant_book_07_research.tex",
    8: "one_quant_book_08_strategies_1.tex",
    9: "one_quant_book_09_strategies_2.tex",
    10: "one_quant_book_10_microstructure.tex",
    11: "one_quant_book_11_hft.tex",
    12: "one_quant_book_12_ml.tex",
    13: "one_quant_book_13_low_latency.tex",
    14: "one_quant_book_14_networks.tex",
    15: "one_quant_book_15_platforms.tex",
    16: "one_quant_book_16_desk.tex",
    17: "one_quant_book_17_industry.tex",
    18: "one_quant_book_18_interviews.tex",
}

LANGS = {
    1: ("en",),
    2: ("en",),
    3: ("en",),
    4: ("en",),
    5: ("en",),
    6: ("en",),
    7: ("en",),
    8: ("en",),
    9: ("en",),
    10: ("en",),
    11: ("en",),
    12: ("en",),
    13: ("en",),
    14: ("en",),
    15: ("en",),
    16: ("en",),
    17: ("en",),
    18: ("en",),
}


def years(book):
    """The year directories the entry file inputs, in reading order."""
    src = open(ENTRY[book], encoding="utf8").read()
    return re.findall(r'\\input\{parts/([^/}]+)/part\}', src)


def chapters(book):
    """[(year, stem)] in reading order, from each parts/<year>/part.tex.

    Grade years include with \\ominput{<year>}{<stem>} (language-aware), the
    bachelor years with a plain \\input{parts/<year>/<stem>}.
    """
    out = []
    for year in years(book):
        part = open("parts/%s/part.tex" % year, encoding="utf8").read()
        for m in re.finditer(
                r'\\ominput\{([^}]+)\}\{([^}]+)\}'
                r'|\\input\{parts/([^/}]+)/([^}/]+)\}', part):
            y, stem = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
            if stem == "part":
                continue
            out.append((y, stem))
    return out


def files(book, lang):
    """[(path, seq, is_solutions)] for the whole book in the given language.

    seq is the chapter's position in the book (1-based), shared by a chapter and
    its solutions file. A translated file that does not exist is skipped rather
    than falling back to English: linking the English body under --lang fr would
    put French links in a file the French book never inputs.
    """
    out = []
    for seq, (year, stem) in enumerate(chapters(book), start=1):
        if lang == "en":
            course = "parts/%s/%s.tex" % (year, stem)
            sols = "parts/%s/solutions/%s.tex" % (year, stem)
        else:
            course = "parts/%s/%s/%s.tex" % (year, lang, stem)
            sols = "parts/%s/solutions/%s/%s.tex" % (year, lang, stem)
        for path, is_sol in ((course, False), (sols, True)):
            if os.path.exists(path):
                out.append((path, seq, is_sol))
    return out
