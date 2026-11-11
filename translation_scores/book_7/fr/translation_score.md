# Translation score: One Quant Book 7, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 7, Research Craft (`research`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-11 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 280 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 6–10, no subagents |
| **Canon** | English not verified: the English of Book 7 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 280 calls, prompt 1761K + cache read 1303K, output 4048K (thinking 3067K), list price $2.39`. Coordinator: shared with Books 6–10, see `sources/TRANSLATION_BOOKS_6-10_FR.md` |
| **Scope** | 29 chapters + 29 solution files, 123 sections; glossary `sources/GLOSSARY_BOOK_7_FR.md` (+ `.run.md`); term config `tools/term_config/book7_fr.py` (106 STOP and 10 DROP entries) |

## Verdict

Fluent research French in the register of a quant team in Paris (backtest, holdout, drawdown, turnover and mark-out are kept
in English). There are calques here and there: *le rang IC* for *rank IC* (fixed book-wide to *l'IC de rang*), and *sa
$t$-statistique*. The sample held nothing worse. Tables and figures needed the most work: French headers made 18 tables and
captions overflow, and ten figures had labels collide.

## Build and gates

- `build/one_quant_book_07_research_fr.pdf`: 370 pp (English 345). Errors 0, undefined 0, overfull 0, nullfont 0, missing
  characters 0, invalid-in-math 0, zero-height 0, `.fls` 58 / 58 on disk. TeX Live 2026.
- `tools/check_translation.sh research fr`: PASSED, gate 12 included. Advisory one-word tiers: 7 hits. One is the company-name
  tick list of Fig. 11.2, identical to English by design; the others are cognates (*exploration*, *session*, *minutes*).
- Linker `--check`: every file matches the config.
- Links: fr 1,408, en 1,306. Every English target is reached. The over-frequent targets are right-sense: *échantillon réservé*
  goes to the pre-registration/holdout definition it belongs to, and full-term repeats account for the rest.
- `pdfsweep.py` against the French Book 5 PDF lists code identifiers, source titles and desk English kept by the glossary.

## What was read

- Text: 20 passages (seed 1) and the openings of chapters 1, 13 and 24 (in the sweep reports).
- Figures: **every captioned figure (87)**, on a contact sheet of the intermediate build (19 pages). The ten repaired figures
  were re-read in the rebuilt PDF, three of them twice.
- NUMDIFF, line by line: every difference explained. They were numbers written in words (*septième année*, *le premier
  mars*, *retard nul*) and numbers moved to the next line.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Typography outside math (`~` before `: ; ? !`, `~\%`) | 95 lines | |
| Doubled currency, `\$` kept beside *dollars*, and `5\%` | 5 + 105 | `$A = \$2.3$ millions de dollars` |
| Decimal comma | 2 lines | `0,10` |
| English printed from code or data | 4 figures | Fig. 3.1 months (`\foreach`), 25.3 and 26.1 symbolic coordinates, 9.4 axis label |
| English heading left | 1 | ch. 24 `Weekend problem --- a model that did not know` (now caught by `extra_report.py`) |
| Definition opening on a bare noun | 15 + 8 lowercase (found during Book 8) | `\emph{Biais de survie} est` → *Le \emph{biais de survie} est* |
| `\index{}` key broken across a line | 4 | ch. 6, 7, 8, 18 (gate) |
| `\texttt{}` split across a line end | 5 | read by the prose gate as English lines (ch. 4, 17, 23, 27, 28) |
| English line left beside its translation | 1 | s20 *do not share.* |
| Term link missed | 2 | *Lambda de Kyle* (bare and capitalised), *parité de rejeu* |
| Overfull boxes from longer French | 20 | 15 tables (headers, `l` columns), 2 legends, 3 prose lines |
| Figure collisions | 10 | Fig. 2.1, 3.4, 5.2, 6.2, 8.2, 9.1, 15.2, 16.1 (text out of its boxes), 23.1, 25.1 |
| English role names in `\iqroles{}` | 30 lines (found during Book 8) | `researcher` → *chercheur* |
| Calque | 6 sites | *rang IC*, *$t$-statistique* |
