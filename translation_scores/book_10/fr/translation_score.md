# Translation score: One Quant Book 10, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 10, Microstructure and Execution (`microstructure`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-11 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 359 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 6–10, no subagents |
| **Canon** | English not verified: the English of Book 10 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 359 calls, prompt 2169K + cache read 2005K, output 3924K (thinking 2589K), list price $2.42`. Coordinator: shared with Books 6–10, see `sources/TRANSLATION_BOOKS_6-10_FR.md` |
| **Scope** | 28 chapters + 28 solution files, 114 sections; glossary `sources/GLOSSARY_BOOK_10_FR.md` (+ `.run.md`); term config `tools/term_config/book10_fr.py` (110 STOP and 10 DROP entries) |

## Verdict

Fluent French for order books, execution and market structure. The desks' English is kept where the desks keep it:
*mid*, *slippage*, *maker-taker*, *iceberg*, *algo wheel*, *mark-out*. The sample held one term defect that ran through
the book: the mid price came back as *point médian* (chs. 5, 6, 25, 26) or *cours médian* (seven files), which are
"median" words in French. All of these now read *prix milieu*, as in Books 1–9. The sample also held three small
wording fixes. Book 10 had the most repairs of the five books: 359 calls for 114 sections, against 243–313 for the
others. One line came back in English and was split into French by hand (ch. 16:370).

## Build and gates

- `build/one_quant_book_10_microstructure_fr.pdf`: 327 pp (English 303). Errors 0, undefined 0, overfull 0, nullfont 0,
  missing characters 0, zero-height 0. TeX Live 2026.
- `tools/check_translation.sh microstructure fr`: PASSED, gate 12 included. The first runs failed on three index keys
  broken across a line end (`index_join.py`, new) and on accent escapes (now UTF-8).
- Linker `--check`: every file matches the config.
- Links: fr 1,017, en 720. The over-frequent targets are right-sense: *pas de cotation*, *ordre enfant*, *algo wheel*.
  French repeats the full term.
- `pdfsweep.py` against the French Book 5 PDF lists code identifiers (`file`, `exchsim`, `agentmkt`), proper names
  (Almgren, Chriss, Kyle, Glosten), desk English kept by the glossary, and French words that are spelt as in English
  (*patient*, *suspension*, *population*).

## What was read

- Text: 20 passages (seed 1) and the sweep reports.
- Figures: **every captioned figure (70)**, on a 22-page contact sheet of an intermediate build. Each repaired figure was
  re-read, cropped, in the rebuilt PDF.
- Numbers: per file, as multisets (`numfile.py`). Every number English has and French lacks was read: numbers written as
  words (*un million*, *d'une minute et de cinq minutes*, *premier août*), clock times (*15 h 50*), and one heading
  coordinate moved in Fig. 2.2.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Typography outside math (`~` before `: ; ? !`, `~\%`) | 174 lines | |
| Term drift and agreement | 28 lines (`fix_common.py`) | |
| Mid price as a "median" word | 4 + 7 files | *point médian*, *cours médian* → *prix milieu* |
| English role names in `\iqroles{}` | 92 lines | `researcher` → *chercheur* |
| Weekend-problem part labels | 32 lines | *Programmation.*, *Trouver la faille.* |
| English headings | 7 | *Exercises* (chs. 10, 23), the ch. 10 weekend title, Part titles in chs. 10, 12, 13, 16, 22 |
| English line left in a section | 1 | ch. 16:370 |
| Duplicated line | 1 | ch. 10:162–163 |
| `\cref` without its article | 3 | *La \Cref{fig:…}* at a sentence start |
| Definition opening on a bare noun | 5 | ch. 18, mid-line: *L'\emph{évanouissement…}* |
| `\texttt{}` split across a line end | 11 groups | |
| `\index{}` key split across a line end | 3 | `index_join.py` (new) |
| Stranded article | 3 | ch. 6:144, 10:67, 24:16 |
| Prose fragments identical to English (gate) | 7 | *noise* → *bruit*, legends in chs. 6, 11, 19, 28, *impact (en ticks)* |
| Names without accents | 2 | *Tóth*, *Lempérière* (ch. 11:202) |
| Overfull boxes from longer French | 7 | tables in chs. 16 (×2), 18, 21, 25; ch. 2 TikZ text; one `\texttt` at a line end in ch. 19 |
| Figure collisions | 6 | Figs. 1.1, 2.2, 7.1, 14.1, 15.2, 28.1 |
| Sense (sample) | 4 | the mid price, *avec une heure devant soi* → *à une heure de la clôture*, a question turned round in ch. 19 |

## English-canon defects (reported, not fixed)

- ch. 11:202 spells *Lemperi\`ere*. The name is Lempérière, with an acute accent as well; the French edition prints it so.
- (Not a defect: ch. 10:140 prints `firm_auctionsim.ClosingAuction` beside `firm.auctionsim` elsewhere. The first is the
  module file's own name, `code/firm/auctionsim/firm_auctionsim.py`.)
