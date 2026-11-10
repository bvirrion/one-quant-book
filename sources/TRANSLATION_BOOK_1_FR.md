# One Quant Book 1 (`markets-1`) in French, pilot method

- **Scope:** 31 chapters and 31 solution files, 200 sections. Run brief: `sources/TRANSLATION_BOOKS_1-5_FR.md` (coordinator
  section). Run directory: `draft/pilot-markets-1-fr/`, with logs and helper scripts in `work/`. Started 2026-11-09 and run
  alongside the Books 2 and 3 coordinators in the same tree.
- **Tier:** pilot. Nothing committed.
- **Model:** `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 546 calls (526 translation, 20 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5).
- **Result:** closed 2026-11-10.
  - 403 pp, 0 errors, 0 undefined, 0 overfull, `.fls` 62 / 62.
  - `check_translation.sh markets-1 fr` passes except one false positive (quant twin, finding 2). Linker `--check` is clean.
  - Score: 88/100, sampled (20 passages, seed 1, not read in full). Score file:
    `translation_scores/book_1/fr/translation_score.md`.

## Run

- `run.py` took six passes (`run1.log`–`run6.log`). Most of the later passes went on two kinds of section:
  - Sections refused for "left in English" because of `yticklabels from table={figdata/...}{label}` (finding 1).
    `work/accept.py` accepts a reply only when every flagged line is such a line.
  - Interview-answer sections in solutions 20 and 31, where Haiku merged long paragraphs and dropped lines on every
    retry. `work/realign.py` realigned them on the English skeleton (blank lines, `\begin`/`\end`, `\iqlookfor`
    blocks).
- Then, in order:
  - `post.py`;
  - `repair.py` (20 calls). Only the tail of its log survives (finding 5);
  - `post.py` again;
  - `sites.py`;
  - `install.py`.
- Term linker: `--unwrap --apply` gave about 5800 links against 1714 in English. The English STOP terms were mirrored in
  French in `tools/term_config/book1_fr.py`, with both cases. `action(s)` and `ordre(s)` were DROPped. The result is 2285
  links on 167 targets.
- Later fixes in `parts/` were made by script. They are listed by class in the score file.
  - From Book 2 and Book 3, retargeted: `work/jointt2.py`, `b3_sweep.py`, `b3_shift.py`, `b3_numlines.py`.
  - Written for this run: `figfix.py`, `punct.py`, `crefart.py`, `fixes1-3.py`, `dollars.py`.
- Seven full builds: five intermediate builds in `draft/pilot-markets-1-fr/build/`, then two final builds into `build/`
  because of the fig. 29.1 re-reads.
  - Build 1 died on `1^er août` (ch. 10).
  - Build 2 had 10 overfull boxes, all of them figures and tables.
  - Builds 3 onwards are 0/0/0.
- Figures:
  - The 11 figure pages of the seeded 40-page sample were read first.
  - Then every captioned figure in the book (106) was read on contact sheets (`work/sheet/mk.py`). These crop each figure
    with its caption and render them two to a page at 140 dpi.
  - That pass found 23 figures with a collision, a clipped label or a wrong label, and none of them had a log warning.
    All were fixed, and every repaired figure was read again on the final build.

## Findings for the shared tools (not fixed here; the files are shared)

1. **`pilot_translation/common.py`, `visible()` (line 211).**
   - Defect: `visible()` does not blank `yticklabels from table={figdata/...}{label}`. The path words in it read as
     English, so a correct reply is refused as "left in English". This happened at 01:328, 02:226, 07:144, 07:230,
     10:163 and 12:278, and cost retry passes.
   - Fix: add `from table` to the first `re.search` that returns `''`, or strip `\{[^{}]*figdata/[^{}]*\}` before the word
     test.
2. **`tools/id_apply.py`, `code_args` (line 556–561), against `tools/check_orphan_lines.py` and the dup tier of
   `tools/check_latin_prose.py`.**
   - Defect: the twin compares `\texttt` contents raw, newlines included. The English
     `\texttt{MarketRules(market, valid\_from, ...,\nlimit\_up, ..., settlement\_days,\ntax\_buy, tax\_sell)}` (ch. 12
     around line 342) has a middle line of pure code, so keeping its newlines fails the orphan and dup gates. Joining the
     argument fails the twin on whitespace alone.
   - Fix: normalise whitespace in the twin, at line 561:
     `[("texttt", " ".join(x.split())) for x in TEXTTT.findall(t)]`. The alternative is to have the orphan and dup gates
     skip continuation lines of an unclosed `\texttt`.
   - This edition keeps the joined form, and the twin FAIL that remains is this false positive.
3. **`tools/check_latin_prose.py`, `\foreach` tier (lines 345–366).**
   - Defect: the tier blocks a slash list of node names. The ch. 16 lending-chain figure has `{own/agent, ...}`, which
     pairs node names with node names and prints nothing.
   - Worked around here by renaming a node to `(lend)`.
   - Fix: also skip a slash list whose every field is a bare identifier.
4. **`pilot_translation/repair.py`, `\cref` article repairs.**
   - Defect: the repair prompt does not know which noun each prefix prints. Its repairs gave `dat` (Encadré) *du*
     (04:82, 04:396, 11:341) and `fig` *l'* (19:267). They also wrote *voir au* (08:34, 08:73) and dropped *niveau de*
     (24:302).
   - Fix: pass the prefix-to-noun-and-gender table (`ch` le, `fig`/`prop`/`def`/`met`/`rem`/`sec` la, `dat`/`ex`/`exo`
     l', `tab`/`lst`/`pb` le) into the repair prompt.
   - Also refuse a repair that removes a non-article word.
5. **Pilot doc (`pilot_translation_instruction.md`), repair step.**
   - Say "tee the full `repair.py` output to `repair.log`". A tail-only copy loses the record of what the repair changed.
   - Here the diff had to be rebuilt from the sections JSON (`work/repairdiff.txt`).
6. **Pilot doc, run step.** Haiku merges and drops lines in long interview-answer paragraphs, and retrying does not help.
   A skeleton realigner like `work/realign.py` belongs in `pilot_translation/`.
7. **Pilot doc, sweeps.** Three sweeps were productive here and are missing from the list:
   - doubled currency, `\$200$ millions de dollars` (72 hits);
   - `5\%` with no space (351 hits);
   - every captioned figure on a contact sheet. The seeded sample showed 11 figure pages, and the full sheet found 23
     defective figures, none of them in the log.

## English-canon notes (reported, not fixed)

- `parts/markets-1/30-getting-access-futures-options.tex` around line 21: `\index{clearing\nmember}`. The index key is broken
  across a line. Fix: join it onto one line. It prints right, but it is fragile in every translation.
- `parts/markets-1/21-basis-roll-and-delivery.tex` around line 259: `\index{basis trade at index\nclose}`. This is the same
  defect, with the same fix.
- `parts/markets-1/12-asian-and-emerging-equity-markets.tex` lines 342–344: the three-line `\texttt{MarketRules(...)}` (see
  finding 2). Fix: put the whole `\texttt{MarketRules(...)}` on one source line. Any newline inside the argument leaves a
  continuation line that is pure code.
- No wrong number or statement was found in the English during the sample or the figure pass. Solutions were not
  recomputed.
