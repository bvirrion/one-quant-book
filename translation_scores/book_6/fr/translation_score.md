# Translation score: One Quant Book 6, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 6, Rates, Credit, XVA and Risk (`rates-credit-risk`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-11 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 313 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 6–10, no subagents |
| **Canon** | English not verified: the English of Book 6 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 313 calls, prompt 1731K + cache read 1499K, output 3828K (thinking 2909K), list price $2.28`. Coordinator: shared with Books 7–10, see `sources/TRANSLATION_BOOKS_6-10_FR.md` |
| **Scope** | 29 chapters + 29 solution files, 150 sections; glossary `sources/GLOSSARY_BOOK_6_FR.md` (+ `.run.md`); term config `tools/term_config/book6_fr.py` (STOP and DROP mapped from `book6_en.py` through the glossary, 92 STOP and 10 DROP entries) |

## Verdict

Fluent technical French in desk register (swap, swaption, caplet, smile, pricer, desk XVA, IPV are kept as the desk keeps
them), with calques and long sentences here and there. The sample held five defects: *numéraire* for cash collateral
(all of ch. 2, which clashes with the numeraire of ch. 4), a garbled *par-yield* in s04, *VIP* for IPV (s27), *contrepartie*
for the clearing member (ch. 25), and *la* Chief Investment Office (ch. 26). All five were fixed, ch. 2 throughout
(*en espèces*). The unread remainder certainly holds more of the same.

## Build and gates

- `build/one_quant_book_06_rates_credit_risk_fr.pdf`: 343 pp (English 314). Errors 0, undefined 0, overfull 0, nullfont 0,
  missing characters 0, invalid-in-math 0, zero-height 0, `.fls` 58 / 58 on disk. TeX Live 2026.
- `tools/check_translation.sh rates-credit-risk fr`: PASSED, gate 12 included. The latin prose gate's advisory one-word tier
  has 14 hits, all cognates, desk English or code.
- Linker `--check`: every file matches the config.
- Links: fr 1,029 on 142 targets, en 824 on 129. The over-frequent targets are right-sense (French repeats the full term of a
  grouped definition). Four targets are reached only at their own definition, as in English.
- `pdfsweep.py` against the French Book 5 PDF lists code identifiers, source titles and glossed English. It finds no English
  figure label.

## What was read

- Text: 20 passages (seed 1) and the openings of chapters 11, 20 and 26.
- Figures: **every captioned figure (107)**, on a contact sheet of the intermediate build (`draft/pilot-quant-fr/sheet.py`,
  23 pages). The repaired figures were re-read in the rebuilt PDF: 10.4, 19.1, 21.1 and 24.2.
- NUMDIFF, line by line (`draft/pilot-quant-fr/numlines.py`): every difference explained. They were line shifts, numbers
  written in words (*premier octobre*, *deuxième éd.*), and `xticklabels` added. One real loss was fixed: a `4{,}08`.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Typography outside math: `~` before `: ; ? !` and inside « », `5\%` → `5~\%` | 134 lines | `Remède : …` |
| Decimal comma, `{,}` included | 55 lines (`fix_common.py`, with the term pins below) | `4{,}08`, *forward 3,05~\%* |
| Term drift against the glossary | *sourire* → *smile*, *valorisateur* → *pricer*, *Fiches de stratégie* | the drift came back despite pinning |
| `\cref` article | 6 (one wrong pick, 19:235 *les* → *des*, fixed by hand) | |
| Definition opening on a bare noun | 11 + 7 lowercase (found during Book 8) | `\emph{XVA} est` → *L'acronyme \emph{XVA} est* |
| English printed from code or data | 15 figures | symbolic `xticklabels` in ch. 1–3, 18, 20–29; ch. 19 bar labels |
| English left beside its translation | 3 | ch. 20:349 *desk can hedge.*, s28 duplicate `\iqlookfor` |
| Figure collisions | 4 | Fig. 10.4 label on the curves, 19.1 arrow label over another, 21.1 tick labels run together, 24.2 *pentification aplatissement* (now *steepener*, *flattener*, as in Fig. 24.1) |
| Overfull boxes from longer French | 6 | ch. 24 running header (`\chaptermark`), ch. 8 (×3), ch. 17, s03 |
| Sense | 5 (sample) | see the verdict |
| English role names in `\iqroles{}` | 10 lines (found during Book 8) | `researcher` → *chercheur* |

## English-canon notes (reported, not fixed)

- The citation author connector varies between *and* and *et* in the `omsources` lists (minor, carried into French as is).
