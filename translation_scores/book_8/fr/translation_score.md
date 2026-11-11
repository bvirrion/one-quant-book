# Translation score: One Quant Book 8, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 8, Strategies I: Equities and Futures (`strategies-1`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-11 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 302 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 6–10, no subagents |
| **Canon** | English not verified: the English of Book 8 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 302 calls, prompt 1683K + cache read 1548K, output 3586K (thinking 2561K), list price $2.14`. Coordinator: shared with Books 6–10, see `sources/TRANSLATION_BOOKS_6-10_FR.md` |
| **Scope** | 29 chapters + 29 solution files, 118 sections; glossary `sources/GLOSSARY_BOOK_8_FR.md` (+ `.run.md`); term config `tools/term_config/book8_fr.py` (108 STOP and 10 DROP entries) |

## Verdict

Fluent strategy-desk French. Momentum, carry, drawdown, pods, nowcast, fade and crowding are kept as a Paris desk keeps
them, and the strategy cards read *fiche de stratégie* throughout. The sample held one calque, *produit de valeur* for the
value product (now *produit value*, as ch. 6 has it), and one bare definition. Tables and figures needed the most work:
French headers made 19 tables overflow, and six figures had collisions.

## Build and gates

- `build/one_quant_book_08_strategies_1_fr.pdf`: 356 pp (English 330). Errors 0, undefined 0, overfull 0, nullfont 0,
  missing characters 0, invalid-in-math 0, zero-height 0, `.fls` 58 / 58 on disk. TeX Live 2026.
- `tools/check_translation.sh strategies-1 fr`: PASSED, gate 12 included. No multi-word finding from the latin prose gate.
- Linker `--check`: every file matches the config.
- Links: fr 720, en 597. Every English target is reached. The one over-frequent target (*stratégie value*, 14 against 1)
  is right-sense: French repeats the full term where English says *value*.
- Census: five index keys and four text runs identical to English, all by design (*s-score*, *pairs trading*, *betting
  against beta*, *nowcast*, the SPAC expansion, and *near*/*far* as subscripts).
- `pdfsweep.py` against the French Book 5 PDF lists code identifiers, source titles and desk English kept by the glossary.

## What was read

- Text: 20 passages (seed 1) and the sweep reports' chapter openings.
- Figures: **every captioned figure (57, on 53 pages)**, on a 12-page contact sheet of the intermediate build. The six
  repaired figures were re-read in the rebuilt PDF, three of them twice.
- NUMDIFF, line by line: 22 lines, every one explained (24-hour times written *15 h 50*, numbers moved to the next line).

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Typography outside math (`~` before `: ; ? !`, `~\%`) | 48 lines | |
| Term drift and agreement | 37 lines (`fix_common.py`) + 4 by hand | *fichier de stratégie* → *fiche de stratégie*, with its articles and adjectives |
| English printed from code or data | 1 figure | Fig. 20.1 asset-class tick labels |
| English role names in `\iqroles{}` | 34 lines | `researcher` → *chercheur* (also 10 lines in Book 6 and 30 in Book 7, found here) |
| English heading left | 1 | ch. 14 `Part I` |
| Definition opening on a bare noun | 21 | `\emph{transactions induites par les flux} … est` → *Les \emph{…} … sont* |
| `\index{}` key broken across a line | 1 | ch. 29 (gate) |
| `\texttt{}` split across a line end | 19 groups | read by the prose gate as English lines |
| Stray article | 2 | ch. 6, ch. 21 |
| Overfull boxes from longer French | 19 tables + 1 legend | ch. 2, 4, 7, 9, 11–15, 17–19, 21, 23, 25, 26 |
| Figure collisions | 6 | Fig. 3.1 (x labels), 7.2 (legend over the y label), 13.1 and 28.2 (legend over the data), 20.1 (tick labels run together), 21.2 (legend over the curve) |
| Calque | 3 sites | *produit de valeur* |
| Midquote as a "median" word (found during Book 10) | 4 | *cours médian(s)* → *prix milieu(x)*, ch. 2 and its solutions |
