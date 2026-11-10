# Translation score: One Quant Book 2, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 2, Markets II: Rates, FX and Credit (`markets-2`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled |
| **Date** | 2026-11-09/10 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 383 calls (357 translation, 26 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5) |
| **Canon** | English not verified: the English of Books 1–5 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 383 calls, prompt 1853K + cache read 1611K, output 4881K (thinking 3889K), list price $2.83`. Coordinator (estimate, no transcript count): about 240 tool calls, roughly 20M cache read, 1M cache write and 120K output, about $15–20 list; far more than the translation |
| **Scope** | 31 chapters + 31 solution files, 178 sections; glossary `sources/GLOSSARY_BOOK_2_FR.md` (+ `.run.md`); term config `tools/term_config/book2_fr.py` (curated, see below) |

## Verdict

Fluent technical French in desk register, with calques and stiff word order here and there. The sample of 20 passages held
about five defects: a lost negation (ch. 1), a broken relative clause (ch. 15), broken agreement (ch. 23), English clock
times (ch. 17) and a wrong pronoun (ch. 9), all fixed. The unread remainder certainly holds more of each. A
sentence-by-sentence pass is what would lift it to the 95 tier.

## Build and gates

- `build/one_quant_book_02_markets_2_fr.pdf`: 392 pp (English 363). Errors 0, undefined 0, overfull 2, nullfont 0, missing
  characters 0, invalid-in-math 0, zero-height 0, `.fls` 62 / 62 on disk. TeX Live 2026. The two overfull boxes are
  `\vbox` (9.2 pt and 2.2 pt) while `\output` is active on the index's even pages: the shared running header
  (`styles/onequant.sty`) wraps `One Quant Book 2 — Marchés II` onto a third line. That is a shared-style bug, reported, not
  fixed here (the English index header wraps the same way on its p. 363).
- Known printed defect, not fixable in this edition's files: every multi-label `\cref{a,b}` prints English `and`
  (`Figures 6.3 and 6.4`, 24 places in the PDF; Book 3's French PDF has 13). cleveref takes its conjunctions from the
  document-class language options, not from babel's package option, and `styles/onequant.sty` localises only the names.
- `tools/check_translation.sh markets-2 fr`: PASSED (only the advisory one-word tiers remain: cognates and names).
  Linker `--check`: every file matches the config.
- Links: fr 2011 on 139 targets, en 1388 on 122. The first linker run gave 2751: the French config had none of the English
  config's STOP list, so `pair` (*au pair*) linked every *paire(s) de devises* (99 wrong links) and `coupon`, `cap`,
  `floor`, `tranche`, `cote` and the like linked everywhere. `book2_fr.py` now mirrors `book2_en.py`'s STOP term by term
  (48 terms, both cases) and DROPs five that only collide in French (`bundle`, `pack`, `edge`, `inventaire`, `largeur`).
  Accepted over-frequency, right sense: CAC 40/13, bill 45/0 (*bons du Trésor*), turn 42/4, when-issued 23/1
  (*marché gris*), cross rate 31/3 (*cours croisé*), par yield 35/3, equity tranche 27/4. One target missing:
  `def:m2:fx-spot-microstructure:skew` (en 1, fr 0: the French says *décaler les cotations*).
- `pdfsweep.py` against the Earth Book 5 French PDF (`draft/pilot-markets-2-fr/pdfsweep.txt`): the top of the list is
  listing code (`float`, `return`, `list`, `else`), desk English the glossary keeps (repo, spread, swap, dealer, fixing,
  basis trade, high yield, tail) and accent-cut French (`march`); no English figure label.

## What was read

- Text: 20 passages (seed 1) and the chapter openings that the title fixes touched (9, 12, 18, 27).
- Figures: the 6 figures on the 39 pages `sample.py --pages 394` lists (the other 33 pages hold none), plus 23 pages read
  for the first build's overfull boxes and every figure whose labels were changed by hand (1.3, 3.x, 5.x, 6.1–6.4, 8.x, 9.x,
  11.x, 13.5, 14.1, 15.1, 15.4, 16.1–16.3, 17.2, 18.2, 25.1, 25.2, 26.4, 27.1, 27.2, 28.2), re-read on the final build.

## Defects found and fixed, by class

The reply checks caught none of these; the gate caught the titles, index keys, accent escapes and code lines.

| Class | Count | Example |
|---|---:|---|
| Plain space or no space before `: ; ? !` | 81 lines | `Données : …` |
| `\cref` article missing or of the wrong gender | 25 lines + 7 sentence-initial `\Cref` | `de \cref{fig}`, `Dans \cref{dat}` (an *Encadré*), `\Cref{fig:…} montre` |
| `1er` without superscript | 22 | now `1\up{er}` |
| `One Quant Book N` left in prose | about 18 | now `livre~N`; `livre~N, chapitre~M` → `chapitre~M` |
| Definition opening on a bare noun | 10 | `\emph{Spread de repli} est` |
| English left in titles, headings, labels, ticks, legends | 5 titles + 13 solution headers + about 20 figures | `\section{Exercises}`, `Interest-rate swaps`, months and weekdays in `\foreach`, `xticklabels`, `CHF~3 bn` |
| Lost, merged or reordered text | 5 | ch. 22:77 `three 7.77` dropped; ch. 29:225 odds sentence scrambled; ch. 12:309 and s08:91 repair damage; ch. 9:298 half-English line |
| Doubled or stranded word | 5 | `de de`, `les taux\nles taux`, a stray `Le` |
| Gender of an English term | 7 | `la DV01` → `le DV01` |
| Amounts | 5 | `1.38~billions` → singular; `105.30 millions USD` order |
| Definition titles in lower case | 3 | `[membre sponsorisé]` |
| Line-broken `\index` keys | 6 | gate 1 |
| TeX accent escapes | 3 | `Tr\'esor` in a source title |
| Overfull boxes from longer French | 7 | figure legends and labels in ch. 1, 11, 15, 17, 25 (×2), 27 |
| Figure label collisions | 6 | Fig. 13.5 tenor ticks, 16.1 heading over an amount, 25.1 note over a box, 27.1 and 28.2 sloped labels over boxes |
| Tie at end of line (double space) | 2 | `4~` / `billions` |

