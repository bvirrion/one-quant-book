# One Quant Book 4 (`methods`) in French, pilot method

- **Scope:** 29 chapters and 29 solution files, 138 sections. Run brief: `sources/TRANSLATION_BOOKS_1-5_FR.md` (coordinator
  section). Run directory: `draft/pilot-methods-fr/` (logs; sweeps, fix scripts and the figure contact sheet in `work/`).
  Started 2026-11-10, alongside the Books 1 and 2 coordinators in the same tree (both closed during the run; their wave
  findings were applied here).
- **Tier:** pilot. Nothing committed.
- **Model:** `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 278 calls (265 translation, 13 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5).
- **Result:** closed 2026-11-10. 372 pp, 0/0/0, `check_translation.sh methods fr` PASSED, linker `--check` clean, 88/100
  sampled (20 passages, seed 1, not read in full). Score file: `translation_scores/book_4/fr/translation_score.md`.

## Run

- `run.py --workers 3`: four passes. Pass 1: 10 files with a rejected section (ch. 5, 6, 8, 12, 14, 17, 19, 25 and s10,
  s15); pass 2: 2 (ch. 5 sections 2 and 3, ch. 6 section 4); pass 3: ch. 5 sections 2 and 3 again, three tries each.
  Both were saved from their last reply by `work/fix05.py` with every check re-run: section 3 needed two lines put back
  (a `\texttt` that lost its `\_` escapes, a question whose math spans were reordered); section 2 holds a TikZ `matrix`
  of text cells (the numeraire table), which the draw check forbids the model to change and the English check forbids it
  to leave, so it was saved with the cells in English (the only check overridden) and translated by hand in `parts/`.
  Pass 4 assembled ch. 5 with no call.
- `post.py` (no `--units`), `repair.py` (13 calls; output in `repair.log`), `post.py` again, `sites.py`, `install.py`;
  then every fix in `parts/` by script: `work/fixA.py` (hand fixes, index keys, elisions, bare definitions, `\Cref`),
  `fixB.py` (cref genders), `fix2.py` (typography, now skipping display math), `fixC.py` (percent, title case), `fixE.py`
  (ordinals), plus a handful of `sed` lines for the figure fixes. `work/recheck.py` re-runs the pilot's own reply checks
  (math, labels, environments, code) on the installed files: only the three intended drawing changes differ.

## Findings for the shared tools (not fixed here; the files are shared)

1. **`pilot_translation/repair.py` changes headings to the wrong heading.** Asked to translate ch. 1:577
   `\section{Interview questions}` (flagged "title left in English"), it returned `\section{Exercices}`, and its acceptance
   check passed. Fix: for a `\section`/`\chapter` line, accept only a reply whose title is the glossary's or the pack's
   rendering of a fixed heading (`Interview questions` → `Questions d'entretien`, `Exercises` → `Exercices`), or refuse a
   reply that duplicates another heading of the same file.
2. **`repair.py` still gets `\cref` genders wrong**: `du \cref{prop:…}` for a *Proposition* (ch. 10:346), as Book 1 saw.
   Fix: give the repair prompt the gender table of the series card, or post-check `du|au` before `prop|fig|def|sec|met`.
3. **A TikZ `matrix of nodes` holding prose cannot be translated by the run**: the draw check (`common.py`, the `draw`
   census "outside the !draw ranges") rejects any change to the cells, and the English-left check rejects leaving them.
   Ch. 5 section 2 failed three passes on this alone. Fix: treat lines between `\matrix[…] (m) {` and `};` like node text
   (blank their visible words in the draw census), or list such lines in `sites.py` and exempt them from the English check.
4. **No gate compares math after install.** `check_translation.sh` checks code, labels and environments but not the
   ordered math spans; `fix2.py`-style typography sweeps (Book 3's, reused here) put `~:` and `~;` inside `$…$` three times
   (`\#\{i~: X_i\}`, `\E[Z^2~; |Z| \le c]`, `I(X~; Y)`) and inside `\[…\]` until the script learnt to skip display math.
   Found only because this run re-ran `common.check` on the installed files (`work/recheck.py`). Proposed gate 13: run
   `common.check`'s `math` census on `parts/<year>/<lang>` against English.
5. **Shared-sweep regex trap.** A naive `\$…\$` span regex pairs the `$` of `\$` (as in `200~\$`) and reports phantom
   math differences; any math census must use `(?<!\\)\$`.
6. **`\iqroles{…}` prints English role names** (*trader, researcher, bank, developer, risk*) in every French edition
   (Book 3's PDF has 32 *researcher*). Fix: map the roles in `styles/lang/fr.tex` (`\iqroles` could look up
   `\omrole@<name>`), or decide they stay as desk English.
7. **Monitor trap (coordinator side):** `pgrep -f "year methods --lang fr"` inside a wait loop matches the loop's own shell,
   so the loop never ends; match `^python3 run.py` or wait on the PID instead.

## English-canon notes (reported, not changed)

- None found that is a factual error; solutions were not recomputed. Fig. 1.1 labels the outcomes `HH`, `HT`, `TH`, `TT`
  (heads/tails), left as is in French.

## For the pilot doc

- A math-heavy book translates well under this method: 265 translation calls for 138 sections, and the math came back
  byte-identical everywhere the reply checks ran. The risk moved to the coordinator's own sweeps (point 4 above).
- Book 1's "contact sheet of every figure" paid again: it found 2 collisions, an English legend (*normal inverse Gaussian*),
  English axis labels (Fig. 18.1) and three inconsistencies (*ECB*, *germe*, *1-2-1*) that the sampled pages did not hold.
- The line-length-ratio sweep found two dropped clauses (s05, ch. 24) and two merges (ch. 7, 16) that no reply check saw;
  the case-of-first-letter sweep found nothing new in this book.
