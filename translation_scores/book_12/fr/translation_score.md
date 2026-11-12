# Translation score: One Quant Book 12, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 12, Machine Learning for Markets (`ml`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 291 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 11–15, no subagents |
| **Canon** | English not verified: the English of Book 12 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 291 calls, prompt 1780K + cache read 1601K, output 4186K (thinking 3167K), list price $2.47`. Coordinator: shared with Books 11–15, see `sources/TRANSLATION_BOOKS_11-20_FR.md` |
| **Scope** | 29 chapters + 29 solution files, 125 sections; glossary `sources/GLOSSARY_BOOK_12_FR.md` (228 lines, + `.run.md`); term config `tools/term_config/book12_fr.py` |

## Verdict

Fluent French for machine learning: *apprentissage automatique*, a feature is a *variable* (a firm characteristic stays a
*caractéristique*), *validation croisée purgée*, *prédiction conforme*, *déploiement fantôme*; the field's English is kept
where French practitioners keep it (*gradient boosting*, *bagging*, *walk-forward*, *kill switch*, *pipeline*). The sample
held one agreement slip (*découpées (par jour, purgé)*); three chapter openings held one more (ch. 29, *une prévision …
validé, compilé*). Two sections were accepted by hand: their only flags were drawing code kept as in English. Two passes
lost content that only NUMDIFF saw (below).

## Build and gates

- `draft/pilot-quant-fr/build-s1/one_quant_book_12_ml_fr.pdf`: 370 pp (English 348). Errors 0, undefined 0, overfull 0,
  nullfont 0, missing characters 0, zero-height 0, `.fls` 58/58. TeX Live 2026. Final build into `build/` at the close of
  session 1, after the series-wide sweeps: 370 pp, 0/0/0.
- `tools/check_translation.sh ml fr`: PASSED, gate 12 included. The first run failed the twin prose gate on Fig. 3.1's
  English nodes, Fig. 16.2's tick list, a legend in ch. 23 and two English headline phrases in solutions 13 (now in
  French quotes; they are the English input of an English model and stay English). One fix (`GARCH-$t$`) then failed the
  code twin gate and was reverted.
- Linker `--check`: every file matches the config.
- Links: fr 1,212, en 1,000. The over-frequent targets are right-sense: English shortens to *the surrogate*, *shadow*,
  *conformal* after the first use, French repeats *modèle de substitution*, *déploiement fantôme*, *prédiction conforme*.
- `pdfsweep.py` against the French Book 10 PDF: 1,608 English-only word types, all code identifiers and comments inside
  listings (`train`, `inner`, `missing`), library names (*torch*, *lightgbm*), proper names, and desk English kept.

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 6, 14, 29), the sweep reports.
- Figures: **every captioned figure (62)**, on a 14-page contact sheet. Each repaired figure was re-read, cropped, in
  the rebuilt PDF; Figs. 3.1 and 19.1 needed a second and third pass.
- Numbers: per line in the run directory (`numrun.py`), then per file after install (`numfile.py`).

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| **Content lost** (NUMDIFF) | 2 | solutions 14: *106\,681 paramètres et 505 jetons* dropped from an answer; ch. 3: *(chapitre~3)* dropped |
| Decimal commas | 7 lines | chs. 4 and 27 |
| Typography outside math | 155 lines | |
| English role names in `\iqroles{}` | 48 lines | |
| Weekend-problem part labels | 20 lines | |
| Infinitive in interview questions | 14 lines | `iq_imperative.py` |
| *and* between authors in source lists | 18 lines | `authors_et.py` (new) |
| Definition opening on a bare noun | 41 | `bare_def_fix.py`, generalised to any verb and to mid-line definitions (26 + 13 + 2 by hand) |
| English headings | 3 | ch. 18 *Learning to make markets*, solutions 20's heading; ch. 18 *formule fermée* → *forme fermée* |
| English figure text | 12 | Fig. 3.1 (eight labels, in a local `\row` macro the gate does not parse), Fig. 26.1 tick labels from a CSV column |
| Overfull boxes | 15 | twelve tables re-specified, two TikZ pictures, one `sloppypar` |
| Figure collisions | 9 | Figs. 1.1, 3.1, 14.1, 14.2, 19.1, 22.1, 22.2, 23.1, 24.1 |
| Grammar (sample and openings) | 2 | *avec purge*, *validée, compilée et exploitée* |

## English-canon defects (reported, not fixed)

None found in the sampled passages.
