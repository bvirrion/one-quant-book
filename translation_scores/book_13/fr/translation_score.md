# Translation score: One Quant Book 13, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 13, Low-Latency Software (`low-latency`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 405 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 11–15, no subagents |
| **Canon** | English not verified: the English of Book 13 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 405 calls, prompt 2611K + cache read 2337K, output 5067K (thinking 3553K), list price $3.08`. Coordinator: shared with Books 11–15, see `sources/TRANSLATION_BOOKS_11-20_FR.md` |
| **Scope** | 26 chapters + 26 solution files; glossary `sources/GLOSSARY_BOOK_13_FR.md` (+ `.run.md`); term config `tools/term_config/book13_fr.py` |

## Verdict

Fluent technical French for systems programming: *chemin critique* (hot path, kept in English where the book uses it as
a name), *faux partage*, *comportement indéfini*, *tampon de réordonnancement*, *contournement du noyau*, *journal binaire*,
*formatage différé*; the identifiers, compiler flags, clock sources and memory orders stay as written. The sample held three
slips, all fixed: Rust's *sound* rendered *sûr*, which is also French for *safe* (below), a *compteur rembourré* for a padded
counter, and a priority *relevé* that read as the holder. Three chapter openings (chs. 4, 13, 20) held one more: *rejoué sur
un desk* for "replayed on a desk" (a workstation, not a trading desk). One section (ch. 23 §1, 110 lines) failed every
retry (truncation, duplicated `\texttt`) and was translated by the coordinator, saved through `run.py`'s checks
(`save_hand.py`).

## Build and gates

- `draft/pilot-quant-fr/build-s1/one_quant_book_13_low_latency_fr.pdf`: 332 pp (English 314). Errors 0, undefined 0,
  overfull 0, nullfont 0, missing characters 0, invalid-in-math 0, zero-height 0, `.fls` 52/52. TeX Live 2026. Final build into `build/` at the close of
  session 1, after the series-wide sweeps: 332 pp, 0/0/0.
- `tools/check_translation.sh low-latency fr`: PASSED, gate 12 included. The twin prose gate first failed on figure labels
  left in English and on chart labels that are C++ and Linux identifiers in every language (`rdtsc`, `O3 native`,
  `seq_cst`, `snprintf`). Book 13's identifier block in `tools/check_latin_prose.py` allows those tokens only; two
  `\foreach` lists of node names that print nothing were rewritten as plain `\draw`s.
- Linker `--check`: every file matches the config.
- Links: fr 817, en 606. Three wrong-sense links found by the sample were removed by the term change below.
- `pdfsweep.py` against the French Book 10 PDF: 151 English-only word types, all code identifiers and comments inside
  listings (`uint`, `const`, `memcpy`), library and tool names, and desk English kept (*heartbeat*, *pipeline*).

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 4, 13, 20), the sweep reports.
- Figures: **every captioned figure (73)**, on a 17-page contact sheet, twice (before and after the repairs); the last
  repairs re-read cropped from the rebuilt PDF.
- Numbers: per line in the run directory (`numrun.py`) before install, then per file (`numfile.py`) after.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| **Wrong-sense term** | 1 term, 3 links | *sound* (Rust) as *sûr*: the linker tied *interface sûre* and *bascule sûre* (safe) to its definition. Now *saine (sound)*; glossary marked |
| **Reversed chart labels** | 1 | Fig. 3.3: `yticklabels` listed in the coordinate order, but `ytick=data` follows the CSV's row order, so *même ligne* sat on the fastest bar |
| Section translated by the coordinator | 1 | ch. 23 §1 (110 lines) |
| Numbers misplaced in the run directory | 6 lines | ch. 26 *99.9\up{e}*, solutions 4 a dropped clause |
| English figure text | 44 `sites` lines | the Fig. 13.2 legend, Fig. 23.1's nodes, Fig. 25.1's pyramid, Fig. 17.1's messages |
| Typography outside math | 65 lines | |
| English role names in `\iqroles{}` | 24 lines | |
| Weekend-problem part labels | 25 lines | |
| Infinitive in interview questions | 11 lines | `iq_imperative.py` |
| *and* between authors | 3 lines | `authors_et.py` |
| Definition opening on a bare noun | 13 | `bare_def_fix.py` (9) and by hand (*Le multicast*, *Le compare-and-swap*, *La dévirtualisation*, *Le Simple Binary Encoding*) |
| English heading | 1 | ch. 20 *Exercises* |
| Overfull boxes | 14 | two tables re-specified, one section title, one TikZ picture, `\sloppy` in seven long-`\texttt` paragraphs |
| Figure collisions | 23 | Figs. 2.1, 3.1, 6.2, 8.1, 8.2, 10.1, 13.4, 14.3, 15.3, 17.2, 18.1, 18.3, 19.2, 20.1, 20.2, 21.1, 22.1, 22.2, 23.1, 24.1, 24.2, 25.1, 26.1 |
| Wording (sample and openings) | 4 | *sain*, *avec remplissage*, *sa priorité relevée*, *poste de travail* |

## English-canon defects (reported, not fixed)

None found in the sampled passages. Fig. 21.2's two crossing arrow labels overlap in English too.