Also: chapter titles 9, 12, 18, 27 and their solution headers made to agree; sample fixes listed in the verdict.

## `NUMDIFF` differences accepted

18 files at first; the one real loss (ch. 22:77) was fixed. All the rest are accepted:

- 32nds → *trente-deuxièmes*;
- clock times, `13:00` → `13~h`, `4 p.m.` → `16~h`, `08:30` → `8~h~30` (s31);
- `ten-year` → *dix ans* / *10 ans*;
- numbers moved across a line break;
- `Aug-33` → *août-33* / *août 2033* (ch. 6);
- ch. 27:118, where the French spells out *50 millions d'euros*;
- ch. 29, where `even money` became *cote 1 contre 1*.

## Conventions

These follow desk usage and the run file. The French term is used where French desks use one, and English otherwise (swap,
spread, repo, roll, carry, fixing, mark-out, last look, prime broker, give-up). Other conventions:

- decimal point kept;
- `~:` `~;` `~?` `~!`;
- an article before `\cref`, chosen by the gender of the printed noun (*la Figure*, *l'Encadré*, *l'Exemple*, *le
  Chapitre*);
- `(livre~N, chapitre~M)`;
- amounts as `10~millions de dollars` in prose and `USD~…` where the English codes the currency;
- `billion` as *milliard*, `trillion` as *billion* (the French long scale).

## Upgrade path

Two steps would lift this edition:

- a sentence-by-sentence pass over all 62 files, then re-score and update the `Model` row;
- the shared fixes listed in the run file (cleveref conjunctions and the index header).

## Main-session edits after close (2026-11-10)

Shared fixes after the coordinators closed, applied to every French book and rebuilt 0/0/0 (TeX Live 2026): cleveref conjunctions in French (`et`, `à`; `\cref{a,b}` had printed "and"); a running-header mark not split by `\omTocMark` printed beside the full-width `\truncate` box, wrapping the book title; the last index page balanced by multicol no longer runs into the foot (`\maxbalancingoverflow` 0 in the index); `\iqroles` translated by script where English was left; gate 12 now also compares every math span with English on disk.

Book 2 specifics: the 2 index overfull boxes reported above are gone (the cause was multicol's last-page balance, not the header); one English "and" between formulas (solutions 25:4) and two `\,\%` (ch. 15) fixed; 12 `\iqroles` translated. Final: 393 pp (one more index page), 0/0/0, 62/62 files.
