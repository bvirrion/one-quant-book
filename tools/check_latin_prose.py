#!/usr/bin/env python3
"""Gate 9 -- the twin-comparison prose gate, for editions written in the Latin
alphabet (fr, nl, es, pt, id).

WHY THIS EXISTS. Gates 5 and 6 are Latin-oriented but score nothing about
whether a fragment was translated; gate 7 (Devanagari, Arabic) works because
residual English is *visibly foreign* in a non-Latin script; gate 8
(Indonesian) works because a curated list of English words that are not
Indonesian words can be built. Neither trick is available for French, Dutch,
Spanish or Portuguese: an English word is spelled with the same letters as a
French one, and no word list can separate them cheaply.

So this gate does not ask "is this English?". It asks a question that needs no
per-language knowledge at all:

    IS THIS FRAGMENT BYTE-IDENTICAL TO ITS ENGLISH TWIN, AND DOES IT CONTAIN
    A LOWERCASE WORD?

A translated fragment that still equals the English one either was never
touched or is a proper noun. Proper nouns (Gauss, Thevenin, Bolzano--
Weierstrass, RLC) carry no lowercase word once math and macros are stripped,
so requiring one removes nearly every false positive without knowing a word of
the target language. The comparison is positional: the Nth fragment of the
translated file against the Nth fragment of its English twin, and it is
skipped entirely when the counts differ, because then check_translation.sh
owns the divergence.

WHAT IT COVERS -- exactly the classes that shipped green in real editions:

  title     environment optional titles (\\begin{definition}[Physical quantity])
            and \\chapter/\\section headings
  text      \\text{...} inside math, including the subscripts that no reader of
            the source ever looks at (S_{\\text{created}})
  node      TikZ/pgfplots node text, node[...] {...}, and axis labels
  dup       a line repeated verbatim from the English twin sitting immediately
            above or below its own translation (an applier misuse: the
            English line was kept AND translated)

Each class was a real defect in a shipped or nearly-shipped edition. The
Portuguese Book 3 edition carried three untranslated environment titles, one
duplicated English line, fourteen English \\text{} subscripts and one English
TikZ node -- all of them through a green check_translation.sh and a clean PDF.

DELIBERATE BLIND SPOTS. \\mathrm{} is mathematics and stays English across
every edition by series convention (S_{\\mathrm{created}}), so it is never
compared. Unit arguments (\\qty, \\unit, \\num) are mathematics too. A fragment
whose lowercase words are all in ALLOWED_IDENTICAL is skipped: those are
strings a Latin-script edition legitimately leaves alone.

Usage:
    python3 tools/check_latin_prose.py parts/bachelor-1/fr parts/bachelor-1/solutions/fr
    python3 tools/check_latin_prose.py --quiet <dirs...>

The English twin is found by dropping the /<lang>/ path component, the same way
check_indonesian_prose.py does it.
"""
import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_hindi_prose import strip_comments          # noqa: E402

# --------------------------------------------------------------------------
# Fragment extractors. Each returns a LIST in document order, so the Nth
# fragment of a translation can be compared with the Nth of its twin.
# --------------------------------------------------------------------------
TITLE_ENVS = ("definition", "theorem", "proposition", "lemma", "corollary",
              "example", "remark", "method", "notation", "exercise",
              "problem", "proof", "omfigure", "figure", "table")
TITLE_RE = re.compile(
    r"\\begin\{(?:" + "|".join(TITLE_ENVS) + r")\}"
    r"\[((?:[^\[\]]|\[[^\]]*\])*)\]"
    r"|\\(?:chapter|section|subsection)\*?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")

# \text{...} but NOT \mathrm{...}: the first is prose, the second mathematics.
TEXT_RE = re.compile(r"\\text\{([^{}]*)\}")

# TikZ node text: "node {...}", "node[opt] {...}", "node[opt] (name) {...}",
# plus pgfplots xlabel=/ylabel=/title= values in braces.
#
# The option bracket must be consumed as a UNIT, not with a lazy [^{;]*?: a
# lazy run stops at the first "{" it can, which inside "node[lab/.style={font=
# \small}]" is the *style* group, so the gate reported "font=\small" as node
# text. Match an optional [...] (allowing one nested brace group inside it),
# then an optional (name), then the real body.
NODE_RE = re.compile(
    r"\\?node\b\s*"
    r"(?:\[(?:[^\[\]{}]|\{[^{}]*\})*\]\s*)?"
    r"(?:\([^()]*\)\s*)?"
    r"(?:at\s*\([^()]*\)\s*)?"
    r"\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
    r"|(?:xlabel|ylabel|zlabel|title)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")

# pgfplots' \legend{...} and \addlegendentry{...} MACROS -- the one piece of visible figure text that
# no gate in this project could see. The KEY form, "legend entries={...}", is
# covered by the sibling gates' TIKZ_TEXT_KEYS; the macro form carries no "=",
# and check_duplicated_lines below cannot help either, because a \legend is
# always INSIDE an axis environment and everything inside one is skipped by
# design. Book 4 carries 18 of them, several with real English ("disk, , no
# friction", "lost, pressure recovered", "copper, sea water"). Two levels of
# nesting are allowed: an entry may hold $\operatorname{Re}(\dots)$.
LEGEND_RE = re.compile(
    r"\\(?:legend|addlegendentry)\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}")

# Environments whose bodies are drawing code, copied byte-identically by
# design. A "duplicated English line" inside one of these is not a defect --
# it is the applier doing exactly what it promises.
DRAW_ENV_OPEN = re.compile(
    r"\\begin\{(?:tikzpicture|axis|semilogxaxis|semilogyaxis|loglogaxis|"
    r"scope|circuitikz|groupplot|pgfonlayer|MOdiagram)\}")
DRAW_ENV_CLOSE = re.compile(
    r"\\end\{(?:tikzpicture|axis|semilogxaxis|semilogyaxis|loglogaxis|"
    r"scope|circuitikz|groupplot|pgfonlayer|MOdiagram)\}")
# A DISPLAYED-MATH body is copied byte-identically by design too, and the
# "$" guard below cannot see it: an align* line carries no $ delimiters at all.
# Translating the \text{} label on one line of an align* therefore made the
# NEXT line -- pure mathematics, identical by construction and enforced as such
# by id_apply's math census -- report as a duplicated English line. Found on the
# Spanish Book 4 edition (11-maxwell-equations), where every edition that
# translates that label would have seen it.
MATH_ENV_OPEN = re.compile(
    r"\\begin\{(?:align|alignat|equation|gather|multline|eqnarray|split|aligned|gathered|cases|array|[pbvVB]matrix|smallmatrix|dmath)\*?\}|\\\[")
MATH_ENV_CLOSE = re.compile(
    r"\\end\{(?:align|alignat|equation|gather|multline|eqnarray|split|aligned|gathered|cases|array|[pbvVB]matrix|smallmatrix|dmath)\*?\}|(?<!\\)\\\]")

# A continuation line of drawing code carries no leading macro to key on:
# "xmin=0, xmax=4.3, ymin=0, ymax=21, xtick={0,1,2,3,4},". Key on the shape.
DRAW_OPTION_LINE = re.compile(
    r"^[^a-zA-Z]*(?:[a-z][a-z ]*\s*=\s*[^=]*,?\s*)+$|^[-\d.,()\s{}\[\]+*/]+;?$")

# A WHOLE word, bounded by any letter (not only ASCII): with [A-Za-z]
# bounds, "Utqia\u0121vik" yielded the fragment "vik" and "Schr\u00f6der"
# the fragment "der", and each edition had to allow-list the shards
# (Earth Book 1 wave 1, 2026-10-25). [^\W\d_] is "a Unicode letter".
LOWER_WORD = re.compile(r"(?<![^\W\d_])[a-z][^\W\d_]{2,}(?![^\W\d_])")

# Strings a Latin-script edition legitimately leaves byte-identical.
ALLOWED_IDENTICAL = {
    # brand, markup and file names
    "one", "course", "com", "www", "http", "https", "tex", "latex", "pdf",
    "github", "book", "md",
    # internationalisms and symbols that are the same word in the targets
    "min", "max", "log", "exp", "sin", "cos", "tan", "arg", "det", "lim",
    "sup", "inf", "abs", "mod", "rad", "deg", "cte", "const",
    "in", "out", "on", "off", "up", "down",          # circuit port labels
    "gaz", "gas", "air", "ion", "bar", "net", "cm", "mm", "km", "kg",
    "obscura", "camera",                              # camera obscura
    "et", "al",                                       # et al.
    # Spectroscopy series labels. "Lyman (ultraviolet)" and "Balmer
    # (visible)" are byte-identical in French, Spanish, Portuguese and Dutch
    # because BOTH words are the same in all of them -- the parenthesis is
    # not untranslated English. Verified in the fr and es Book 3 editions.
    "ultraviolet", "visible", "infrarood", "infrarouge",
    # Same word in Dutch as in English, verified in the nl Book 3 edition:
    # a guitar "fret" and a "pseudo-integrator" op-amp stage.
    "fret", "pseudo", "integrator",
    # Conventional subscript abbreviations. These are the SAME abbreviation in
    # French, Spanish, Portuguese, Dutch and Indonesian (ext = extérieur /
    # exterior / externo / extern; tot = total; cons = conservatives /
    # conservativas), so an identical \text{ext} is correct, not untranslated.
    # Verified against the shipped Book 2 editions before being listed.
    "ext", "int", "tot", "cons", "max", "min", "eff", "abs", "rel", "gen",
    "th", "eq", "crit", "ref", "res", "init", "fin", "moy", "med", "num",
    "den", "obs", "src", "det", "acc", "rms", "emf", "dc", "ac", "pp",
    # ---- biology -----------------------------------------------------------
    # Latin binomials are international scientific nomenclature: "Homo
    # sapiens" is written exactly so in French, Dutch, Spanish, Portuguese and
    # Indonesian, and leaving it byte-identical is CORRECT, not untranslated.
    # A binomial is two words, so without this it lands in the gate's
    # high-confidence multi-word tier and fires on every Latin edition at
    # once. Only the species epithet needs listing: the genus is capitalised
    # and the gate counts lowercase words. These are the epithets the canon
    # actually uses -- grep the English bodies again if a later book adds
    # species, rather than opening the rule to any "Capitalised lowercase"
    # pair, which would swallow "Simple sugars" and "Natural selection".
    "sapiens", "habilis", "erectus", "afarensis", "coli", "aureus",
    "victoria",
    # Book 3 (University Year 1) adds these five: Paris japonica,
    # Paramecium aurelia, Quercus robur, Felis catus, Canis lupus.
    # "lupus" was first added per-language by the Indonesian agent, which
    # noted in its own comment that it belonged here instead -- correctly: a
    # binomial epithet is identical in EVERY Latin-script target, which is the
    # criterion for this global set. Moved. Its three companions (domain,
    # genus, monomer) stay per-language, because French says domaine, genre
    # and monomere.
    "japonica", "aurelia", "robur", "catus", "lupus",
    # Book 4 (University Year 2): the wheat ancestors Triticum urartu and
    # Aegilops tauschii, named in the polyploidy figure of ch. 3 in every
    # edition. Reconstructed after the wave-1 entries were lost; see the
    # incident note in the Indonesian Book 4 report.
    "urartu", "tauschii",
}

