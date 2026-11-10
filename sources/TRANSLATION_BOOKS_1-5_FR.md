# French pilot editions of One Quant Book 1–5: the run file

**Scope.** French (`fr`) editions of Books 1–5 (`markets-1`, `markets-2`, `markets-3`, `methods`, `derivatives`) by the
pilot method of `../pilot_translation_instruction.md`. Requested by the user 2026-11-09. Pilot tier: gates green, not
read sentence by sentence, figures sampled, solutions not recomputed.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section; glossaries, toolchain port and coordinators `claude-opus-5-5` (Opus 5.5) |
| Run shape (user ruling 2026-11-09) | The main session ported the toolchain and wrote all five glossaries; then one Opus coordinator agent per book, **at most three at once** (Books 1–3, then 4 and 5 as slots free), each `run.py --workers 3` |
| Terminology (user ruling 2026-11-09) | **Desk usage**: the French term where French practitioners use one, the English word where French desks say it in English; English in parentheses at the definition |

## What the main session did (Phase 0–1, 2026-11-09)

- `styles/onequant.sty`: babel French (pdfTeX, `shorthands=off`, guarded by `IfFileExists`), a language-aware
  `\ominput`/`\ominputsol`, and every hard-coded English string moved to `styles/lang/en.tex` (`\omnameListing`,
  `\omnameFigure`, `\omnameBox`, `\omdatedtitle`, `\omnameStep`, `\omnameSources`, …). **The English PDFs of Books 1–5
  are text-identical to the pre-port builds** (pdftotext, 0 diff lines; 374/363/332/351/348 pp, 0/0/0).
- `styles/lang/fr.tex`; `frontmatter/{preface,colophon}.fr.tex`; five entry files `one_quant_book_0N_*_fr.tex`;
  `latexmkrc` and `.github/workflows/ci.yml` (texlive-lang-french, release body).
- Tools ported from the Earth repo: `tools/id_apply.py` (plus a `code` census: `\omcode` path and line range,
  `\begin{dated}` date, `\texttt{}` contents), `tools/check_translation.sh` (gate 3 counts `iq:` keys; gate 12 is the new
  `tools/check_quant_twin.py`), `tools/check_latin_prose.py` + `check_hindi_prose.py` (blanks `\texttt` and `\omcode`
  arguments; a quant-French allow-list of desk words), `tools/term_config/lang_fr.py`, `book{1..5}_fr.py`, `fr` in
  `tools/termlink/books.py` and `link_defined_terms.py`.
