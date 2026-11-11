# Translation score: One Quant Book 9, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 9, Strategies II: Volatility, Relative Value, Macro and the Bank Desks (`strategies-2`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-11 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 243 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 6–10, no subagents |
| **Canon** | English not verified: the English of Book 9 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 243 calls, prompt 1306K + cache read 1162K, output 2811K (thinking 2050K), list price $1.68`. Coordinator: shared with Books 6–10, see `sources/TRANSLATION_BOOKS_6-10_FR.md` |
| **Scope** | 29 chapters + 29 solution files, 116 sections; glossary `sources/GLOSSARY_BOOK_9_FR.md` (+ `.run.md`); term config `tools/term_config/book9_fr.py` (108 STOP and 10 DROP entries) |

## Verdict

Fluent French for volatility, relative-value and bank desks. Skew, straddle, butterfly, basis, carry, crack, spoofing and
mark-out are kept as the desks keep them. The sample held three defects, all fixed: *sous-évaluation* for *mispricing* (a
one-sided word for a two-sided error; now *erreur de prix*, with a double negative in the same chapter), *entre deux roll*, and
*livre de base* for the basis book in ch. 11 (a "basic book"; now *book de basis*, as the rest of the chapter has it).
Tables needed the most work: French headers made 18 of them overflow.

## Build and gates

- `build/one_quant_book_09_strategies_2_fr.pdf`: 356 pp (English 333). Errors 0, undefined 0, overfull 0, nullfont 0,
  missing characters 0, zero-height 0, `.fls` 58 / 58 on disk. TeX Live 2026. **invalid-in-math 2, at the English baseline**:
  `\euro` inside math in s28:4, kept so that gate 12's math comparison holds (reported as an English-canon defect).
- `tools/check_translation.sh strategies-2 fr`: PASSED, gate 12 included. The first run failed the twin-comparison prose
  gate on three fragments identical to English (`(points)` in an axis label, `call OI`/`put OI` in a sum); fixed.
- Linker `--check`: every file matches the config.
- Links: fr 336, en 262. Every English target is reached (one, *rendement d'option couverte en delta*, by a hand link in an
  exercise). The over-frequent targets are right-sense: French repeats the full term.
- `pdfsweep.py` against the French Book 5 PDF lists code identifiers, source titles and desk English kept by the glossary.

## What was read

- Text: 20 passages (seed 1) and the sweep reports.
- Figures: **every captioned figure (57, on 53 pages)**, on a 12-page contact sheet of the intermediate build. The six
  repaired figures were re-read in the rebuilt PDF.
- Numbers: per file, as multisets (`draft/pilot-quant-fr/numfile.py`, new: the line-by-line check is noise once table
  fixes shift lines). Every number English has and French lacks was read: numbers written as words (*cinquante fois*,
  *la huitième année*, *à un mois*) and clock times (*15 h 30*).

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Typography outside math (`~` before `: ; ? !`, `~\%`) | 92 + 147 | |
| Term drift and agreement | 47 lines (`fix_common.py`) | *fichier de stratégie* → *fiche de stratégie*, *sourire* → *smile* |
| Decimal comma | 4 lines | *2,60~\$* |
| A sweep's own false hit | 1 | `xtick={1,2,3,4,5}` read as decimal commas; restored, and `fix_common.py` now skips tick and coordinate lists |
| English printed from data | 1 figure | Fig. 4.1 rule names from the CSV's `rule` column, now mapped through `\pgfkeys` |
| English role names in `\iqroles{}` | 74 lines | `researcher` → *chercheur* |
| English headings | 4 | ch. 25 `Part I --- Pooling.` … |
| Weekend-problem part labels in six forms | 38 lines | one form: *Programmation.*, *Trouver la faille.* (`wkend_labels.py`, also run over Books 6–8) |
| English quotes in French prose | 2 | ``` ``L'ETF … '' ``` → *«~L'ETF … ~»* |
| Definition opening on a bare noun | 13 | `\emph{Corrélation réalisée} est` → *La \emph{corrélation réalisée} est* |
| `\texttt{}` split across a line end | 9 groups | |
| Stranded article | 2 | *contre le / l'indice* |
| Term link missed | 1 | *rendement d'option couverte en delta* (exercise) |
| Overfull boxes from longer French | 18 tables | ch. 1, 4 (×2), 5, 7, 9, 10, 12, 17, 18, 22 (×2), 23–27, 29 |
| Figure collisions | 6 | Fig. 4.1 (label out of the axis), 18.1 (`( %)`), 21.2 (legend over the curve), 22.2 and 29.2 (tick labels run together), 26.1 (y label longer than the axis) |
| Sense (sample) | 3 | see the verdict |
| Midquote as a "median" word (found during Book 10) | 1 | *prix médian* → *prix milieu*, ch. 24 |
