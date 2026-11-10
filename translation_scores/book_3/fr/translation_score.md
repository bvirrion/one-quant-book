# Translation score: One Quant Book 3, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 3, Markets III: Commodities, Energy and Crypto (`markets-3`) |
| **Language** | French (`fr`) |
| **Overall score** | **87 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled |
| **Date** | 2026-11-09/10 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 273 calls (249 translation, 24 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5) |
| **Canon** | English not verified: the English of Books 1–5 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 273 calls, prompt 1462K + cache read 1116K, output 3716K (thinking 2921K), list price $2.16`. Coordinator (estimate, no transcript count): about 120 tool calls, roughly 10M cache read, 0.8M cache write and 90K output, about $10–13 list; far more than the translation |
| **Scope** | 29 chapters + 29 solution files, 138 sections; glossary `sources/GLOSSARY_BOOK_3_FR.md` (+ `.run.md`); term config `tools/term_config/book3_fr.py` (unchanged: no curation needed) |

## Verdict

Fluent technical French in desk register, with occasional calques and stiff word order. The sample still held two content
defects (a clause dropped in ch. 27, a stray English-order fragment in ch. 15) and an untranslated series name, all fixed;
the unread remainder certainly holds more of each. A sentence-by-sentence pass is what would lift it to the 95 tier.

## Build and gates

- `build/one_quant_book_03_markets_3_fr.pdf`: 354 pp (English 332). Errors 0, undefined 0, overfull 0, nullfont 0, missing
  characters 0, invalid-in-math 0, zero-height 0, `.fls` 58 / 58 on disk. TeX Live 2026.
- `tools/check_translation.sh markets-3 fr`: PASSED. Linker `--check`: every file matches the config.
- Links: fr 1641 on 167 targets, en 1267 on 153; every English target reached. Accepted over-frequency, right sense:
  front-running 38/7 (back-running shares the definition), fire sale 28/0 (*ventes forcées* is the term itself),
  perp 50/21, crop year 17/6 (*campagne*, agricultural sense only), day-ahead 16/2, wash trading 15/5, trading house 10/0.
- `pdfsweep.py` with English as both reference and edition prints 0 (useless by construction); against the Earth Book 5
  French PDF its list is desk English kept by the glossary (spread, swap, trader, pool, funding), names, listing code and
  accent-cut tokens; no English figure label.

## What was read

- Text: 20 passages (seed 1) and the openings of chapters 5, 14 and 26.
- Figures: the 6 figures on the 35 pages `sample.py --pages 354` lists (the other 29 pages hold none), plus the 11 figures
  whose labels were changed by hand (2.1, 2.3, 6.1, 7.1, 7.3, 8.2, 8.4, 9.1, 22.4, 25.1, 29.1), re-read after repair.

## Defects found and fixed, by class

None of these was caught by a reply check; the gate caught only the titles, legends and index keys.

| Class | Count | Example |
|---|---:|---|
| Plain space or no space before `: ; ? !` | 137 lines | `Données : …` |
| Decimal comma (and comma thousands in ch. 11) | 23 lines | `81,20`, `25,800~\$` |
| Definition opening on a bare noun | 17 | `\emph{Stockage flottant} est` |
| `\cref` article missing or of the wrong gender | 33 | `de \cref{fig}`, `la \cref{dat}` (an *Encadré*), `voir du \cref{ch}` |
| `One Quant Book N` left in prose | about 20 | now `livre~N`, `(livre~1, chapitre~19)` |
| Missed elision, including across a line break | 12 | `ce que émettent`, `et le\nestimation`, `à\nle port` |
| `frais` in the singular | 10 | `Le frais de base est brûlé` |
| English left in titles, headings, legends, labels | 31 | 4 `\section{Exercises}`, 2 `Part III/IV`, `[Floating storage]`, 4 solution headers, 4 `\foreach` lists, 2 legends, 2 tick lists |
| Lost or merged text | 4 | s01 answer 12 (`154\,000~\$`) dropped; ch. 27 clause dropped; ch. 15 stray `clients.`; ch. 4 source title half translated |
| Wrong-sense link | 1 | ch. 18 *base risk limit* written *plafond de risque de base*, linked to basis risk |
| Figure collisions | 2 | Fig. 6.1 top labels, Fig. 8.4 arrow labels over the boxes |
| Overfull boxes from longer French | 8 | ch. 13, 15, 28 tables; ch. 16 `\text{cours vendeur}` subscripts in a proof |
| Repair pass reverted a French line to English | 1 | ch. 15:181 (see the run file) |
| Doubled word, stray article, calque | about 8 | `pour\npour`, `le fret et le\nl'assurance`, `revenu fixe américain` |

Also: `1er` became `1\textsuperscript{er}` (24); chapter titles 13, 25, 28 and their solution headers made to agree.

## `NUMDIFF` differences accepted

16 files at first; the real losses (s01:63 and 23 decimal commas) were fixed. The final residual, 12 files, all accepted:

- ch. 5, 6 and s06: `day-ahead` → `J-1` adds a 1; `13:00` → `13~h` drops `00`; ch. 6:367 `15-minute` → *au quart d'heure*;
- ch. 9:62, ch. 19 and s19: clock times, `3:00 p.m.` → `15~h`, `4 p.m.` → `16~h`;
- ch. 8:165 `\pounds9\,245\,900` → `9\,245\,900~livres sterling` (the sweep reads `\pounds9` as one token);
- ch. 13:51 the title `Ring dealing member (catégorie~1)`, from the definition;
- ch. 18:213 and 342, ch. 25:30, ch. 27:259: `USD~1 million` → *par million de dollars*, `One Quant Book 1` → *Marchés~I*,
  `1 cent` → *un cent*;
- ch. 24:154 *Opérations 24 heures sur 24* for *Round-the-clock operations*.

## Conventions

Desk usage per the run file: French term where French desks use one, English otherwise (spread, swap, funding, perp,
front-running, flash loan, travel rule). Decimal point kept, `~:` `~;` `~?` `~!`, an article before `\cref` by the gender
of the printed noun (*l'Encadré*, *le Tableau*, *la Figure*), `(livre~N, chapitre~M)`, amounts as `5.40~\$`.
*J-1* (glossary) and *day-ahead* (a section title, figure legends) both occur in chapters 5–6; *crypto-actif* is now the
only spelling.

## Upgrade path

A sentence-by-sentence pass over all 58 files, then re-score and update the `Model` row.

## Main-session edits after close (2026-11-10)

Shared fixes after the coordinators closed, applied to every French book and rebuilt 0/0/0 (TeX Live 2026): cleveref conjunctions in French (`et`, `à`; `\cref{a,b}` had printed "and"); a running-header mark not split by `\omTocMark` printed beside the full-width `\truncate` box, wrapping the book title; the last index page balanced by multicol no longer runs into the foot (`\maxbalancingoverflow` 0 in the index); `\iqroles` translated by script where English was left; gate 12 now also compares every math span with English on disk.

Book 3 specifics: 24 `\textsuperscript{er}` became the series' `\up{er}`; 67 `\iqroles` translated; three `\,\%` (ch. 18) became `~\%`. Final: 354 pp, 0/0/0, 58/58 files.