# A fragment of a single word is reported in a SEPARATE, lower-confidence
# class. In the Latin-script targets a one-word fragment is very often a true
# cognate -- French "distance", "signal", "amplitude", "absorption", "visible"
# and Spanish "amplitud"-class words are correct prose, and firing on them
# would make the gate useless. A multi-word fragment left byte-identical is
# the high-confidence defect: no two languages agree on a whole phrase by
# accident. Both tiers are reported; only the multi-word tier is worth
# blocking on.
def _strip_nonprose(s):
    """Markup that is never prose in any language.

    A COLOUR NAME and an ENVIRONMENT NAME with its column spec are
    identifiers from the style file and from LaTeX, not words: left in,
    \\textcolor{omDef}{A\\,B} and \\begin{tabular}{c|ccc} supply the "words"
    omDef, tabular and ccc, which both make a correct fragment a finding at
    all and push it into the BLOCKING multi-word tier. Reported by the wave-1
    Book 4 agents (fr/nl/es/pt) 2026-09-16; reconstructed after the original
    fix was lost, so the wording of the original may have differed.
    """
    # A TeX line break is a separator, not the start of a macro name: node
    # text "{340\\incoming}" left "\incoming" for the macro strip below, so the
    # one English word of the label vanished and the fragment was never
    # reported. ~95 multi-line node labels in Earth Book 2 (2026-10-25,
    # coordinator, before wave 1). The optional skip "\\[2pt]" goes with it.
    s = re.sub(r"\\\\(?:\[[^\]]*\])?", " ", s)
    # tabular's column spec nests one level: {l@{\ }ccccc}. A plain
    # {[^{}]*} stops at the inner brace and leaves "ccccc" standing.
    s = re.sub(r"\\begin\s*\{tabular\*?\}\s*\{(?:[^{}]|\{[^{}]*\})*\}", " ", s)
    s = re.sub(r"\\(?:begin|end)\s*\{[^{}]*\}(?:\s*\{[^{}]*\})?", " ", s)
    s = re.sub(r"\\(?:textcolor|color|cellcolor|rowcolor|columncolor)\s*\{[^{}]*\}", " ", s)
    # Chemistry (2026-10-04): a formula, a drawing, a pictogram code and the
    # code arguments of the chemistry macros are identical in every edition by
    # design. Left in, a node reading "\ce{NaCl(aq)}" supplies the "word" aq
    # and fires on every Latin edition. Two brace levels: \ce{^{14}_{6}C}.
    s = re.sub(r"\\(?:ce|chemfig|ghs|chemmove|omorbs|setchemfig|cip)\s*(?:\[[^\]]*\])?"
               r"\s*\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}", " ", s)
    s = re.sub(r"\\omperiodictable(?:\[[^\]]*\])?", " ", s)
    # Earth series (2026-10-24): icon names, lithology styles and the
    # vertical-exaggeration number are code (\omwx{rain}, \omlith{shale}).
    s = re.sub(r"\\(?:omwx|omlith|omve)\s*(?:\[[^\]]*\])?\s*\{[^{}]*\}", " ", s)
    # The number format of a pgfplots value label is code, identical in every
    # edition: "nodes near coords={\pgfmathprintnumber[fixed, fixed zerofill,
    # precision=2]{\pgfplotspointmeta}}" supplied the "words" fixed, zerofill
    # and precision and fired the BLOCKING axisstr tier on a figure with no
    # prose in it. Reported by the French Chemistry Book 2 agent, 2026-10-04
    # (bachelor-1/02-periodicity, the successive-ionisation-energy bar chart).
    s = re.sub(r"\\pgfmathprintnumber\s*(?:\[[^\]]*\])?", " ", s)
    # One Quant Book (2026-11-09): \texttt{} holds identifiers from the tested
    # code (NbboBuilder(round\_lot)), and \omcode's path and line numbers are
    # its include arguments; both are identical in every edition by design.
    # Only \omcode's fourth argument, the caption, is prose.
    s = re.sub(r"\\texttt\s*\{(?:[^{}]|\{[^{}]*\})*\}", " ", s)
    s = re.sub(r"\\omcode\s*\{[^{}]*\}\s*\{[^{}]*\}\s*\{[^{}]*\}", " ", s)
    return s


def _word_count(s):
    s = _strip_nonprose(s)
    s = re.sub(r"\$[^$]*\$", " ", s)
    # A graphics path is never prose, in any language. The overlay-label
    # figures put \includegraphics INSIDE a tikz node, so the node-text
    # extractor hands the whole include to this gate -- and it is
    # byte-identical between English and every translation BY DESIGN. Left in,
    # "images/book1/ai/fig-frog-cycle.png" counts as several words and the
    # fragment lands in the high-confidence multi-word tier, firing on every
    # Latin edition for every annotated figure in the book.
    s = re.sub(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{[^{}]*\}", " ", s)
    s = re.sub(r"\\omimg\s*\{[^{}]*\}", " ", s)
    s = re.sub(r"\\(?:qty|unit|num|SI|si)\s*(?:\{[^{}]*\})?\{[^{}]*\}", " ", s)
    # A label argument is not prose: "def:b1:kinetic-theory:temperature" would
    # otherwise count as four words and make a bare \omterm line look like a
    # duplicated English sentence. It fired on three shipped editions at once.
    s = re.sub(r"\{[^{}]*:[^{}]*\}", " ", s)
    s = re.sub(r"\\[A-Za-z@]+", " ", s)
    # A HYPHENATED COMPOUND IS ONE WORD, not two. Counting the parts put the
    # international loanword "Crossing-over" -- correct, unchanged prose in
    # Dutch, French, Spanish and Portuguese -- into the blocking multi-word
    # tier, and a legitimate environment title FAILED a whole year until it
    # was retitled to satisfy the gate. That is the gate driving the
    # translation, which is backwards. A single lexical item, hyphens and
    # elision apostrophes included, is exactly the true-cognate case the
    # one-word tier exists for. Found by the Dutch Book 2 agent, 2026-09-05.
    return len(re.findall(r"[A-Za-z]{2,}(?:[-'\u2019][A-Za-z]{2,})*", s))


FOREACH_RE = re.compile(
    r"\\foreach\s+[^{]*?\bin\s*(\{(?:[^{}]|\{[^{}]*\})*\})", re.S)
AXIS_STR_RE = re.compile(
    r"(?:xticklabels|yticklabels|symbolic\s+[xy]\s+coords|legend\s+entries"
    r"|nodes\s+near\s+coords)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\})")


XCOLOR_NAMES = {"red", "green", "blue", "cyan", "magenta", "yellow", "black",
                "gray", "grey", "white", "darkgray", "lightgray", "brown", "lime",
                "olive", "orange", "pink", "purple", "teal", "violet"}
XCOLOR_EXPR = re.compile(r"[A-Za-z]+(?:!\d+(?:\.\d+)?(?:![A-Za-z]+)?)*")
NUMBER_FIELD = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)")


def _code_only_list(body):
    """True when every slash-field of every item is a number or a colour."""
    inner = body.strip()[1:-1]
    for item in inner.split(","):
        for field in item.split("/"):
            f = field.strip().strip("{}").strip()
            if not f or NUMBER_FIELD.fullmatch(f):
                continue
            if XCOLOR_EXPR.fullmatch(f):
                names = re.findall(r"[A-Za-z]+", f)
                if all(n in XCOLOR_NAMES or n.startswith("om") for n in names):
                    continue
            return False
    return True