- Pilot scripts: `langs/fr.md` lost its Earth-only lines to `langs/series/one-earth-and-space-sciences-book.fr.md`;
  `langs/series/one-quant-book.fr.md` is new; `post.py --units` skips the French unit pass outside the Earth repo
  (`UNIT_REPOS`); `common.py` lets lines inside `omsources` stay in English (titles of other people's documents).
- Glossaries: `sources/GLOSSARY_BOOK_{1..5}_FR.md` (1,447 lines written by hand, a `00` core vocabulary in Book 1), and
  generated `GLOSSARY_BOOK_N_FR.run.md` = the book's own lines plus every earlier book's lines as `00`. Every defined
  term of each book is covered; `glossary.py split` has been run for all five (`draft/pilot-<slug>-fr/glossary/`).
- Trial: Book 1 chapter 9 in `draft/pilot-trial-markets-1-fr/`: 18 calls, $0.13 list, one section needed a re-run
  (a two-line `\iqlookfor` merged into one), 0 NUMDIFF, 0 orphan lines, probe 14 pp 0/0/0. Figure findings: a legend
  overlapping a longer French y-label (Fig. 9.2), English labels from `symbolic y coords` (Figs 9.3, 9.4) and from a
  `\foreach` list (`Exchange A`).

## Wave findings applied (2026-11-10, after Book 3)

Book 3 `fr` closed at 87 (pilot tier), 354 pp, 0/0/0, gates green. Shared fixes made by the main session before
Books 4 and 5: `repair.py` refuses a reply that is the English line again; `common.py`'s `visible()`,
`tools/check_orphan_lines.py` and `check_latin_prose.py` blank `\texttt{}`; the prose gate's `dup` tier skips
`omsources` lines, and every tier accepts a fragment that is exactly a term the glossaries keep in English
(`[Flash loan]`, `[Travel rule]`); the series card gained the `\cref` gender table, `livre~N`, `les frais` and the
`\item` rule; `pdfsweep.py` takes the Earth Book 5 French PDF as reference.

## Wave findings applied (2026-11-10, after Book 2)

Book 2 `fr` closed at 88 (pilot tier), 392 pp, gates green; its last 2 overfull boxes came from a shared header bug.
Shared fixes made by the main session:
- **`styles/onequant.sty`, header:** a mark that is not an `\omTocMark` (the index's) printed outside `\truncate`,
  which always takes its full width, so the book title wrapped onto a third line (`Overfull \vbox`, index pages). Raw
  marks now print in place of the truncated title.
- **`styles/lang/fr.tex`:** cleveref's conjunctions are French (`et`, `à`); `\cref{a,b}` printed "and" in every
  French edition.
- **`repair.py`** refuses a reply with under 60 % of the English line's words, or one that adds a `%` comment.
- **`tools/check_orphan_lines.py`** skips `omsources` blocks.
- **Series card:** `1\up{er}` (Book 3's 24 `\textsuperscript{er}` were converted), sentence-initial `\Cref` and
  "dans la \cref", le DV01, French month/weekday/tenor names in figures.
- Open (no fix yet): a `\texttt{…}` broken across a line puts the twin gate and the prose `dup` tier at odds. Book 2's
  workaround, `draft/pilot-markets-2-fr/work/jointt2.py`, joins the broken line to its neighbours.

## Wave findings applied (2026-11-10, after Book 1)

Book 1 `fr` closed at 88 (pilot tier), 403 pp, 0/0/0. Shared fixes by the main session:
- `tools/id_apply.py` `code_args` compares `\texttt` contents with whitespace normalised: a `\texttt` broken across
  lines in the English (ch. 12:342) no longer sets the twin gate against the orphan and `dup` checks. Book 1's gate 12
  now passes, and Book 2's `jointt2.py` workaround is no longer needed.
- `pilot_translation/common.py` `visible()` blanks `yticklabels from table=…` lines: six correct replies had been
  refused as "left in English".
- Percent is `5~\%` across the series; Book 1's 351 `\,\%` were converted by the main session (Book 2's last English
  "$…$ and $…$" too).
- Not changed: the `\foreach` tier of `check_latin_prose.py` blocks a slash list of node names that prints nothing
  (`{own/agent,…}`); a bare-identifier exemption would also pass real labels (`0/prophase`), so rename the node
  instead. The broken `\index{clearing\nmember}` keys in the English print one entry each and are harmless.
- Book 1's productive sweeps: doubled currency (72), `\%` with no space, a contact sheet of every captioned figure
  (`draft/pilot-markets-1-fr/work/sheet/mk.py`: 23 defective figures, no log warning), and `realign.py` for long
  interview answers whose lines Haiku merges.

## Wave findings applied (2026-11-10, after Book 4)

Book 4 `fr` closed at 88 (pilot tier), 372 pp, 0/0/0. Shared fixes by the main session:
- **Gate 12 compares math on disk.** `tools/check_quant_twin.py` now adds the ordered math spans
  (`id_apply.math_spans`) to the code census, with whitespace collapsed and the two moves the series card allows
  taken out (`\$` leaving the span; a space before `\%`). A planted `~:` inside `$…$` fails it. The reason: Book 4
  found a typography sweep reused from Book 3 putting `~:`/`~;` inside math after install, which nothing checked.
  Book 4's `work/recheck.py`, run by the main session over Books 1–4, also found Book 1's coordinator had put `\,`
  before `\%` inside 296 math spans (converted to `~\%` by the main session's percent sweep); both are reverted to
  the English `\%`.
- **`\iqroles` translated.** Books 2–4 had left 137 role names in English (`researcher`, `risk`, `developer`); mapped
  per the series card by script.
- Not changed: `repair.py` turned a `\section{Interview questions}` into `\section{Exercices}` and wrote
  `du \cref{prop:…}` despite the series card's table (it gets the card); a TikZ `matrix of nodes` with prose cells
  cannot pass both the draw census and the English-left check (Book 4 translated the cells by hand).

## Brief for each book's coordinator agent

You are the coordinator of ONE French edition. Book N, slug, entry and description:

| N | Slug | Entry (no `.tex`) | `--book-desc` |
|---|---|---|---|
| 1 | `markets-1` | `one_quant_book_01_markets_1_fr` | `university-level textbook of quantitative finance (One Quant Book 1, Markets I: the ecosystem and exchange-traded markets)` |
| 2 | `markets-2` | `one_quant_book_02_markets_2_fr` | `university-level textbook of quantitative finance (One Quant Book 2, Markets II: rates, FX and credit)` |
| 3 | `markets-3` | `one_quant_book_03_markets_3_fr` | `university-level textbook of quantitative finance (One Quant Book 3, Markets III: commodities, energy and crypto)` |
| 4 | `methods` | `one_quant_book_04_methods_fr` | `university-level textbook of quantitative finance (One Quant Book 4, Quantitative Methods: stochastic calculus, statistics, time series, optimisation, numerics)` |
| 5 | `derivatives` | `one_quant_book_05_derivatives_fr` | `university-level textbook of quantitative finance (One Quant Book 5, Derivatives and Volatility)` |

**Read first:** `../pilot_translation_instruction.md` (all of it: you run its steps 4–8 and 9's deliverables), this file,
`CLAUDE.md` (rules), and in `../translation_instruction.md` the "Hard rules" and "New language checklist" sections (for
the traps: elision at a line end, `\qty` units, `\legend`/`\foreach`, Latin twin gate). The Earth Book 5 French files are
your models: `../one-earth-and-space-sciences-book/translation_scores/book_5/fr/translation_score.md` and
`../one-earth-and-space-sciences-book/sources/TRANSLATION_BOOK_5_FR.md`.

**Set:**
```sh
cd /home/bvirrion/repositories/one-course/pilot_translation
REPO=/home/bvirrion/repositories/one-course/one-quant-book; ARGS="--repo $REPO --year <slug> --lang fr"
DESC="<book-desc>"; RUN=$REPO/draft/pilot-<slug>-fr      # exists, with glossary/ already split
```

**Steps** (the numbers are the pilot doc's):
4. `python3 run.py $ARGS --workers 3 --book-desc "$DESC" > $RUN/run.log 2>&1`. Re-run until `0 with a rejected
   section`. If it stops on a usage limit or failed calls, **stop and report** (say how many sections are done); the
   main session resumes it.
5. `post.py` **without `--units`**, `repair.py --dry-run`, `repair.py`, `post.py` again; logs in `$RUN`. Every `NUMDIFF`
   difference explained; fix real losses with `redo.py` or by hand.
6. `sites.py`, `install.py`. Then work in `parts/<slug>/fr` and `parts/<slug>/solutions/fr` only:
   - Printed English from code and data: `\foreach` label lists (careful: some items are keys), `symbolic x/y coords` and
     the matching coordinates in `\addplot` (translate both consistently, or keep the keys and add `yticklabels`),
     `xticklabels`, legends, node text.
   - Term links (`python3 tools/link_defined_terms.py --book N --lang fr --unwrap --apply`, then `--apply`), curating
     only `tools/term_config/bookN_fr.py` (STOP for French homographs; see "Term linking" in `translation_instruction.md`);
     then `census.py $ARGS`.
   - Gates: `bash tools/check_translation.sh <slug> fr` must PASS; `python3 tools/link_defined_terms.py --book N --lang
     fr --check` must report 0. The `-1word` tiers of the prose gate are advisory: read them.
   - The `parts/` sweeps of step 6.4 for French: lines ending on an elision, doubled words across a line break, stranded
     articles, `\($`, definitions on a bare noun (`\emph{Teneur de marché} est` → `Le \emph{teneur de marché} est`),
     `voir \cref`/`de \cref` without article, headings left in English, names spelled two ways, any decimal comma that
     touches a coordinate. After a bulk sweep, audit labels and paths against English.
   - Two sweeps Book 3 added, both productive: compare each line's length with its English twin (a much shorter line
     is a dropped clause), and the case of each line's first letter with English (a mismatch is a merged or shifted line).
   - Book 3's commonest fixes, worth a sweep each: the non-breaking space before `: ; ? !` (137 lines), decimal commas
     (the book keeps the point), `\cref` articles by the printed noun's gender, "One Quant Book N" left in prose
     (→ livre~N), definitions on a bare noun, missed elisions, singular "le frais".
   - Book 2's lessons: start `tools/term_config/bookN_fr.py`'s STOP from the English config's STOP list (without it
     `pair` linked every *paire de devises*, 99 wrong links); sweep every `\foreach` list and `xticklabels` for English
     months, weekdays and tenors (no gate catches them); after fixing figure labels, re-read the final build's figure
     pages (6 new collisions appeared with no log warning); sentence-initial `\Cref` without article.
   - `\textsuperscript` inside a TikZ `\foreach` label crashed a build ("Giving up on this path"); use babel's
     `\up{er}` there.
7. Build: intermediate builds in `$RUN/build`; the final one with
   `bash ../pilot_translation/build.sh $REPO <entry> $REPO/build`. Exit: 0 errors, 0 undefined, 0 overfull,
   invalid-in-math 0, zero-height 0, missing char 0, nullfont at the English baseline (0), `.fls` = files on disk.
   `pdfsweep.py <english.pdf> <reference.pdf> <french.pdf>`, the reference being a finished edition in another
   language: use `../one-earth-and-space-sciences-book/build/one_earth_and_space_sciences_book_5_university_year_3_fr.pdf`
   (English as its own reference prints 0 by construction; Book 3 found this). The fresh English PDFs are in
   `/tmp/claude-1000/-home-bvirrion-repositories-one-course/d3d089a5-50da-489c-9cdc-e6a812553956/scratchpad/base0/`.
   Figures: `sample.py --repo $REPO --year <slug> --lang fr --pages <page count>`, render those pages at 130 dpi and read
   every figure on them (`OQB_BOOK=N .venv/bin/python tools/figcrop.py` crops one figure); fix collisions and English
   labels, look for the same defect elsewhere, re-read every page you repair.
8. `sample.py $ARGS --n 20 --seed 1 > $RUN/sample.txt`; read the 20 passages against English plus the openings of three
   chapters; write `translation_scores/book_N/fr/translation_score.md` (rows: Overall score with "sampled: 20 passages,
   seed 1, not read in full"; Ship status "**Pilot tier**: gates green; not read sentence by sentence; figures sampled";
   Model, from `post.py`'s `== models` plus yourself as coordinator `claude-opus-5-5`; Canon: the English of Books 1–5
   has had no fresh-reader verification pass and solutions were not recomputed; Tokens: the `all:` line plus your own
   estimate; defects found; every accepted NUMDIFF) and the per-edition run file `sources/TRANSLATION_BOOK_N_FR.md` with
   the same Model line.

**Hard rules.**
- Edit ONLY: `parts/<slug>/fr/`, `parts/<slug>/solutions/fr/`, `tools/term_config/bookN_fr.py`,
  `translation_scores/book_N/fr/`, `sources/TRANSLATION_BOOK_N_FR.md`, `draft/pilot-<slug>-fr/`, and
  `build/<entry>.*`. Everything else is shared with two other agents running now: the English `parts/`, `styles/`,
  `tools/` (other than your term config), `pilot_translation/`, the glossaries, `CLAUDE.md`. **Report** a needed change
  there instead of making it, with the exact file, line and fix.
- **Never run a git command that changes anything** (`checkout`, `restore`, `stash`, `clean`, `reset`, `commit`, `add`).
  Never create a commit. To undo your own edit, rewrite that file.
- Helper scripts and scratch files go in `$RUN/work/`, never in a shared scratchpad.
- Never delete a file in `$RUN/rejected/`. Never use `install.py --overwrite` except on files this same run installed.
- Never wildcard-delete; delete files by name.
- No dataset downloads. No `make test`, `make reproduce` or other repo-wide jobs; `build.sh` allows two full builds
  machine-wide and waits for a slot.
- An error you find in the English (a wrong number, a wrong statement, a broken figure) is reported, not fixed: the
  translation follows the English as it stands.
- Keep your own tool calls lean: several commands per call, long output to files, read only what a step names.

**Report** (your final message, which the user does not see; the main session relays it): pages, the build summary, the
gate results, score, Haiku calls and list price from `post.py`, your coordinator token estimate, the defect classes you
fixed with counts, every English-canon defect and every shared-tool bug you found (file, line, proposed fix), and
anything the pilot doc should learn.

## Close (2026-11-10)

All five editions are done: Book 1 88 (403 pp), Book 2 88 (393), Book 3 87 (354), Book 4 88 (372), Book 5 88 (366).
All are pilot tier (20-passage seeded sample, not read in full), 0/0/0 under TeX Live 2026, `check_translation.sh <slug> fr`
PASSED and linker `--check` clean for each. Haiku: 1,721 calls, $13.3 list. Coordinators (their own estimates): about
$80–115. Nothing committed.

After Book 5 (the last to close), the main session:
- moved Book 5's `$-\$8\,720$`-style amounts after the number (gate 12 accepts `\$` leaving a math span);
- found its own first cleveref fix (`\AtBeginDocument` in `styles/lang/fr.tex`) had run before cleveref defined the
  conjunctions — Book 5's two failed builds — and moved it to `\AddToHook{begindocument/end}`;
- traced the Book 2 index overfull boxes to multicol's last-page balance (`\maxbalancingoverflow`, 12pt), not the
  header, and fixed it in `onequant.sty` ("Index balance": allowance 0 in the index, trial-box warning silenced only
  then). English Books 1–5 rebuilt 0/0/0 with unchanged page counts; their text differs from the pre-port baseline
  only in the date and in the running header of unnumbered pages, where the book title no longer wraps;
- rebuilt all five French books and re-ran every gate.

Open, for the user:
- **"Solution de Exercice N"**: `\omsolutionof{Solution de}` plus a capitalised cref noun with no article. It is in every
  French edition of every series (Earth, chemistry, physics, biology, math: 300–372 per book sampled), so it was left
  as the family convention here. A fix needs a hook that takes the label and supplies *l'exercice*, *la question*,
  *du problème*.
- **cleveref's English "and"** also prints in the math series' French editions (9 in Book 3 alone).
- The HTML reader for the French quant books.
