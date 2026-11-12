# Translation score: One Quant Book 11, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 11, Market Making and High-Frequency Trading (`hft`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 239 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 11–15, no subagents |
| **Canon** | English not verified: the English of Book 11 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 239 calls, prompt 1456K + cache read 1249K, output 3184K (thinking 2404K), list price $1.90`. Coordinator: shared with Books 11–15, see `sources/TRANSLATION_BOOKS_11-20_FR.md` |
| **Scope** | 29 chapters + 29 solution files; glossary `sources/GLOSSARY_BOOK_11_FR.md` (83 lines, + `.run.md` with Books 1–10 as `00`); term config `tools/term_config/book11_fr.py` |

## Verdict

Fluent French for market making. The desks' English is kept where the desks keep it: *market making*, *skew*, *rebate*,
*kill switch*, *mark-out*, *searcher*, *bundle*, *auto-quoter*; a market maker is a *teneur de marché*, a feature a
*variable*. The sample held four small defects: a gender agreement (*le plus faible des cinq variables*), an English
noun with no article opening a strategy-card field (*Hedgers qui font le roll*), and interview questions that mixed the
imperative (*Définissez*) with the exercises' infinitive (*Expliquer*). Interview questions now all use the imperative
(`iq_imperative.py`, new, 13 lines). A fourth fix came from a figure's page: *Le skew rend l'inventaire revenir* →
*fait revenir*. Haiku's first pass left 7 files with a rejected section; three passes cleared them.

## Build and gates

- `draft/pilot-quant-fr/build-s1/one_quant_book_11_hft_fr.pdf`: 353 pp (English 329). Errors 0, undefined 0, overfull 0,
  nullfont 0, missing characters 0, zero-height 0, `.fls` 58/58. TeX Live 2026. Final build into `build/` at the close of
  session 1, after the series-wide sweeps: 353 pp, 0/0/0.
- `tools/check_translation.sh hft fr`: PASSED, gate 12 included. The first runs failed on TeX accent escapes (`\'A`,
  now UTF-8 *Á.~Cartea*) and on 11 prose fragments identical to English, all in figures.
- Linker `--check`: every file matches the config.
- Links: fr 430, en 361. *Prix de couverture* links 12 times against 1 in English, which says "the cover" for short
  after the first use. French repeats the full term, and the sense is right.
- `pdfsweep.py` against the French Book 10 PDF (there is no other edition of Book 11): 748 English-only word types, all
  code identifiers inside listings (`years`, `alive`, `takes`, `hits`), proper names, desk English kept by the glossary
  (*proxy*, *spot*, *funding*, *bundle*, *searcher*) and the term *fail closed*.

## What was read

- Text: 20 passages (seed 1), the sweep reports, and the pages around every repaired figure.
- Figures: **every captioned figure (68)**, on a 21-page contact sheet of an intermediate build. Each repaired figure was
  re-read, cropped, in the rebuilt PDF; two (14.1, 22.2) needed a second fix.
- Numbers: per file, as multisets (`numfile.py`). Every number English has and French lacks was read: the euro sign set
  after its number, numbers written as words (*une milliseconde*), clock times (3 pm → *15~h*), *4Q* → *T4*, and line
  shifts. One real defect: chapter 20 came back with decimal commas, against the series' decimal points (fixed).

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Typography outside math (`~` before `: ; ? !`, `~\%`) | 124 lines | |
| Term drift and agreement | 28 lines (`fix_common.py`) | *Laquelle des N fiches*, *la plus exposée* (new Book 11 rules) |
| English role names in `\iqroles{}` | 70 lines | |
| Weekend-problem part labels | 33 lines | ch. 20: *Taux et portage*, *Le jeu du dividende*, *Le verdict* |
| `\texttt{}` split across a line end | 16 lines | |
| `\cref` without its article; quotes | 3 + 3 | |
| Infinitive in interview questions | 13 lines | `iq_imperative.py` (new): *Dériver* → *Dérivez* |
| Decimal commas | 1 file | ch. 20 |
| TeX accent escapes | 3 | *\'A.~Cartea* → *Á.~Cartea* (chs. 3, 4, 7) |
| Definition opening on a bare noun | 2 | chs. 4 and 6 |
| Prose fragments identical to English (gate) | 11 | `\foreach` labels in chs. 6 and 21, *achat/vente*, *messages envoyés*, *en cents*, *gain capté* |
| Overfull boxes from longer French | 15 | eleven tables re-specified (`tabspec.py`), three `sloppypar`, one legend in ch. 12 |
| Figure collisions and clipping | 10 | Figs. 1.2, 11.1, 14.1, 18.1, 21.2, 22.1, 22.2, 24.1, 25.1 (14.1 twice) |
| Sense and grammar (sample) | 4 | *la plus faible*, *Les hedgers*, *fait revenir l'inventaire*, *les frais d'emprunt* |

## English-canon defects (reported, not fixed)

None found in the sampled passages.
