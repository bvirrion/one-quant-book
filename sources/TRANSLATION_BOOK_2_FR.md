# One Quant Book 2 (`markets-2`) in French, pilot method

- **Scope:** 31 chapters and 31 solution files, 178 sections. Run brief: `sources/TRANSLATION_BOOKS_1-5_FR.md` (coordinator
  section). Run directory: `draft/pilot-markets-2-fr/` (logs, sweeps and helper scripts in `work/`). Started 2026-11-09,
  run alongside the Books 1 and 3 coordinators in the same tree.
- **Tier:** pilot. Nothing committed.
- **Model:** `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 383 calls (357 translation, 26 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5).
- **Result:** closed 2026-11-10. 392 pp, 0 errors, 0 undefined, 2 overfull (shared index header, finding 1),
  `check_translation.sh markets-2 fr` PASSED, linker `--check` clean, 88/100 sampled (20 passages, seed 1, not read in
  full). Score file: `translation_scores/book_2/fr/translation_score.md`.

## Run

- `run.py --workers 3`: four passes. After pass 1, 13 files held a rejected section; after pass 2, 6; after pass 3, 1
  (ch. 29 section 3, where the model kept stopping at the problem statement); pass 4 cleared it.
- `post.py` (no `--units`), `repair.py` (26 calls), `post.py` again, `sites.py`, `install.py`.
- Term linker: `--unwrap --apply`, then curation of `tools/term_config/book2_fr.py`. The first run gave 2751 links, against
  1388 in English; mirroring the English STOP list and dropping five French collisions brought it to 2011.
- All later fixes in `parts/` were made by script: `work/fix1.py`, `crefart.py`, `typo.py`, `jointt2.py`, `sweep.py`,
  `shift.py`, `lens.py` and `numlines.py`. They are listed by class in the score file.
- Three full builds. The first had 9 overfull boxes, all figures plus the index header; the second had 3. The final build
  has 2, both from the index header.

## Findings for the shared tools (not fixed here; the files are shared)

1. **`styles/onequant.sty`, even-page header of the index (the `\omHeadChapMark\hfill\omHeadBook` page style, lines
   290–321, where `\omHeadChapMark` is truncated against `\omHeadBookWd`)**.
   - Defect: `One Quant Book 2 — Marchés II` wraps onto a third line, past the 41 pt head height. The log shows two
     `Overfull \vbox (9.2pt / 2.2pt too high) has occurred while \output is active` on the index pages, printed
     pp. 382–383.
   - The English build wraps the same header on its p. 363 (`INDEX … One Quant Book 2 — / Markets II`), but its box still
     fits.
   - Fix: set the book half on one line (`\mbox{\omHeadBook}`), or make the index's chapter mark empty or short.
2. **cleveref conjunctions stay English in every French edition.**
   - Defect: `\cref{fig:a,fig:b}` prints `Figures 6.3 and 6.4`. That happens in 24 places in Book 2's PDF and 13 in Book 3's.
   - Cause: `styles/onequant.sty:100` loads `cleveref` without a language option. cleveref reads the class options, not
     babel's package option, and the `\crefname` block (lines 392–420) localises only the names.
   - Fix, either way:
     - (a) in `styles/lang/fr.tex`, add `\AtBeginDocument{\renewcommand{\crefpairconjunction}{ et~}\renewcommand{\crefmiddleconjunction}{, }\renewcommand{\creflastconjunction}{ et~}\renewcommand{\crefpairgroupconjunction}{ et~}\renewcommand{\crefmiddlegroupconjunction}{, }\renewcommand{\creflastgroupconjunction}{ et~}\renewcommand{\crefrangeconjunction}{ à~}}`, with the matching lines in each other `lang/*.tex`;
     - (b) pass `french` to cleveref when the language is French.
3. **`pilot_translation/repair.py` damages lines while its acceptance check passes.** Three cases:
   - it inserted a French meta-comment as a line of solutions 08 (line 91), which displaced the following lines;
   - it dropped a content word (`roll`) at ch. 12:309;
   - it left the CFTC line at ch. 9:298 half English.

   Fix: refuse a reply that adds a line, or whose word count falls well below the English twin's, as is already done for
   the revert-to-English case.
4. **The twin gates disagree on a line-broken `\texttt{}`**, at 16 sites in Book 2. This is the same finding as Book 3's
   finding 3. Workaround: `work/jointt2.py` joins the opening line of the `\texttt` to the prose line before it, and the
   closing line to the prose line after it, which keeps the code twin byte-identical.
5. **`tools/check_orphan_lines.py` flags `omsources` lines.** 15 lines were byte-identical to English: titles of cited
   documents. Workaround: each was joined with the line before it. Fix: skip `omsources` blocks.
6. **The pilot sweeps and the repair prompt miss two `\cref` article patterns:**
   - a sentence-initial `\Cref{fig:…} montre` with no article (7 files);
   - `Dans \cref{dat:…}` and `de \cref{…}` before a noun the pack capitalises.

   `work/crefart.py` handles both by the gender of the printed noun; it could join `sweeps.py`.
7. **Series consistency**: Book 2's access chapters are titled `Accéder aux marchés~: le change`, `… : taux et crédit`.
   The matching "Getting Access" chapters of Books 1 and 3 should read the same way.
8. **`1er`**: Book 2 uses babel's `1\up{er}` (22 sites) and Book 3 uses `1\textsuperscript{er}`. One series rule would be
   better; `\up` is the one that is safe inside TikZ.

## English-canon notes (reported, not changed)

- No factual error was found. Solutions were not recomputed.
- The linker map has no French site for `def:m2:fx-spot-microstructure:skew`. This is not a canon defect: the French
  says *décaler les cotations*.

## For the pilot doc

- The French term config must start from the English STOP list. Without it, `pair` (*au pair*) linked every *paire(s)*
  (99 wrong links), and the first run had twice the English link count.
- Figures with month, weekday or tenor `\foreach` lists and `xticklabels` need a sweep of their own. About 20 figures here
  kept English ticks, and none was caught by a reply check or a gate.
- After every label fix, re-read the final build's figure pages. A French label one word longer collided with a box or a
  heading in 6 figures that had built without any warning.