def _fragments(text):
    """[(class, string, char-offset)] for every comparable fragment."""
    out = []
    for m in TITLE_RE.finditer(text):
        # A float placement specifier (\begin{table}[htbp], [h!]) is code,
        # not a title: reported by the Dutch Earth Book 3 agent, 2026-10-27.
        if m.group(1) is not None and re.fullmatch(r"\s*[htbpH!]+\s*", m.group(1)):
            continue
        out.append(("title",
                    m.group(1) if m.group(1) is not None else m.group(2),
                    m.start()))
    for m in TEXT_RE.finditer(text):
        out.append(("text", m.group(1), m.start()))
    for m in NODE_RE.finditer(text):
        out.append(("node",
                    m.group(1) if m.group(1) is not None else m.group(2),
                    m.start()))
    for m in LEGEND_RE.finditer(text):
        out.append(("legend", m.group(1), m.start()))
    # A \foreach LABEL LIST and a pgfplots string-valued KEY are visible text
    # that NO gate in this project could see, and the applier cannot cover them
    # either: id_apply compares \foreach lists BYTE-FOR-BYTE on purpose (a list
    # mixes labels with style names and coordinates, which must never change),
    # so an UNTRANSLATED list is the only form that passes it. Reported by the
    # Arabic Book 4 agent, 2026-09-16, which found four live cases in its own
    # tree -- English shipping behind two green gates. The census over the
    # other editions then found one in French and, in the ALREADY SHIPPED
    # books, four Indonesian ones.
    #
    # The twin comparison is the right owner precisely because it needs no
    # per-language knowledge: node NAMES ({kale,cab,spr}) and unit lists
    # ({10 s, 1 min}) are identical in every edition by design and land in the
    # one-word/cognate tier, while a real label ({0/prophase, 1/metaphase})
    # carries several words and blocks.
    for m in FOREACH_RE.finditer(text):
        body = m.group(1)
        # A \foreach list of BARE IDENTIFIERS is not text: it is node names,
        # consumed as (\t.west) and never printed. `{kale,cab,spr,kohl,broc,
        # cauli}` in the artificial-selection figure is byte-identical in all
        # eight editions BY DESIGN, and blocked the shipped grade-12 Indonesian
        # edition the moment this class was added. A list that CARRIES a label
        # always shows it: as a `\x/\lab` slash field ({0/prophase, 1/metaphase}),
        # as a brace group ({0/{1. a charged tRNA enters the A site}}), or as a
        # multi-word item ({10 s, 1 min}). Requiring one of those keeps every
        # real defect this class was written for and drops the identifier lists.
        if "/" not in body and "{" not in body[1:] and " " not in body:
            continue
        # A list of COORDINATES and COLOURS is not text either, slashes and
        # all: {0/0/black!40, 1.7/0.82/black!80} and {90/red/red, ...} are
        # drawing parameters, identical in every edition by design, and fired
        # the blocking tier on the very first chemistry control run
        # (2026-10-04). Skip a list only when EVERY field is a number or an
        # xcolor expression; one word anywhere keeps it.
        if _code_only_list(body):
            continue
        out.append(("foreach", body, m.start()))
    for m in AXIS_STR_RE.finditer(text):
        # `symbolic x coords` keys are printed only when the axis gives no
        # explicit tick labels for that direction. When it does, the keys are
        # code (matched by name to a figdata column, ASCII in every edition)
        # and the printed labels are checked through `xticklabels` itself.
        # Earth Book 3: `{buried, surface}` (ch. 23) and ten closure-chart
        # keys (ch. 25) needed a per-language allow-list in fr; 2026-10-27,
        # lenient only.
        sym = re.match(r"symbolic\s+([xy])", m.group(0))
        if sym:
            start = text.rfind("\\begin{axis}", 0, m.start())
            stop = min([i for i in (text.find("\\addplot", m.end()),
                                    text.find("\\end{axis}", m.end())) if i >= 0]
                       or [len(text)])
            if start >= 0 and re.search(sym.group(1) + r"ticklabels\s*=",
                                        text[start:stop]):
                continue
        out.append(("axisstr", m.group(1), m.start()))
    return out


