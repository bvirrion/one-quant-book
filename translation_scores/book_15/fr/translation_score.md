# Translation score: One Quant Book 15, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 15, Research, Data and Risk Platforms (`platforms`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 314 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 11–15, no subagents |
| **Canon** | English not verified: the English of Book 15 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 314 calls, prompt 1891K + cache read 1669K, output 3973K (thinking 2979K), list price $2.38`. Coordinator: shared with Books 11–15, see `sources/TRANSLATION_BOOKS_11-20_FR.md` |
| **Scope** | 30 chapters + 30 solution files; glossary `sources/GLOSSARY_BOOK_15_FR.md` (+ `.run.md`); term config `tools/term_config/book15_fr.py` |

## Verdict

Fluent technical French for data and risk platforms: *base de ticks*, *données de référence*, *résolution des symboles*,
*lignage*, *mise en quarantaine*, *jointure as-of*, *élagage des partitions*, *report des prédicats*, *base bitemporelle*,
*temps de validité* / *temps système*, *boîte d'envoi transactionnelle*, *rapprochement*, *astreinte*, *vitesse de
consommation* (burn rate), *menace interne*. Library and format names stay as written (DuckDB, Polars, Parquet, Arrow,
pybind11), and desk English is kept where the trade keeps it (*notebook*, *pipeline*, *spot*, *batch*, *feed handler*).
The sample held five slips, all fixed: Rust *crates* rendered as *caisses*, an *insider* as *un salarié* (now *un
initié*, as the rest of ch. 29 has it), a Kafka *offset* as *décalage* next to *position du consommateur* (the
glossary form), an exercise in English-style double quotes, and imperatives (*Donnez*, *relancez*) where the series
writes infinitives. Three chapter openings (chs. 9, 18, 23) held one more, *le agrégateur*: a missing elision across a
line break, which turned out to be a series-wide class (below). Residual: offsets are *position du consommateur* in
running text and *offset* in two solution items; the firm is *la société* and *la firme* both.

## Build and gates

- `draft/pilot-quant-fr/build-s1/one_quant_book_15_platforms_fr.pdf`: 395 pp (English 367). Errors 0, undefined 0,
  overfull 0, nullfont 0, missing characters 0, invalid-in-math 0, zero-height 0, `.fls` 60/60. TeX Live 2026. Final build
  into `build/` at the close of session 1: 395 pp, 0/0/0.
- `tools/check_translation.sh platforms fr`: PASSED, gate 12 included. Book 15's identifier block in
  `tools/check_latin_prose.py` allows chart and table tokens (`duckdb`, `polars`, `sym`, `bid`, `ask`, …) and the
  series colour names in a `\foreach` list (`omDef`, `omMeth`, …; the allow list is case-sensitive).
- Linker `--check`: every file matches the config. Links: fr 922 (652 course + 270 solutions), en 702.
- `pdfsweep.py` against the French Book 10 PDF: the top English-only word types are product and format names
  (*duckdb*, *parquet*, *polars*, *sqlite*, *ctypes*, *pybind*), code identifiers from listings (*symbol*, *valid*,
  *known*, *dtype*, *asof*) and desk English kept (*spot*, *notebook*, *pipeline*, *cloud*, *roofline*). It found
  *pages* for alerts three times in the ch. 28 solutions; now *alertes*.

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 9, 18, 23), the sweep reports.
- Figures: **every captioned figure (110)**, on a 25-page contact sheet; every repaired figure re-read, cropped from the
  rebuilt PDF, twice for Figs. 2.1, 4.1, 5.4, 13.2, 15.3, 16.1 and 22.3.
- Numbers: per line in the run directory (`numrun.py`) before install, then per file (`numfile.py`) after; every
  remaining difference is a figure coordinate, a column width, an inline table that replaced a CSV column, a clock time
  written the French way (*14~h~40* for *2:40 in the afternoon*), or a number written as a word (*les cent*, *une
  trentaine*).

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Figure collisions and overflows | 38 figures | French labels wider than the English layout: nodes broken onto two or three lines and spread, long y labels cut to the plot's height (*âge maximal (s, log)*), legends to one column (`figfix.py`, ten passes) |
| English figure text | 90 `sites` lines | `figfr.py`, 33 substitutions: tick-label lists in the CSV's row order, frame headers, *one transaction* in Fig. 24.4 |
| Symbolic coordinates translated by Haiku | 4 figures | chs. 11, 12, 15, 21: the CSV keys must stay English, the French goes in `xticklabels`/`yticklabels` |
| Stray `=` line in a display | 1 here, 50 series-wide | `eqline_fix.py`, run over every French book |
| Units | 42 series-wide, plus Book 15's figures | *GB/s* → *Go/s*, *MB* → *Mo* |
| Clock times | series-wide | `clock_fr.py`; `typo_apply.py` had put a `~` before the seconds of a timestamp (fixed in the script) |
| Wrong-sense rendering | 3 | Rust *crates* as *caisses*; Kafka *offset* as *décalage*; *insider* as *salarié* |
| Missing elision at a line break | 3 here, 37 series-wide | *le agrégateur*, *la action*, *Le expected shortfall* (`elision_fr.py`); three were dropped words (*la* ‹spirale› *a besoin*) |
| Imperative for infinitive | 13 here, 36 series-wide | *Énoncez le résultat nommé* → *Énoncer* (`imperative_fr.py`) |
| Overfull boxes | all | twelve tables re-specified, four hyphenations, legends, TikZ widths, `biblio\-thèque` (the first word of a cell never hyphenates) |
| Calque | 7 | *épisodes plantés* (planted) → *insérés* |

## English-canon defects (reported, not fixed)

None found in the sampled passages.
