# Translation score: One Quant Book 5, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 5, Derivatives and Volatility (`derivatives`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-10 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 241 calls (235 translation, 6 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5) |
| **Canon** | English not verified: the English of Books 1–5 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 241 calls, prompt 1449K + cache read 1088K, output 3613K (thinking 2841K), list price $2.11`. Coordinator (estimate, no transcript count): about 230 tool calls over two context windows, roughly 20M cache read, 1.2M cache write and 150K output, about $20–25 list; ten times the translation |
| **Scope** | 28 chapters + 28 solution files, 140 sections; glossary `sources/GLOSSARY_BOOK_5_FR.md` (+ `.run.md`); term config `tools/term_config/book5_fr.py` (STOP seeded from `book5_en.py` through the glossary, 110 STOP and 10 DROP entries) |

## Verdict

Fluent technical French in desk register (smile, skew, strike, forward, pricer and strip are kept as the desk keeps them), with
occasional calques (*de sorte que la vente apparaisse*) and stiff word order. The sample held two term defects (*panier* for
*strip*, *cours à terme* for *forwards*), and both were fixed book-wide. The unread remainder certainly holds more calques and
the odd dropped nuance. A sentence-by-sentence pass would lift it to the 95 tier.

## Build and gates

- `build/one_quant_book_05_derivatives_fr.pdf`: 366 pp (English 348). Errors 0, undefined 0, overfull 0, nullfont 0,
  missing characters 0, invalid-in-math 0, zero-height 0, `.fls` 56 / 56 on disk. TeX Live 2026.
- `tools/check_translation.sh derivatives fr`: PASSED, with gate 12 comparing math spans. The latin prose gate's advisory
  one-word tier has 15 hits, all read: cognates and desk English.
- Linker `--check`: every file matches the config.
- Links: fr 1708 on 141 targets, en 1378 on 118. Every English target is reached.
- Accepted over-frequency, right sense: French spells the full term where English says the short form, e.g. *obligation
  convertible* 26/1, *option digitale* 23/4, *Arrow–Debreu* 24/12, *option asiatique* 8/1, *couverture statique* 9/0 and
  *worst-of* 6/0.
- `pdfsweep.py` against the Earth Book 5 French PDF lists code identifiers, desk English kept by the glossary and accent-cut
  tokens. It finds no English figure label.

## What was read

- Text: 20 passages (seed 1) and the openings of chapters 9, 17 and 27.
- Figures: **every captioned figure (113)**, on a two-column contact sheet of the intermediate build
  (`draft/pilot-derivatives-fr/work/sheet/mk2.py`, 27 pages). The figures repaired by hand were re-read in the final PDF:
  5.4, 13.3, 14.4, 21.1, 24.3 and 24.4.

## Defects found and fixed, by class

The reply checks caught none of these. The gate caught only English legends, tick lists and titles.

| Class | Count | Example |
|---|---:|---|
| Typography outside math: `~` before `: ; ? !` and inside « », and `5\%` → `5~\%` | 517 lines | `Données : …`, `90\%` |
| Decimal comma | 11 lines | ch. 7 (8), ch. 14 (3) |
| `\cref` article missing or of the wrong gender | 1 (of 41 flagged sites, all read) | ch. 7:295 `de \cref{ex}` → `de l'\cref{ex}` |
| Missed elision across a line break | 13 | `que aucune`, `le algorithme`, `de environ`, `que au` |
| Definition opening on a bare noun | 4 | `\emph{Couverture statique} est` → `La couverture …` |
| Term drift against the glossary | 5 terms, about 200 sites | *panier* for *strip* (44), *sourire* for *smile* (98), *valorisateur* for *pricer* (16), five spellings of the miniature firm (24, now *firme miniature*), *contrat à terme* for *forward* in ch. 5 (title included) and *cours à terme* in ch. 28 |
| English left in titles, headings, legends, labels | about 30 | `\section{Exercises}` (ch. 8), 27 `Part IV --- Judgement.` / *Appréciation* part labels, ch. 2 proposition title, 4 `\iqroles` roles, 6 figure labels and legends (Fig. 2.4, 13.x, 15.x, 25.x), 3 ch. 18 tick lists read from a table |
| Solution headers disagreeing with chapter titles | 28 checked, several aligned | ch. 3 *Black--Scholes de trois façons* |
| Grammar | about 10 | *one-touch* made feminine (ch. 15, 20); *Donner-le* → *Le donner* (2); stray *Le* (ch. 21:134) |
| Lost text | 1 | s15:22, the number 1.498 dropped |
| Figure collisions and overruns | 5 | Fig. 5.4 arrow labels over the boxes; 13.3 title; 14.4 axis labels; 21.1 legend (3 → 2 columns); 24.3–24.4 y-labels taller than the plot |
| Overfull boxes from longer French | 8 | ch. 2, 20 and 21 (×2) prose; ch. 21 legend; s09, s24 inline formulas at a line end |
| TeX accent escapes | 2 | `Labord\`ere`, `L\'evy` → UTF-8 |

Also: the joins of `\texttt` broken across lines (the Book 2 `jointt2.py` route) were undone because they shifted line
counts. The break now sits before `\texttt` (ch. 2, 4, 5, 18; ch. 26 after `\bfield{Règles}`).

## `NUMDIFF` differences accepted

9 course files, all accepted:

- ch. 2: *moment d'ordre 2*;
- ch. 7, 10, 20: `3-month`, `1-year` written in words (*trois mois*, *un an*);
- ch. 13: *ten percent* → `10~\%`; `1-month`, `1-week` in words;
- ch. 18: explicit tick lists replace the `table`-driven ones;
- ch. 19: *Seventy Percent* → `70~\%`;
- ch. 20:236: *half* → *de poids 0.5*;
- ch. 26: *one* → `1`;
- ch. 27: `\euro259` tokenisation.

Also accepted, for gate 12: ch. 26:203–204 keep the English math spans `$-\$8\,720$` (the French form, `$-8\,720$~\$`,
would change the math span).

## Conventions

- Vocabulary follows desk usage (glossary): smile, skew, strike, forward (the futures sites keep *contrat à terme*), pricer,
  strip, bump-and-reprice, *firme miniature*.
- Decimal point kept. Typography: `~:` `~;` `~?` `~!`, `«~…~»` and `5~\%` outside math.
- An article goes before each `\cref`, by the gender of the printed noun. Series references are written `(livre~N, chapitre~M)`.
- Ordinals use `\up{er}`. Part labels read *Partie I --- Le forward.* … *Partie IV --- Jugement.*

## Upgrade path

A sentence-by-sentence pass over all 56 files, then re-score and update the `Model` row.

## Main-session edits after close (2026-11-10)

Shared fixes after the coordinators closed, applied to every French book and rebuilt 0/0/0 (TeX Live 2026): cleveref conjunctions in French (`et`, `à`; `\cref{a,b}` had printed "and"); a running-header mark not split by `\omTocMark` printed beside the full-width `\truncate` box, wrapping the book title; the last index page balanced by multicol no longer runs into the foot (`\maxbalancingoverflow` 0 in the index); `\iqroles` translated by script where English was left; gate 12 now also compares every math span with English on disk.

Book 5 specifics: the six amounts of ch. 26:203–204 now put the dollar after the number (`$-8\,720$~\$`), which gate 12 accepts. Final: 366 pp, 0/0/0, 56/56 files.
