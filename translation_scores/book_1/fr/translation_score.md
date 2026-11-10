# Translation score: One Quant Book 1, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 1, Markets I: the ecosystem and exchange-traded markets (`markets-1`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled |
| **Date** | 2026-11-09/10 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 546 calls (526 translation, 20 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5) |
| **Canon** | English not verified: the English of Books 1–5 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 546 calls, prompt 2911K + cache read 2297K, output 6392K (thinking 4831K), list price $3.80`. Coordinator (estimate, no transcript count): about 300 tool calls, roughly 25M cache read, 1.5M cache write and 200K output, about $20–30 list; far more than the translation |
| **Scope** | 31 chapters + 31 solution files, 200 sections; glossary `sources/GLOSSARY_BOOK_1_FR.md` (+ `.run.md`, split per chapter in `draft/pilot-markets-1-fr/glossary/`); term config `tools/term_config/book1_fr.py` (curated, see below) |

## Verdict

Near-native technical French in desk register, with calques and stiff word order here and there. The 20-passage sample
held about six defects: a wrong verb for a busted trade (28:416, *corrige l'impression* for *annule la transaction*), a
mistranslated "half a per cent" (26:13), "mainland China" (12:143), a mistranslated opening position (07:45), "This chapter
is this algorithm" (13:11) and a missing comma (08:103). All were fixed. The figure pass then found a mistranslated
cut-off (*échéances* for brokers' cut-off times, 23:143) and a gender slip (*une plafond*, 12:260). The unread remainder
certainly holds more of each. A sentence-by-sentence pass is what would lift it to the 95 tier.

## Build and gates

- `build/one_quant_book_01_markets_1_fr.pdf`: 403 pp (English 374). Errors 0, undefined 0, overfull 0, nullfont 0,
  missing characters 0, invalid-in-math 0, zero-height 0, `.fls` 62 / 62 on disk. TeX Live 2026, `pilot_translation/build.sh`.
- `tools/check_translation.sh markets-1 fr`: every gate passes except one known false positive. Only the advisory one-word
  tiers remain, and they are cognates and names. The false positive is the quant twin (gate 12) at
  `parts/markets-1/fr/12-asian-and-emerging-equity-markets.tex:341–342`: the English `\texttt{MarketRules(...)}` spans three
  lines, and its middle line is pure code. Keeping the English newlines fails the orphan-line and dup gates. Joining the
  argument fails the twin on whitespace alone (a newline against a space). Both layouts were built and gated. The joined
  form is kept; see the run file, finding 2.
- Linker `--check`: every file matches the config.
- Links: fr 2285 on 167 targets, en 1714 on 148, and no English target is missing. The first run gave about 5800: the
  French config had no STOP list, so *action(s)*, *ordre(s)*, *bourse*, *position*, *prime*, *base*, *indice de référence*
  and the like linked everywhere. `book1_fr.py` now carries the English STOP terms in French (both cases) and DROPs
  `action(s)` and `ordre(s)`. The remaining over-frequencies are right-sense.
- `pdfsweep.py`: the hits are cognates, accent-split tokens and listing code. Spot checks of `years`, `before`, `best` and
  `left` found only code.
- Residual English in print by design: the fee name « 2 and 20 » (ch. 3, quoted desk jargon).

## What was read

- Text: 20 passages (seed 1, `sample.txt`) and the openings of chapters 1, 10, 12 and 28.
- Figures: the 11 figure pages among the 40 listed by `sample.py --pages 405`, and then every captioned figure in the
  book (106 figures), on contact sheets cropped at 140 dpi. Every figure repaired by hand was read again on the final
  build, and fig. 29.1 three times.

## Defects found and fixed, by class

Nearly all were caught by the sweeps and the figure pass, not by a reply check or a gate.

| Class | Count | Example |
|---|---:|---|
| Thin space before `\%` in numbers | 351 | `5\%` → `5\,\%` |
| Non-breaking space before `: ; ? !` and inside « » | 85 lines | |
| Doubled currency (`\$200$ millions de dollars`) | 72 | `\$` dropped where *de dollars* follows |
| `\cref` with no article, or the wrong gender | 41 + ~16 | *voir \cref{dat:...}* → *voir l'\cref*; `dat` (Encadré) given *du* |
| Figure labels left in English | ~25 figures | `yticklabels from table`, `\foreach` lists, symbolic coords, months, `\text{years}` |
| Figure collisions and clipped labels | 23 figures | 2.1, 3.1, 5.4, 5.5, 6.3, 8.1, 9.2, 11.1, 11.4, 14.1, 16.1, 17.2, 19.4, 21.4, 26.2, 26.3, 27.1, 27.2, 29.1, 30.1, 31.3 |
| Overfull boxes from longer French | 10 | tables in ch. 1, 18, 22; nodes in ch. 1, 4, 9, 13; legends in ch. 11, 19 |
| *One Quant Book N* in prose | ~15 | → *livre~N* |
| Ordinals | 12 | `1er` → `1\up{er}` (one was a fatal `1^er` in ch. 10), `85e` → `85\up{e}` |
| Repair-introduced defects | 6 | wrong `\cref` gender (04:82, 04:396, 11:341, 19:267), *voir au* (08:34, 08:73), lost words (24:302) |
| Bare noun opening a definition | 8 | ch. 2 ×2, 3 ×2, 5 ×2, 15, 26 |
| Headings left in English | 6 | ch. 11 *Exercises*, 18, 24, solutions 06, boxes in 19 and 21 |
| Imperatives in exercises | ~10 | *Essayez* → *Essayer*; ch. 10 opening rewritten with *on*, ch. 31 *vos* → *ses* |
| Article stranded before a line break | 4 | solutions 27:81, 31:216, 07:372, 28:225 (*le construction*) |
| Wrong word or sense | ~10 | *point-in-time* as *temps réel*; *répondeur* → *répondant* (17×); *échéances* for cut-offs; *corrige l'impression*; *Coût principal* linked to principal–agent |
| Broken `\index` keys, accent escapes | 4 | `It\^o`, `G\^arleanu` → Itô, Gârleanu; keys rewrapped at 30:21, 21:259 |
| Lines merged or dropped by the model | 2 files | solutions 20 and 31, interview answers; realigned by skeleton (`work/realign.py`) |

Role-play exercises in ch. 2, 10, 19 and 28 keep *vous*. That is accepted: they address the reader as a desk trainee.

## `NUMDIFF` differences accepted

13 files, all accepted:

- ch. 7:219 *Line 2* → *le second poste*;
- ch. 12: *a tenth of a percent* → `0.1~\%`, *first autocorrelation* → *d'ordre 1*, plus lines moved;
- ch. 14: *twenty-four trillion* → `24~billions`, *three-times* → *levier 3*;
- ch. 15: *one percent* → `1~\%`;
- ch. 17: `15:00` → *15 h*;
- ch. 20: *day 15* → *quinzième jour*;
- ch. 23: *cents* → `0.02~\$`;
- solutions 17: *one* → `1`;
- the rest are `\euro` / `\pounds` parse artefacts and numbers moved across lines.

Every *billion*/*trillion* was checked: *milliard* and *billion* are used correctly throughout.

## Conventions

These follow the series card and the Book 2 and Book 3 coordinators' rulings:

- `~:` `~;` `~?` `~!`, «~ ~», and the decimal point kept;
- `1\up{er}`;
- an article before `\cref`, in the gender of the printed noun, including a sentence-initial `\Cref`;
- *livre~N* in prose;
- *les frais*, never *le frais*;
- *on* or the infinitive outside the interview questions and role-plays;
- French month names in figures;
- desk anglicisms kept where French desks use them (*bid*, *ask*, *spread*, *roll*, *carry*, *fair value*, *special*).

## Upgrade path

A sentence-by-sentence pass over all 62 files, then re-score and update the `Model` row.

## Main-session edits after close (2026-11-10)

Shared fixes after the coordinators closed, applied to every French book and rebuilt 0/0/0 (TeX Live 2026): cleveref conjunctions in French (`et`, `à`; `\cref{a,b}` had printed "and"); a running-header mark not split by `\omTocMark` printed beside the full-width `\truncate` box, wrapping the book title; the last index page balanced by multicol no longer runs into the foot (`\maxbalancingoverflow` 0 in the index); `\iqroles` translated by script where English was left; gate 12 now also compares every math span with English on disk.

Book 1 specifics: the coordinator's thin space before `\%` (351) became the series' `~\%`, and inside 296 math spans the English `\%` was restored. Final: 403 pp, 0/0/0, 62/62 files.