# Per-LANGUAGE allow-lists. The global set above is for words identical in
# EVERY target; these are for words identical in ONE of them, which a global
# entry would blind the other six to. Amino-acid names are the clearest case:
# Dutch and French keep the English -ine forms (alanine, glycine), but Spanish
# and Portuguese say alanina and glicina, so listing them globally would hide a
# genuine Spanish defect.
#
# EVERY entry here is evidence: it comes from an agent reporting that the gate
# made it reword CORRECT prose. That report is a gate bug, not a workaround --
# a gate that drives the translation is worse than no gate (the Book 2 Dutch
# `Crossing-over` incident). Add to this list rather than letting the next
# agent reword around it, and say which edition supplied the evidence.
ALLOWED_BY_LANG = {
    # Reported by the Dutch Book 3 agent, 2026-09-06: 11 multi-word fragments
    # failed the BLOCKING tier although every one is correct Dutch.
    "nl": {
        # Latin anatomical nomenclature, unchanged in Dutch.
        "muscularis", "mucosae", "propria", "lamina", "serosa", "submucosa",
        # Amino acids and sugars keep the English -ine/-ose form in Dutch.
        "alanine", "serine", "glycine", "valine", "leucine", "proline",
        "lysine", "cysteine", "histidine", "arginine", "glutamine",
        "asparagine", "threonine", "methionine", "tyrosine", "fructose",
        "glucose", "sucrose", "lactose", "ribose", "gyrase",
        # Second round, reported by the same agent after the first fix: four
        # fragments still blocked, each for ONE word, each in a family already
        # here. -ose sugars beside ribose/glucose/lactose; an -ase enzyme
        # beside gyrase; and "carrier", which is the loanword Dutch membrane
        # physiology actually uses -- this edition's term config deliberately
        # keeps "carrier" (the transporter) linked and distinct from "drager"
        # (the NAD carrier). Adding them cleared gate 9 with NO change to the
        # text, which is the whole point.
        "galactose", "deoxyribose", "hexokinase", "carrier",
        # "per" is an ordinary Dutch preposition (4 H+ per ATP).
        "per",
        # Book 4 developmental vocabulary, identical in Dutch (reconstructed).
        "parental", "proximal", "distal", "posterior", "anterior", "somite",
        "dermomyotome", "induction", "recombinant", "megasporangium",
        "nucellus", "zygote", "embryo", "sensing",
        # Book 5 (nl agent, 2026-09-16). Latin disease nomenclature, unchanged
        # in Dutch ("xeroderma pigmentosum"); and the genomics loanwords Dutch
        # actually uses -- a Dutch bioinformatics text writes "contigs per
        # read", "seed" and "scaffold" exactly as English does. Adding them
        # cleared the blocking tier with NO change to correct Dutch prose.
        "xeroderma", "pigmentosum", "contigs", "contig", "read", "reads",
        "scaffold", "seed", "seeds",
        # "via" is an ordinary Dutch preposition, like "per" above.
        "via",
        # Reported by the Dutch Book 5 agent, 2026-09-17: the combinatorial-
        # code figure of the sensory-systems chapter carries a \foreach whose
        # label field is the row legend {1/receptor A, ... 5/receptor E}. The
        # list has slash fields, so it lands in the BLOCKING foreach tier, but
        # "receptor" is spelt exactly so in Dutch -- the label is already
        # correct Dutch and was NOT reworded. Same shape as the Spanish "lab,
        # pb, abd" entry below.
        "receptor",
        # Same shape again (Dutch Book 5 agent, 2026-09-17): the endocrine-axis
        # figure labels its top tier "hypothalamus\\CRH, TRH, GnRH, GHRH".
        # "hypothalamus" is spelt identically in Dutch (like "muscularis"
        # above) and the four releasing-hormone abbreviations are capitalised,
        # so the whole label is correct Dutch as it stands.
        "hypothalamus",
        # The Hox-cluster \foreach of the developmental-genetics chapter,
        # exactly the case the Spanish Book 5 agent reported below: the label
        # field is the list of Drosophila Hox gene SYMBOLS, canonical and
        # identical in every edition. Only the lowercase ones need listing.
        # (Dutch Book 5 agent, 2026-09-17.)
        "lab", "pb", "abd",
        # Chemistry Book 1, Dutch agent (2026-10-04): figure labels and a
        # title that are correct Dutch spelt exactly as in English. "water
        # in" / "water uit" on a condenser, "316 ppm in 1959" on the CO2
        # curve, and the definition title "Proton, neutron, nucleon" all
        # hit the BLOCKING tier with no word of English in them: "in" is the
        # Dutch preposition, "water" the Dutch noun, "ppm" a unit symbol,
        # and the three particle names are the Dutch names.
        "in", "water", "ppm", "proton", "neutron", "nucleon",
        # Same agent, grade 11: "lamp", "detector", "display" (spectrophotometer
        # parts) and "thermometer" are the Dutch nouns; "Red" is the
        # reductant symbol of the couple notation Ox/Red, kept as a symbol in
        # every edition; the title "Amine, amide" names the two families by
        # their Dutch names, which are spelt as in English.
        "lamp", "detector", "display", "thermometer", "red", "amine",
        "amide",
    },
    # French keeps the same -ine forms; accented ones (sérine) differ and are
    # deliberately absent, because there the identical spelling WOULD be a
    # defect.
    "fr": {"muscularis", "mucosae", "propria", "lamina", "alanine", "glycine",
           "valine", "leucine", "proline", "lysine", "arginine", "glutamine",
           "asparagine", "gyrase", "fructose", "glucose", "lactose", "ribose",
           # Book 4 developmental vocabulary (reconstructed).
           "parental", "proximal", "distal", "posterior", "anterior",
           "somite", "dermomyotome", "induction", "recombinant", "nucellus",
           "embryo", "sensing", "parental",
           # Book 5: the Latin disease name is unchanged in French medical
           # usage ("le xeroderma pigmentosum"), so the two-word TikZ node
           # label is correct prose, not residual English. Appended by the
           # French Biology Book 5 agent, 2026-09-16, together with three
           # ordinary French words that happen to spell like their English
           # twins inside short figure labels: "position (nm)" is a correct
           # French axis label and "caspase-8 active" is correct French for
           # the active form of the enzyme (the adjective follows the noun).
           "xeroderma", "pigmentosum", "position", "caspase", "active",
           # Book 5, second round, appended by the French Biology Book 5
           # agent, 2026-09-17. Five more fragments blocked although every
           # one is already correct French and none could be reworded
           # without falsifying it:
           #  * the Hox-cluster \foreach of the developmental-genetics
           #    chapter carries the Drosophila gene SYMBOLS in its label
           #    field (lab, pb, Dfd, Scr, Antp, Ubx, abd-A, Abd-B) --
           #    canonical nomenclature, identical in every edition by
           #    design; the Spanish and Portuguese Book 5 agents listed the
           #    same three lowercase symbols;
           #  * "distance (mm)" is a correct French axis label, like the
           #    "position (nm)" already listed above;
           #  * "interstitium" and "hypothalamus" are the French words
           #    themselves (the nephron and pituitary figures);
           #  * "Pr (inactive)" is correct French for the inactive form of
           #    phytochrome -- the adjective is spelt the same.
           "lab", "pb", "abd", "distance", "interstitium", "hypothalamus",
           "inactive",
           # Chemistry Book 1, French agent (2026-10-04): three definition
           # titles hit the BLOCKING title tier with no word of English in
           # them -- "Ion, cation, anion" (grade 9), "Amine, amide"
           # (grade 11) and "Anode, cathode" (grade 12) are the French terms
           # themselves, spelt exactly as in English (the Dutch agent listed
           # "proton, neutron, nucleon" for the same reason). Not reworded.
           "ion", "cation", "anion", "amine", "amide", "anode", "cathode",
           # Chemistry Book 2, French agent (2026-10-04): five fragments hit
           # the BLOCKING tier with no word of English in them, none reworded:
           #  * the definition title "Constitution, configuration,
           #    conformation" (stereochemistry) names the three French terms;
           #  * the scheme nodes "\cip{S}-butan-2-ol" and "SN2, inversion"
           #    (alcohol activation): IUPAC names are spelt identically in
           #    French ("butan", "ol"), and "inversion" is the French word;
           #  * the contact-process box "dilution\\\ce{...}" and the pH-curve
           #    legend "exact, ..." (the exact calculation, "exact" agreeing
           #    with "calcul") are the French words themselves.
           "constitution", "configuration", "conformation", "butan", "ol",
           "inversion", "dilution", "exact"},
    # Spanish and Portuguese keep the Latin positional adjectives unchanged.
    "es": {"proximal", "distal", "posterior", "anterior", "somite",
           "dermomyotome", "nucellus",
           # Reported by the Spanish Book 5 agent, 2026-09-17: the Hox-cluster
           # figure of the developmental-genetics chapter carries a \foreach
           # whose label field is the list of Drosophila Hox gene SYMBOLS
           # (lab, pb, Dfd, Scr, Antp, Ubx, abd-A, Abd-B). Gene symbols are
           # canonical and identical in every edition by design, but the list
           # has slash fields, so it lands in the BLOCKING foreach tier. Only
           # the lowercase symbols need listing; the capitalised ones are
           # already invisible to the word scan.
           "lab", "pb", "abd",
           # Reported by the Spanish Chemistry Book 2 agent, 2026-10-04: the
           # tosylation figure of the alcohol-activation chapter labels its
           # starting alcohol "\cip{S}-butan-2-ol" in a TikZ node. The IUPAC
           # substitutive name is spelt identically in Spanish (butan-2-ol,
           # like propan-2-ol, pentan-3-ol), so the node is already correct
           # Spanish and was NOT reworded; the two fragments of the locant
           # name are the only "words" the scan sees.
           "butan", "ol"},
    "pt": {"proximal", "distal", "posterior", "anterior", "somite",
           "dermomyotome", "nucellus",
           # Appended by the Portuguese Biology Book 5 agent, 2026-09-17.
           # Three fragments blocked although every one is correct Portuguese
           # and none could be reworded without falsifying it:
           #  * the Hox-cluster \foreach of the developmental-genetics
           #    chapter carries the Drosophila gene SYMBOLS (lab, pb, Dfd,
           #    Scr, Antp, Ubx, abd-A, Abd-B) in its label field -- canonical
           #    nomenclature, identical in every edition by design (the
           #    Spanish Book 5 agent listed the same three symbols);
           #  * the combinatorial-code \foreach of the sensory-systems
           #    chapter reads {1/receptor A, ... 5/receptor E}, and
           #    "receptor" is spelt exactly so in Portuguese (the Dutch
           #    Book 5 agent listed it for the same figure);
           #  * the limb-bud figure labels its posterior signal
           #    "ZPA: sonic hedgehog", the gene's own name, which no
           #    edition translates.
           "lab", "pb", "abd", "receptor", "sonic", "hedgehog",
           # Reported by the Portuguese Chemistry Book 2 agent, 2026-10-04:
           # the tosylation figure of the alcohol-activation chapter labels
           # its starting alcohol "\cip{S}-butan-2-ol" in a TikZ node. The
           # IUPAC substitutive name is spelt identically in Brazilian
           # Portuguese (butan-2-ol, like propan-2-ol, pentan-3-ol: the
           # names used throughout the edition), so the node is already
           # correct Portuguese and was NOT reworded; the two fragments of
           # the locant name are the only "words" the scan sees (the es and
           # fr agents listed the same two for the same node).
           "butan", "ol",
           # Appended by the Portuguese Chemistry Book 3 agent, 2026-10-06:
           # three fragments blocked although none is untranslated prose:
           #  * 17-frontier-orbitals, the Diels--Alder figure's \foreach
           #    {0/endo, 5/exo}: the fields are the endo/exo stereodescriptors
           #    (italic prefixes, identical in Portuguese -- "aduto endo",
           #    "regra endo" throughout the edition) and serve as keys;
           #  * 21-alkene-redox, the dihydroxylation node "syn: meso": the
           #    syn descriptor and the meso prefix are written exactly so in
           #    Portuguese;
           #  * 08-solid-liquid-diagrams, the proposition title
           #    "Schröder--van Laar": a proper name whose particle "van"
           #    (as in van 't Hoff, van Deemter) is a lowercase word, and
           #    whose umlaut makes LOWER_WORD (ASCII-only) read "Schröder"
           #    as "Schr" + "der" -- a tokeniser bug worth fixing for every
           #    language; "der" is listed here only to get past it.
           "endo", "exo", "syn", "meso", "van", "der"},
    # Indonesian absorbs Latin anatomical nomenclature verbatim.
    "id": {"muscularis", "mucosae", "propria", "lamina", "serosa", "submucosa",
           # Reported by the Indonesian Book 3 agent, 2026-09-06: three
           # multi-word fragments blocked although each is correct Indonesian.
           # "domain" and "genus" are the Indonesian rank names themselves
           # (the figure translates the ranks around them: filum, kelas, ordo,
           # famili), and "monomer" is the Indonesian word for a monomer. The
           # fourth fragment the agent found, "kingdom Animalia", WAS a real
           # defect and was translated to "kerajaan Animalia" instead of being
           # exempted here.
           "domain", "genus", "monomer",
           # Book 4: Indonesian anatomy keeps the Latin positional adjectives
           # ("posterior", "anterior") and the developmental loanwords
           # unchanged, so the limb-bud axis label is correct as it stands.
           # Reported by the Indonesian Book 4 agent, 2026-09-16.
           "posterior", "anterior", "proximal", "distal", "nucellus",
           # Book 5, appended by the Indonesian Biology Book 5 agent,
           # 2026-09-17. The Latin disease name is unchanged in Indonesian
           # medical usage ("xeroderma pigmentosum"), exactly as the Dutch and
           # French Book 5 agents reported for their editions, so the
           # two-word TikZ node label is correct prose, not residual English.
           "xeroderma", "pigmentosum",
           # Same round, same agent: the Hox-cluster \foreach of the
           # developmental-genetics chapter carries the Drosophila Hox gene
           # SYMBOLS in its label field (lab, pb, Dfd, Scr, Antp, Ubx, abd-A,
           # Abd-B). Gene symbols are canonical and identical in every
           # edition by design, but the list has slash fields, so it lands in
           # the BLOCKING foreach tier. Only the lowercase symbols need
           # listing; the Spanish, Portuguese, French and Dutch Book 5 agents
           # listed exactly the same three for the same figure.
           "lab", "pb", "abd",
           # Chemistry Book 1, appended by the Indonesian Chemistry Book 1
           # agent, 2026-10-04: the instrument is called "pH meter" in
           # Indonesian too (KBBI "meter" = measuring instrument), so the
           # g9/03 figure label "pH meter" is correct as it stands.
           "meter",
           # Chemistry Book 2, appended by the Indonesian Chemistry Book 2
           # agent, 2026-10-04: the ch. 22 figure node "\cip{S}-butan-2-ol"
           # is the IUPAC name exactly as Indonesian writes it (butan-2-ol,
           # propan-2-ol and pentan-3-ol are the names used throughout the
           # edition), so it was NOT reworded. The two fragments of the locant
           # name are the only "words" the scan sees -- the same two the es,
           # fr and pt agents listed for the same node.
           "butan", "ol",
           },
}


def _kept_terms():
    """One Quant Book: the terms its French glossaries keep identical to English.

    Desk usage (user ruling 2026-11-09) keeps flash loan, travel rule, dark pool
    in English, so a box title made of exactly such a term is correct French; the
    blocking `title` tier failed 12 of them in Book 3 (quant Book 3 fr agent).
    Read from sources/GLOSSARY_BOOK_*_FR.md: a `NN | English | French` line whose
    French form, notes removed, equals one of its English forms.
    """
    out = set()
    root = pathlib.Path(__file__).resolve().parent.parent / "sources"
    for g in sorted(root.glob("GLOSSARY_BOOK_*_FR.md")):
        for ln in g.read_text(encoding="utf-8").split("\n"):
            m = re.match(r"^\d\d \| (.+?) \| (.+)$", ln)
            if not m:
                continue
            en = {re.sub(r"\([^()]*\)", "", f).strip().lower() for f in m.group(1).split(" / ")}
            for f in m.group(2).split(" / "):
                f = re.sub(r"\[[^\]]*\]|\([^()]*\)", "", f).strip().lower()
                if f and f in en:
                    out.add(f)
    return out


KEPT_TERMS = _kept_terms()


def _kept_term(s):
    t = re.sub(r"\s+", " ", s.strip().strip("[]{}").strip()).lower()
    return t in KEPT_TERMS or (t.endswith("s") and t[:-1] in KEPT_TERMS)


def _allowed(lang):
    return ALLOWED_IDENTICAL | ALLOWED_BY_LANG.get(lang or "", set())


def _lang_of(path):
    """parts/<year>[/solutions]/<lang>/NN-slug.tex -> <lang>."""
    m = re.search(r"/([a-z]{2})/[^/]*$", str(path).replace("\\", "/"))
    return m.group(1) if m else None


