# One Quant Book 5 (`derivatives`) in French, pilot method

- **Scope:** 28 chapters and 28 solution files, 140 sections. Run brief: `sources/TRANSLATION_BOOKS_1-5_FR.md` (coordinator
  section). Run directory: `draft/pilot-derivatives-fr/` (logs, sweeps and helper scripts in `work/`). Started 2026-11-10,
  run alongside the Books 1 and 4 coordinators in the same tree.
- **Tier:** pilot. Nothing committed.
- **Model:** `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 241 calls (235 translation, 6 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5).
- **Result:** closed 2026-11-10. 366 pp, 0/0/0, `check_translation.sh derivatives fr` PASSED, linker `--check` clean,
  88/100 sampled (20 passages, seed 1, not read in full). Score file: `translation_scores/book_5/fr/translation_score.md`.

## Run

- `run.py --workers 3` took two passes. Pass 1 left 5 files with a rejected section: s03, ch. 4 s1, ch. 12 s2 and s5,
  ch. 21 s4, ch. 22 s3. Pass 2 cleared all of them: 56 of 56 files written, 0 rejected, 0 failed calls.
- Then `post.py` (no `--units`) and `repair.py` (6 flagged lines). Repair refused the ch. 18 code line, fixed the ch. 2, s06
  and s15 titles, and left ch. 7 and 25 unchanged. Every heading it touched was checked by hand, and all were right.
- Then `post.py` again, `sites.py` and `install.py`.
- All later fixes were made in `parts/` by script or by hand: `work/typo5.py`, `sweep.py`, `shift.py`, `numlines.py`,
  `crefart1.py`, `lens90.py`, `figfix.py`. They are listed by class in the score file.
- Term links: STOP seeded from `book5_en.py` through the run glossary (`work/seedstop.py`), plus 4 entries by hand (Covenant,
  Floor, Linker, Strip).
- Figures: a two-column contact sheet of all 113 captioned figures (`work/sheet/mk2.py`, built in LaTeX because the machine
  has no PIL or ImageMagick) found 5 collisions or overruns that no gate sees.

## Findings for the shared tools (not fixed here; the files are shared)

1. **`styles/lang/fr.tex:26` `\newcommand{\omsolutionof}{Solution de}` prints "Solution de Exercice 28.4" and "Solution de
   Question d'entretien 3.2"** (via `styles/onequant.sty:465` `\textbf{\omsolutionof~\cref{#1}}`), in every French book.
   Fix: `\newcommand{\omsolutionof}{Solution~:}`, which prints "Solution : Exercice 28.4". Alternatively, give the lang file
   the whole line, e.g. a `\omsolutionline{#1}` hook so that French can write `Solution de l'\cref{#1}`.
2. **Index overfull `\vbox` (9.2pt, last index page) — resolved by the main session's `onequant.sty` patch of 2026-11-10
   02:41** (`\maxbalancingoverflow=\z@` in the index). Before it, the overfull reproduced in a small test
   (`work/hdrtest/c.tex`, with the real `.ind`). `\setcounter{collectmore}{-2}` or `\indexsetup{othercode=\small}` also
   cleared it, while `\raggedcolumns`, `finalcolumnbadness` and `collectmore=2` did not. The final build has 0 overfull; the
   index now takes one more page (366 against 365).
3. **The first build after that patch died at `\begin{document}` with `Command \crefpairconjunction undefined`, twice**
   (the hook in `styles/lang/fr.tex:120`). A fresh output directory built cleanly on both passes, and so did `build/` once
   this book's `.aux .out .toc .fdb_latexmk` were deleted by name. The first failure most likely read the style file while it
   was being written, and left a 104-byte `.aux` that kept the next build failing. Lesson: when a build fails at
   `\begin{document}` just after a shared style changed, delete the book's state files by name before debugging.
4. **Gate 12 now freezes math spans, so `$-\$8\,720$` (English amount style inside math) cannot become `$-8\,720$~\$`**
   (ch. 26:203–204). Either the gate allows a currency move out of math, or the English canon puts the minus outside
   (`$-$\$8\,720`).

## English-canon notes (reported, not changed)

- None found; solutions were not recomputed.

## For the pilot doc

- **Glossary gaps cost the most here.**
  - Haiku translated *strip* (of options) as *panier* 44 times, a homonym of *basket*, which this book also uses.
  - It wrote *sourire* and *smile* side by side (98 to normalise).
  - It wrote *contrat à terme* for *forward* through ch. 5 (title included) and *cours à terme* in ch. 28.
  - It gave five renderings of *the miniature firm* and *valorisateur* for *pricer*.
  - The series glossary should fix *strip*, *smile*, *forward* vs *future*, *pricer* and *the firm*.
- **A typography sweep must mask math, solution keys and `\texttt`.** The first version put `~` into 420
  `\begin{solution}{exo:…}` keys, which failed the keys check in all 28 solution files; they were restored by script.
- **Do not join a `\texttt{}` broken across lines** (it shifts the line count that every per-line sweep relies on). Move the
  break before `\texttt` instead.
- **Read every figure, not a page sample.** `sample.py --pages` reaches a handful of figures; the contact sheet of all 113
  found Fig. 5.4's labels over its boxes and 24.3's y-label in the next panel. Neither shows in the log.
- **Long French axis labels**: when a French y-label is longer than the plot height in a `groupplot`, shorten it with
  abbreviations (*pts de vol.*) rather than widening `horizontal sep`, which risks an overfull line.
- **Inline formulas at a line end** cause most of the remaining overfulls. A small test document with only the paragraph and
  the real style (`work/hdrtest/p*.tex`) settles a rewording in seconds instead of a 4-minute book build.
- Repair touched only titles in this book, and all were right; the Book 4 warning (`\section{Interview questions}` →
  *Exercices*) did not recur.