def _has_lowercase_word(s, lang=None):
    """A lowercase word that is not an allowed internationalism."""
    s = _strip_nonprose(s)
    # Strip math and macros first: [$\arcsin$] and [Gram--Schmidt] must not fire.
    s = re.sub(r"\$[^$]*\$", " ", s)
    # A graphics path is not prose, and it is byte-identical to English BY
    # DESIGN -- id_apply's `img` census requires exactly that. The overlay-label
    # figures put \includegraphics inside a tikz node, so the node-text
    # extractor hands the whole include to this gate; without stripping it here
    # too, "images/book1/ai/fig-frog-cycle.png" supplies the lowercase word that
    # makes the fragment a finding at all. _word_count() already strips it, but
    # that only chooses the TIER -- this is what decides whether it is reported.
    # Found by the French Book 1 agent, 2026-09-04: 17 hits in 14 files, and a
    # FAILED check_translation.sh with nothing wrong in the text.
    s = re.sub(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{[^{}]*\}", " ", s)
    s = re.sub(r"\\omimg\s*\{[^{}]*\}", " ", s)
    # siunitx option keys are code, not prose: \qty[text-series-to-math=true]
    # (a bold unit-bearing answer) put "text series math true" into the dup tier
    # of the French Earth Book 3 edition (01-spherical-astronomy solutions,
    # 2026-10-26); the translation is correct and the line is identical to its
    # twin by design.
    s = re.sub(r"(\\(?:qty|num|ang|unit|si|SI|qtyrange|numrange|angle)\b)\s*\[[^\]]*\]", r"\1", s)
    s = re.sub(r"\\[A-Za-z@]+", " ", s)
    return any(w not in _allowed(lang) for w in LOWER_WORD.findall(s))


CAP_WORD = re.compile(r"(?<![^\W\d_])[A-Z][a-z]{2,}(?![^\W\d_])")


def _capitalised_only(s):
    """Capitalised word(s) and no lowercase word at all.

    _has_lowercase_word() decides whether a fragment is reported AT ALL, so a
    fragment made only of capitalised words was invisible in BOTH tiers. The
    English canon of Biology Book 3 has 42 \begin{proof}[Evidence] titles and
    ~30 one-word capitalised definition titles; every one of them could ship
    untranslated behind a green gate. The Spanish Book 3 agent found its 42 by
    writing an independent title census after this gate stayed silent, which is
    the gate failing at its one job.

    Reported in the LOW-CONFIDENCE tier only, never blocking: a capitalised
    one-word title is very often a true cognate (Mitosis, Virus, Turgor,
    Plasmid) or a proper noun (Michaelis--Menten, Hardy--Weinberg), and a gate
    that blocks on those would drive the translation instead of checking it --
    exactly the failure the hyphenated-compound bug caused on Book 2.
    """
    s = re.sub(r"\$[^$]*\$", " ", s)
    s = re.sub(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{[^{}]*\}", " ", s)
    s = re.sub(r"\\omimg\s*\{[^{}]*\}", " ", s)
    s = _strip_nonprose(s)
    s = re.sub(r"\\[A-Za-z@]+", " ", s)
    return bool(CAP_WORD.search(s)) and not LOWER_WORD.search(s)


def _line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def check_duplicated_lines(path, body, en_body, findings, lang=None):
    """An English line kept AND translated: the twin's line sits verbatim in
    the translation, adjacent to a line that is not in the twin at all."""
    # Floor 12, not 40: two short kept English lines shipped unseen (Earth Book 1
    # nl and the biology Book 1 pt edition, 2026-10-25); three counted words, not
    # four ("even in a moment." counts three).
    en_lines = {ln.strip() for ln in en_body.split("\n") if len(ln.strip()) > 12}
    lines = body.split("\n")
    depth = 0
    in_sources = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        # Track drawing AND displayed-math environments: everything inside one
        # is copied byte-identically on purpose, so a "duplicate" there means
        # nothing.
        opens = len(DRAW_ENV_OPEN.findall(ln)) + len(MATH_ENV_OPEN.findall(ln))
        closes = len(DRAW_ENV_CLOSE.findall(ln)) + len(MATH_ENV_CLOSE.findall(ln))
        was_inside = depth > 0
        depth = max(0, depth + opens - closes)
        if was_inside or opens:
            continue
        # One Quant Book: an omsources list keeps the titles of other people's
        # documents in English, so a line of it may be identical to its twin
        # (quant Book 3 fr agent, 2026-11-09).
        if "\\begin{omsources}" in ln:
            in_sources = True
        if in_sources:
            if "\\end{omsources}" in ln:
                in_sources = False
            continue
        if len(s) <= 12 or s not in en_lines:
            continue
        if not _has_lowercase_word(s, lang) or _word_count(s) < 3:
            continue
        # Prose only: drawing code and math are copied verbatim by design. A row
        # of the interview books' generated tracks table (\hyperref + counts) is
        # identical when the chapter title is (Book 20 fr, "C++", 2026-11-12).
        if re.search(r"\\(?:draw|fill|path|node|addplot|foreach|coordinate|"
                     r"begin|end|label|cref|ref|hyperref|index|input|item|omterm)\b", s) or "$" in s:
            continue
        if DRAW_OPTION_LINE.match(s):
            continue
        neighbours = [lines[j].strip() for j in (i - 1, i + 1)
                      if 0 <= j < len(lines)]
        if any(n and len(n) > 12 and n not in en_lines for n in neighbours):
            findings.append((str(path), i + 1, "dup",
                             "English line kept beside its translation: "
                             f"{s[:70]!r}"))


def check_file(path, findings):
    twin = pathlib.Path(re.sub(r"/[a-z]{2}/(?=[^/]*$)", "/", str(path)))
    if not twin.is_file() or twin == path:
        return
    lang = _lang_of(path)
    body = strip_comments(path.read_text(encoding="utf-8"))
    en_body = strip_comments(twin.read_text(encoding="utf-8"))

    mine, theirs = _fragments(body), _fragments(en_body)
    by_class = {}
    for cls, s, off in mine:
        by_class.setdefault(cls, []).append((s, off))
    en_by_class = {}
    for cls, s, off in theirs:
        en_by_class.setdefault(cls, []).append((s, off))

    for cls, items in by_class.items():
        en_items = en_by_class.get(cls, [])
        if len(items) != len(en_items):
            # A structural divergence; check_translation.sh owns it.
            continue
        for (s, off), (e, _) in zip(items, en_items):
            if s.strip() != e.strip():
                continue
            if lang == "fr" and _kept_term(s):
                continue
            if _has_lowercase_word(s, lang):
                tier = cls if _word_count(s) >= 2 else cls + "-1word"
            elif _word_count(s) >= 2 and LOWER_WORD.search(
                    _strip_nonprose(re.sub(r"\$[^$]*\$", " ", s))):
                # Every lowercase word is on an allow-list, so the fragment was
                # reported in NEITHER tier -- and genuinely untranslated text
                # can be built entirely from allowed words. The Portuguese
                # Book 4 agent found `$\mathrm{N_2}$ in air` shipped unseen
                # ("in" and "air" are both allowed), plus "cm to m" and two
                # `10\% at $K_d/10$` labels. Advisory, never blocking: the
                # allow-lists exist because these words are usually correct.
                tier = cls + "-1word"
            elif _capitalised_only(s):
                # No lowercase word: always the low-confidence tier. See
                # _capitalised_only() -- without this branch the fragment was
                # reported in NEITHER tier.
                tier = cls + "-1word"
            else:
                continue
            findings.append((str(path), _line_of(body, off), tier,
                             f"identical to English ({cls}): {s.strip()[:70]!r}"))

    check_duplicated_lines(path, body, en_body, findings, lang)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--max-detail", type=int, default=8)
    args = ap.parse_args()

    findings, files = [], 0
    for d in args.dirs:
        p = pathlib.Path(d)
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*.tex")):
            files += 1
            check_file(f, findings)

    if not findings:
        print(f"  latin prose gate: OK ({files} files)")
        return 0

    by_class = {}
    for rel, line, cls, msg in findings:
        by_class.setdefault(cls, []).append((rel, line, msg))
    print(f"  latin prose gate: {len(findings)} issue(s) in {files} files")
    for cls in sorted(by_class):
        hits = by_class[cls]
        print(f"    {cls:<8} {len(hits):>5} hit(s) in "
              f"{len({h[0] for h in hits})} file(s)")
        if not args.quiet:
            for rel, line, msg in hits[:args.max_detail]:
                print(f"        {rel}:{line}: {msg}")
            if len(hits) > args.max_detail:
                print(f"        ... {len(hits) - args.max_detail} more")

    # Exit non-zero ONLY for the multi-word tiers. The module docstring has
    # always said "both tiers are reported; only the multi-word tier is worth
    # blocking on", but main() returned 1 for any finding at all -- so gate 9
    # in check_translation.sh failed on the one-word tier, which in these
    # editions is overwhelmingly TRUE COGNATES (French "distance", "signal",
    # "amplitude"; Dutch "fret"). A gate that fires on correct prose gets
    # ignored, which is worse than not having it. The one-word hits are still
    # printed, because they are worth a human's eye; they are just not a
    # failure. Reported by the French Book 1 agent, 2026-09-04.
    blocking = sum(len(h) for c, h in by_class.items() if not c.endswith("-1word"))
    if blocking:
        return 1
    print("  latin prose gate: no multi-word findings "
          "(the one-word tier above is advisory -- read it, it is usually cognates)")
    return 0


# Appended by the Spanish Chemistry Book 3 agent, 2026-10-06: the Diels--Alder
# figure of 17-frontier-orbitals carries the \foreach {0/endo, 5/exo}; its
# fields are the endo/exo stereodescriptors, written identically in Spanish
# ("aducto endo", "regla endo" throughout the edition) and used as keys. Same
# two words the Portuguese Book 3 agent listed for the same figure.
ALLOWED_BY_LANG["es"] |= {"endo", "exo"}


# Appended by the French Chemistry Book 3 agent, 2026-10-06: three fragments
# hit the BLOCKING tier with no untranslated prose in them, none reworded:
#  * 17-frontier-orbitals, the Diels--Alder figure's \foreach {0/endo, 5/exo}:
#    the endo/exo stereodescriptors, written exactly so in French ("adduit
#    endo", "règle endo" throughout the edition) and used as keys (the pt
#    Book 3 agent listed the same two);
#  * 30-biomolecules, the legend "cation, zwitterion, anion": "zwitterion" is
#    the French term itself (the edition's defined term, \index{zwitterion});
#    cation and anion are already listed;
#  * 08-solid-liquid-diagrams, the proposition title "Schröder--van Laar": a
#    proper name; "van" is its lowercase particle and "der" the tokeniser
#    fragment of "Schröder" the pt agent described.
ALLOWED_BY_LANG["fr"] |= {"endo", "exo", "zwitterion", "van", "der"}

# Appended by the Dutch Chemistry Book 3 agent, 2026-10-06: five fragments hit
# the BLOCKING tier with no untranslated prose in them, none reworded:
#  * 17-frontier-orbitals, the Diels--Alder figure's \foreach {0/endo, 5/exo}:
#    the endo/exo stereodescriptors, written so in Dutch ("endo-adduct",
#    "endoregel" throughout the edition) and used as keys (es, fr, pt listed
#    the same two);
#  * 08-solid-liquid-diagrams, the title "Schröder--van Laar": a proper name;
#    "van" its particle, "der" the tokeniser fragment of "Schröder" (as fr);
#  * 06-ellingham, the axis node "(\unit{kJ} per mol \ce{O2})": "mol" is the
#    unit name, "per" is already listed;
#  * 07-liquid-vapour-diagrams, the node "ethanol--water (model)": "ethanol"
#    and "model" are the Dutch words themselves;
#  * 21-alkene-redox, the node "syn: meso": the stereodescriptors, written so
#    in Dutch ("syn-additie", "mesoverbinding").
ALLOWED_BY_LANG["nl"] |= {"endo", "exo", "van", "der", "mol", "ethanol",
                          "model", "syn", "meso"}

# Appended by the French Chemistry Book 4 agent, 2026-10-06: six fragments hit
# the BLOCKING tier with no untranslated prose in them, none reworded:
#  * solutions 05-group-theory-applied, answers 13 and 14 of the weekend
#    problem, "cis 2, trans 1, fac 2, mer 3." (the "dup" tier): the cis/trans
#    and fac/mer isomer descriptors, written exactly so in French, followed by
#    band counts -- the line is correct French as it stands;
#  * 06-rovibrational-spectroscopy, the axis node "absorbance (relative)":
#    "absorbance" and "relative" are the French words themselves;
#  * 27-radicals-carbenes, the carbene node "triplet\\ sp2 p": "triplet" is
#    the French term (the edition writes "carbène triplet", "état triplet");
#  * 30-total-synthesis, the retrosynthesis node "iodolactonisation,
#    Baeyer--Villiger": the French name of the reaction, plus a proper name;
#  * 31-green-industrial, the ammonia-loop node "purge (Ar, CH4)": "purge" is
#    the French word (the edition's "recyclage et purge").
ALLOWED_BY_LANG["fr"] |= {"cis", "trans", "fac", "mer", "absorbance",
                          "relative", "triplet", "iodolactonisation", "purge"}

# Appended by the Indonesian Chemistry Book 3 agent, 2026-10-06: two fragments
# hit the BLOCKING tier with no untranslated prose in them, none reworded:
#  * 17-frontier-orbitals, the Diels--Alder figure's \foreach {0/endo, 5/exo}:
#    the endo/exo stereodescriptors, written exactly so in Indonesian ("adduk
#    endo", "aturan endo" throughout the edition) and used as keys (es, fr,
#    nl, pt listed the same two);
#  * 06-ellingham, the axis node "(\unit{kJ} per mol \ce{O2})": "per mol" is
#    the Indonesian unit phrase itself ("per" is the Indonesian word too, as
#    in "per detik"; "mol" is the unit name; the nl agent listed "mol" for the
#    same node).
# A third, the ch. 23 proposition title "pH optimum", was reworded to "pH
# optimal" instead of being exempted.
ALLOWED_BY_LANG["id"] |= {"endo", "exo", "mol", "per"}

# Appended by the Indonesian Chemistry Book 4 agent, 2026-10-07: four fragments
# hit the BLOCKING tier with no untranslated prose in them, none reworded:
#  * solutions 05-group-theory-applied, answers 13 and 14 of the weekend
#    problem, "cis 2, trans 1, fac 2, mer 3." (the "dup" tier): the cis/trans
#    and fac/mer isomer descriptors, written exactly so in Indonesian (the
#    edition's "isomer cis", "isomer fac"), followed by band counts -- the
#    same line the fr Book 4 agent listed;
#  * 27-radicals-carbenes, the carbene nodes "singlet\\ sp2 p" and
#    "triplet\\ sp2 p": "singlet" and "triplet" are the Indonesian terms
#    (the edition writes "karbena singlet", "keadaan triplet" throughout; fr
#    listed "triplet" for the same node);
#  * 31-green-industrial, the ammonia-loop node "purge (Ar, CH4)": "purge" is
#    the Indonesian term of the Book 3 edition's definition ("Konversi sekali
#    lewat, daur ulang, purge"), kept so here (fr listed the same word).
ALLOWED_BY_LANG["id"] |= {"cis", "trans", "fac", "mer", "singlet", "triplet",
                          "purge"}

# Appended by the Spanish Earth & Space Book 1 agent, 2026-10-25: the grade-5
# climate-zone map node "Utqiaġvik" (the town's official name, kept in every
# edition) hits the BLOCKING "node" tier with no English in it. LOWER_WORD's
# [a-z] class stops at the non-ASCII "ġ", so the proper noun yields the
# lowercase fragment "vik". The other Latin-script editions keep the same name
# on the same node.
ALLOWED_BY_LANG["es"] |= {"vik"}

# Appended by the Portuguese Earth & Space Book 1 agent, 2026-10-25: the same
# grade-5 climate-zone map node "Utqiaġvik" (official name, kept in pt too);
# LOWER_WORD's [a-z] class stops at "ġ" and leaves the fragment "vik", which
# hits the blocking "node" tier with no English in it (see the es entry).
ALLOWED_BY_LANG["pt"] |= {"vik"}

# Appended by the Dutch Earth & Space Book 1 agent, 2026-10-25: the same
# grade-5 climate-zone map node "Utqiaġvik" (official name, kept in nl too);
# LOWER_WORD's [a-z] class stops at "ġ" and leaves the fragment "vik", which
# hits the blocking "node" tier with no English in it (see the es entry).
ALLOWED_BY_LANG["nl"] |= {"vik"}

# Appended by the Spanish Earth & Space Book 1 agent, 2026-10-25: the grade-6
# rock key (03-rocks-and-minerals) draws its yes/no arrows with two \foreach
# lists of NODE-NAME PAIRS, {q3/gran, q4/bas, q5/sand, q6/slat} and
# {q3/q4, q4/q5, q5/q6, q6/shal}. They are never printed and are identical in
# every edition by design, but the slash fields defeat the bare-identifier
# exemption above, so they land in the BLOCKING foreach tier. Only the
# lowercase node names need listing (the gate cannot tell a node-name pair
# from a label field; the other Latin-script editions will meet the same two).
ALLOWED_BY_LANG["es"] |= {"gran", "bas", "sand", "slat", "shal"}

# Appended by the French Earth & Space Book 1 agent, 2026-10-25: the same two
# false positives in fr. (1) The grade-5 climate-zone map node "Utqiaġvik"
# (official name, kept in fr): LOWER_WORD stops at "ġ" and leaves "vik" in the
# blocking "node" tier (see the es entry). (2) The grade-6 rock-key \foreach
# lists of node-name pairs {q3/gran, ...} and {..., q6/shal}, never printed and
# identical in every edition by design (see the es entry just above).
ALLOWED_BY_LANG["fr"] |= {"vik", "gran", "bas", "sand", "slat", "shal"}

# Appended by the Dutch Earth & Space Book 1 agent, 2026-10-25: the same
# grade-6 rock-key \foreach lists of TikZ node-name pairs
# ({q3/gran, q4/bas, q5/sand, q6/slat} and {q3/q4, q4/q5, q5/q6, q6/shal}),
# never printed and identical in every edition, land in the blocking
# "foreach" tier in nl too (see the es entry).
ALLOWED_BY_LANG["nl"] |= {"gran", "bas", "sand", "slat", "shal"}

# Appended by the Portuguese Earth & Space Book 1 agent, 2026-10-25: the same
# grade-6 rock-key \foreach lists of TikZ node-name pairs
# ({q3/gran, q4/bas, q5/sand, q6/slat} and {q3/q4, q4/q5, q5/q6, q6/shal}),
# never printed and identical in every edition, land in the blocking
# "foreach" tier in pt too (see the es entry).
ALLOWED_BY_LANG["pt"] |= {"gran", "bas", "sand", "slat", "shal"}

# Appended by the Portuguese Earth & Space Book 1 agent, 2026-10-25: the axis
# label "altitude (km)" (grade-8 atmosphere profiles) is correct Brazilian
# Portuguese -- "altitude" is the same word in both languages -- and with the
# unit it lands in the BLOCKING two-word node tier.
ALLOWED_BY_LANG["pt"] |= {"altitude"}

# Appended by the Dutch Earth & Space Book 1 agent, 2026-10-25: the grade-8
# sea-breeze figure (02-winds-global-circulation) labels the ground "warmer
# land" by day (and "kouder land" at night). That is correct Dutch -- "warmer"
# and "land" are the Dutch words themselves -- and the two-word node lands in
# the BLOCKING node tier.
ALLOWED_BY_LANG["nl"] |= {"warmer", "land"}

# Appended by the Indonesian Earth & Space Book 1 agent, 2026-10-25: the same
# grade-6 rock-key \foreach lists of TikZ node-name pairs
# ({q3/gran, q4/bas, q5/sand, q6/slat} and {q3/q4, q4/q5, q5/q6, q6/shal}),
# never printed and identical in every edition, land in the blocking
# "foreach" tier in id too (see the es entry).
ALLOWED_BY_LANG["id"] |= {"gran", "bas", "sand", "slat", "shal"}

# Appended by the Spanish Earth & Space Book 2 agent, 2026-10-25: the grade-12
# fold block diagram (02-mountain-building, lines 224 and 237) fills its layers
# with two \foreach lists that pair heights with COLOUR NAMES,
# {0.0/bandB, ...} and {0.0/0.6/bandB, ...}. They are never printed and are
# identical in every edition by design, but the slash fields put them in the
# BLOCKING foreach tier; the colour names are the only "words" it sees. The
# other Latin-script editions will meet the same two lists. Book 2 es
ALLOWED_BY_LANG["es"] |= {"bandB", "bandC", "bandD", "bandE", "bandF"}

# Appended by the Portuguese Earth & Space Book 2 agent, 2026-10-25: the same
# grade-12 fold block diagram (02-mountain-building, lines 223 and 236 of the
# pt file) and its two \foreach lists of heights paired with COLOUR NAMES
# ({0.0/bandB, ...}, {0.0/0.6/bandB, ...}): never printed, identical in every
# edition by design, in the BLOCKING foreach tier (see the es entry). Book 2 pt
ALLOWED_BY_LANG["pt"] |= {"bandB", "bandC", "bandD", "bandE", "bandF"}

# Appended by the French Earth & Space Book 2 agent, 2026-10-25: (1) the same
# grade-12 fold block diagram (02-mountain-building, lines 231 and 244 of the
# fr file) and its two \foreach lists of heights paired with COLOUR NAMES
# ({0.0/bandB, ...}, {0.0/0.6/bandB, ...}): never printed, identical in every
# edition by design, in the BLOCKING foreach tier (see the es entry). (2) The
# Varden-granite isochron label {plagioclase,\\hornblende} (07-age-of-the-earth,
# line 279 of the fr file): both mineral names are spelled exactly so in
# French ("le plagioclase", "la hornblende"), so the node is translated and
# merely identical; its two words put it in the BLOCKING node tier. Book 2 fr
ALLOWED_BY_LANG["fr"] |= {"bandB", "bandC", "bandD", "bandE", "bandF",
                          "plagioclase", "hornblende"}

# Appended by the Dutch Earth & Space Book 2 agent, 2026-10-25: the same
# grade-12 fold block diagram (02-mountain-building, lines 219 and 232 of the
# nl file) and its two \foreach lists of heights paired with COLOUR NAMES
# ({0.0/bandB, ...}, {0.0/0.6/bandB, ...}): never printed, identical in every
# edition by design, in the BLOCKING foreach tier (see the es entry). Book 2 nl
ALLOWED_BY_LANG["nl"] |= {"bandB", "bandC", "bandD", "bandE", "bandF"}

# Appended (append-only) by the Indonesian Earth & space Book 2 agent,
# 2026-10-26: the same grade-12 fold block diagram (02-mountain-building, lines
# 224 and 237 of the id file) and its two \foreach lists of heights paired with
# COLOUR NAMES ({0.0/bandB, ...}, {0.0/0.6/bandB, ...}): never printed,
# identical in every edition by design, in the BLOCKING foreach tier (see the es
# entry). Book 2 id
ALLOWED_BY_LANG["id"] |= {"bandB", "bandC", "bandD", "bandE", "bandF"}

# Appended by the French Earth & space Book 3 agent, 2026-10-26: blocking hits
# with no untranslated prose in them, none reworded (evidence: the fr edition of
# Book 3, `bachelor-1`):
#  * 23-diagenesis-basins, line 188, `symbolic x coords={buried, surface}`: the
#    two coordinate KEYS of a stacked-bar chart, matched by name to the `state`
#    column of figdata/out/bachelor-1-compaction-demo.dat, shared by every
#    edition; the printed tick labels (`xticklabels`) are translated;
#  * 25-radiometric-methods, line 567, `symbolic y coords={zrupb, spupb, hbar,
#    mssr, msar, btsr, btar, zrft, kfsar, apft}`: ten coordinate keys of the
#    closure-temperature chart, never printed (the `yticklabels` are translated);
#  * 19-weathering-clays, title "Bisiallitisation, monosiallitisation,
#    allitisation": the three weathering regimes of Pedro (1966), named exactly
#    so in French (the edition's own definition term);
#  * 28-atmospheric-circulation, title "Cyclone, anticyclone": the two French
#    words of the definition, spelt as in English.
ALLOWED_BY_LANG["fr"] |= {"buried", "surface", "zrupb", "spupb", "hbar", "mssr",
                          "msar", "btsr", "btar", "zrft", "kfsar", "apft",
                          "monosiallitisation", "allitisation", "anticyclone"}

# Appended by the Dutch Earth & space Book 3 agent, 2026-10-27: the one blocking
# node that is correct Dutch, with no untranslated prose in it:
#  * 28-atmospheric-circulation, line 489, the lake-and-ocean figure label
#    `warm water` ("warm water", the Dutch phrase, identical in spelling to the
#    English): both words are Dutch as they stand, the figure is not reworded.
ALLOWED_BY_LANG["nl"] |= {"warm", "water"}

# Appended by the coordinator of the French Earth & space Book 4 run
# (`bachelor-2`), 2026-10-28: blocking hits with no untranslated prose in them,
# none reworded:
#  * 17-oceanic-islands, line 386, the atoll boreholes as tick labels (Funafuti,
#    Kita-daito-jima, Bikini, Enewetak, with their years): place names;
#  * 24-climate-proxies, lines 362 and 498, photograph credits ending
#    "via Wikimedia Commons.)}": copied exactly by rule; "via" is French;
#  * 03-elements-in-the-earth, line 79, and 26-deep-time-climate, line 332:
#    `\foreach` lists of element symbols with the style keys atm, lith, chal,
#    sid, none, and of ICS colour names (icsOrdovician ...): code, not text;
#  * mineral, cloud and node words spelt the same in French: muscovite (split
#    mus-/covite in a node), quartz, diopside, anorthite, enstatite,
#    cristobalite, collision, coalescence, cumulo-/nimbus, tonnage (Mt);
#  * 24-climate-proxies, line 428, "Mg/Ca (\\unit{mmol/mol})" (the unit
#    argument reaches the tokenizer as "mmol", "mol"), and 11-thermobarometry, the
#    subscripts Mg,grt / Fe,grt / Ca,grt (grt = garnet, the IUGS symbol).
ALLOWED_BY_LANG["fr"] |= {"daito", "jima", "via", "atm", "lith", "chal", "sid",
                          "none", "icsOrdovician", "icsSilurian", "icsDevonian",
                          "icsCarboniferous", "icsPermian", "icsTriassic",
                          "icsJurassic", "icsCretaceous", "icsPaleogene",
                          "icsNeogene", "muscovite", "mus", "covite", "quartz",
                          "diopside", "anorthite", "enstatite", "cristobalite",
                          "collision", "coalescence", "cumulo", "nimbus",
                          "tonnage", "grt", "mmol", "mol"}

# Appended (append-only) by the Indonesian Earth & space Book 4 agent,
# 2026-10-30: the standard aluminosilicate MINERAL ABBREVIATIONS ky/and/sil as
# \text{} subscripts in the triple-point proof (bachelor-2 10-metamorphic-facies,
# lines 212-217: $\Delta G_{\text{ky}\to\text{and}}$, $G_{\text{sil}}$). They are
# symbols, kept byte-identical by id_apply's math census and identical in every
# edition; Indonesian spells the minerals kianit/andalusit/silimanit, so the
# symbols cannot be "translated". The id prose gate still catches a free "and".
ALLOWED_BY_LANG["id"] |= {"and", "sil"}

# Appended (append-only) by the Indonesian Earth & space Book 4 agent,
# 2026-10-30, mirroring the French entry above: (1) 03-elements-in-the-earth,
# line 79, the `\foreach` list of element symbols with the Goldschmidt style
# keys atm, lith, chal, sid, none -- code, byte-identical by design; (2)
# 11-pt-paths, the site subscripts Mg,grt / Fe,grt / Ca,grt (grt = garnet, the
# IUGS mineral symbol), frozen by id_apply's math census.
ALLOWED_BY_LANG["id"] |= {"atm", "lith", "chal", "sid", "none", "grt"}

# Appended (append-only) by the Indonesian Earth & space Book 4 agent,
# 2026-10-30, mirroring the French entry above: 17-oceanic-islands, line 386,
# the atoll boreholes as xticklabels (Funafuti, Kita-daito-jima, Bikini,
# Enewetak with their years) -- place names, identical in every edition.
ALLOWED_BY_LANG["id"] |= {"daito", "jima"}

# Appended (append-only) by the Indonesian Earth & space Book 4 agent,
# 2026-10-30, mirroring the French entry above: the ICS colour names in the
# period-bar `\foreach` lists of 19-phanerozoic-earth (lines 195, 480) and
# 26-deep-time-climate (line 332) -- colour keys of styles/oneearth.sty, code,
# byte-identical in every edition.
ALLOWED_BY_LANG["id"] |= {"icsCambrian", "icsOrdovician", "icsSilurian",
                          "icsDevonian", "icsCarboniferous", "icsPermian",
                          "icsTriassic", "icsJurassic", "icsCretaceous",
                          "icsPaleogene", "icsNeogene", "icsQuaternary"}

# Appended (append-only) by the Indonesian Earth & space Book 4 agent,
# 2026-10-30, mirroring the French entry above: 24-climate-proxies, line 428,
# the axis label "Mg/Ca (\\unit{mmol/mol})" -- the siunitx unit argument
# reaches the tokenizer as "mmol" ("mol" is already listed for id); a unit
# symbol, identical in every edition.
ALLOWED_BY_LANG["id"] |= {"mmol"}

# Appended (append-only) by the Spanish Earth & space Book 4 agent (Book 4 es),
# 2026-10-30, mirroring the French and Indonesian entries above: blocking hits
# with no untranslated prose in them, none reworded:
#  * 17-oceanic-islands, line 386, the atoll boreholes as xticklabels
#    (Funafuti, Kita-daito-jima, Bikini, Enewetak): place names;
#  * 03-elements-in-the-earth, line 79, the `\foreach` list of element symbols
#    with the Goldschmidt style keys atm, lith, chal, sid, none, and
#    26-deep-time-climate, line 332, the ICS colour names: code;
#  * 11-pt-paths, the site subscripts Mg,grt / Fe,grt / Ca,grt (grt = garnet,
#    the IUGS symbol), frozen by id_apply's math census;
#  * 24-climate-proxies, line 428, "Mg/Ca (\\unit{mmol/mol})": unit symbols;
#  * 12-crustal-melting, line 445, the axis nodes "A/CNK (molar)" and
#    "A/NK (molar)": "molar" is the Spanish adjective, spelt as in English.
ALLOWED_BY_LANG["es"] |= {"daito", "jima", "atm", "lith", "chal", "sid", "none",
                          "icsOrdovician", "icsSilurian", "icsDevonian",
                          "icsCarboniferous", "icsPermian", "icsTriassic",
                          "icsJurassic", "icsCretaceous", "icsPaleogene",
                          "icsNeogene", "grt", "mmol", "mol", "molar"}

# Appended (append-only) by the Portuguese Earth & space Book 4 agent (Book 4 pt),
# 2026-10-30, mirroring the French, Indonesian and Spanish entries above:
# blocking hits with no untranslated prose in them, none reworded:
#  * 17-oceanic-islands, line 386, the atoll boreholes as xticklabels
#    (Funafuti, Kita-daito-jima, Bikini, Enewetak): place names;
#  * 20-palaeoenvironments, line 193, a photograph credit ending
#    "via Wikimedia Commons.)}": copied exactly by rule; "via" is Portuguese;
#  * 03-elements-in-the-earth, line 79, the `\foreach` list of element symbols
#    with the Goldschmidt style keys atm, lith, chal, sid, none, and
#    26-deep-time-climate, line 332, the ICS colour names: code;
#  * 11-pt-paths, the site subscripts Mg,grt / Fe,grt / Ca,grt (grt = garnet,
#    the IUGS symbol), frozen by id_apply's math census;
#  * 12-crustal-melting, line 445, the axis nodes "A/CNK (molar)" and
#    "A/NK (molar)": "molar" is the Portuguese adjective, spelt as in English.
ALLOWED_BY_LANG["pt"] |= {"daito", "jima", "via", "atm", "lith", "chal", "sid",
                          "none", "icsOrdovician", "icsSilurian", "icsDevonian",
                          "icsCarboniferous", "icsPermian", "icsTriassic",
                          "icsJurassic", "icsCretaceous", "icsPaleogene",
                          "icsNeogene", "grt", "molar"}

# Appended (append-only) by the Dutch Earth & space Book 4 agent (Book 4 nl),
# 2026-10-30, mirroring the French, Indonesian, Spanish and Portuguese entries
# above: blocking hits with no untranslated prose in them, none reworded:
#  * 17-oceanic-islands, line 386, the atoll boreholes as xticklabels
#    (Funafuti, Kita-daito-jima, Bikini, Enewetak): place names;
#  * 26-deep-time-climate, line 332, the ICS colour names of the period bar:
#    style keys of styles/oneearth.sty, code;
#  * 11-pt-paths, the site subscripts Mg,grt / Fe,grt / Ca,grt (grt = garnet,
#    the IUGS symbol), byte-identical in every edition;
#  * 22-weather-systems, line 117, the cloud node "cumulo-/nimbus", and
#    29-ore-deposits, lines 460 and 553, the axis nodes "tonnage (Mt)": Dutch
#    words spelt as in English (cumulonimbus, tonnage);
#  * 15-wilson-cycle, line 112, the definition title "Terrane; microcontinent":
#    both are the Dutch terms (the edition's own \index keys), spelt as in English.
ALLOWED_BY_LANG["nl"] |= {"daito", "jima", "icsOrdovician", "icsSilurian",
                          "icsDevonian", "icsCarboniferous", "icsPermian",
                          "icsTriassic", "icsJurassic", "icsCretaceous",
                          "icsPaleogene", "icsNeogene", "grt", "cumulo",
                          "nimbus", "tonnage", "microcontinent"}


# One Quant Book (2026-11-09): the French editions follow trading-desk usage
# (user ruling), so the words the glossaries (sources/GLOSSARY_BOOK_*_FR.md)
# keep in English are correct French here. Curated by hand from the glossaries:
# only desk words with no French equivalent in use, never a function word or a
# noun the glossary translates (exchange, price, order, index stay gated).
ALLOWED_BY_LANG["fr"] |= {
    "alpha", "arbitrage", "axe", "backbone", "backtest", "backtests", "backwardation", "bail",
    "bear", "bid", "ask", "bonus", "bookmaker", "bootstrap", "box", "bridge", "broker", "brokers",
    "brokerage", "bucket", "buckets", "bull", "bump", "bund", "bundle", "bundles", "butterfly",
    "cap", "caps", "caplet", "caplets", "carry", "cash", "call", "calls", "callable", "cliquet",
    "collar", "contango", "crack", "crash", "crush", "dark", "dealer", "dealers", "delta",
    "depeg", "desk", "desks", "drawdown", "drawdowns", "edge", "equity", "flash", "flattener",
    "flattening", "floor", "floors", "forward", "forwards", "funding", "futures", "gamma",
    "gap", "gilt", "gilts", "hedge", "hedger", "hedgers", "jackknife", "lasso", "lite",
    "lookback", "maker", "makers", "taker", "takers", "mempool", "netback", "outright",
    "overround", "pack", "packs", "penny", "pip", "pips", "pool", "pools", "prime", "pricer",
    "pricers", "put", "puts", "quanto", "rally", "rebate", "repo", "repos", "restaking", "rho",
    "roll", "rollup", "rollups", "scalping", "searcher", "searchers", "smile", "snowball",
    "softs", "special", "specialness", "spark", "spread", "spreads", "squeeze", "stablecoin",
    "stablecoins", "stableswap", "staking", "steepener", "steepening", "straddle", "straddles",
    "strangle", "strangles", "strike", "strikes", "strip", "strips", "swap", "swaps", "swaption",
    "swaptions", "swing", "theta", "tick", "ticks", "trader", "traders", "trading", "tranche",
    "tranches", "upfront", "uptick", "vanna", "vega", "volga", "wildcard", "wholesaler",
    "wholesalers", "skew", "streaming", "through", "sell", "buy", "side", "sales", "hedge",
    "fund", "funds", "give", "look", "last", "lookback", "worst", "best", "snooping", "moneyness",
    "checkpointing", "multistart", "mirroring",
}


# One Quant Book 13 (low-latency, French, 2026-11-12): its measured charts label
# their bars with the C++ and Linux identifiers being timed (memory orders, clock
# sources, compiler flags, logging calls), printed in English in every language.
# Only identifiers, never a prose word the chapters translate.
ALLOWED_BY_LANG["fr"] |= {
    "rdtsc", "rdtscp", "gettimeofday", "steady", "clock", "native", "lto", "pgo", "pmr",
    "new", "delete", "relaxed", "release", "acquire", "seq", "cst", "binlog", "snprintf",
    "fprintf", "ostringstream", "firm", "rustc", "fast", "math",   # -ffast-math
}

# One Quant Book 14 (networks, French, 2026-11-12): figure nodes that read the same in French. AWS zone ids
# (use1-az4), French words (participant, zone, colocation) and the desk's "ticker plant".
ALLOWED_BY_LANG["fr"] |= {"use", "az", "participant", "zone", "colocation", "ticker", "plant"}

# One Quant Book 15 (platforms, French, 2026-11-12): product names in a legend (DuckDB, Polars, SQLite, pandas, numpy),
# column and key names drawn in figures (sym, ts, bid, ask, instrument_id, account_id), symbolic coordinates that are a
# CSV's keys (point, report, analytic), and figure words spelt the same in French (lot, correction, partition, date,
# table, messages, archive, desk, puts).
ALLOWED_BY_LANG["fr"] |= {
    "duckdb", "polars", "sqlite", "pandas", "numpy", "sym", "ts", "bid", "ask", "instrument", "account", "id",
    "point", "report", "analytic", "lot", "correction", "partition", "date", "table", "messages", "archive",
    "desk", "puts",
    "omDef", "omMeth", "omThm", "omProp",   # the series colour names in a \foreach list (case-sensitive)
}

# One Quant Book 16 (desk, French, 2026-11-12): figure nodes that read the same in French (pod, capital, options,
# prime broker), the US registration categories kept in English (FCM, IB, CPO, CTA, swap dealer, commodity pool operator,
# introducing broker), durations in tick labels (min, h), and due diligence.
ALLOWED_BY_LANG["fr"] |= {"pod", "capital", "options", "prime", "broker", "fcm", "ib", "cpo", "cta", "swap", "dealer",
                          "commodity", "pool", "operator", "introducing", "min", "h", "due", "diligence"}

# One Quant Book 17 (industry), French pilot edition: firm, exchange and city names in figure nodes, legends and
# \foreach lists, the internal node keys of Fig. 18.1, the job title "Trader" (ch. 16) and \text{base} in a formula.
ALLOWED_BY_LANG["fr"] |= {"drw", "tower", "research", "jane", "street", "hudson", "river", "trading", "millennium",
                          "management", "balyasny", "asset", "schonfeld", "strategic", "advisors", "exoduspoint",
                          "hong", "kong", "zurich", "chicago", "new", "york", "infrastructure", "philadelphia", "stock",
                          "exchange", "board", "optiver", "susquehanna", "group", "one", "san", "francisco",
                          "belvedere", "amsterdam", "base", "trader", "ceo", "cro", "mkt", "mrm", "ra", "qa", "ld",
                          "ds", "dv", "rd", "rv", "v1"}

if __name__ == "__main__":
    sys.exit(main())

