# Translation score: One Quant Book 16, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 16, The Desk and the Firm (`desk`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 251 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 16–20 (session 2 of the Books 11–20 run), no subagents |
| **Canon** | English not verified: the English of Book 16 has had no fresh-reader verification pass, and solutions were not recomputed. One English layout defect was fixed on the way (below). |
| **Tokens** | `all: 251 calls, prompt 1606K + cache read 1337K, output 3616K (thinking 2792K), list price $2.14`. Coordinator: shared with Books 16–20; weekly plan 82 % before step 5 and 82 % after this book's step 9 (see `sources/TRANSLATION_BOOKS_11-20_FR.md`) |
| **Scope** | 30 chapters + 30 solution files; glossary `sources/GLOSSARY_BOOK_16_FR.md` (+ `.run.md`); term config `tools/term_config/book16_fr.py` |

## Verdict

Fluent French for the business side of a trading firm: *teneur de marché pour compte propre*, *plateforme
multigérants*, *frais refacturés* (pass-through), *fonds propres*, *exigence au titre des frais généraux fixes*,
*limite indicative* / *limite ferme*, *tolérance aux pertes*, *trésorerie non grevée*, *marge maison*, *contrat-cadre*,
*compensation avec déchéance du terme*, *barrière à l'information*, *franchissement de la muraille*, *rémunération à la
formule*, *dispositif de limites*, *goulot d'étranglement*. Desk English is kept where the trade keeps it (*pod*,
*drawdown*, *garden leave*, *prime broker*, *edge*, *due diligence*), and US registration categories stay as the law
names them (*swap dealer*, *introducing broker*). The sample held six slips, all fixed: a clause that lost its subject
(*celui qui atteint … dont la cotation* → *…, celui dont la cotation*), a dropped clause opener in ch. 18 (*The design
point is that*), *dans un activité*, *tirages* for the chapter's *prélèvements*, a question without its inversion (*ne
tire-t-il*), and a definition on a bare noun. Three chapter openings (chs. 5, 16, 24) held one more: *types de
\omterm{…}{opérations d'initié}*, an elision the link hid. Residual: *a year N* is sometimes an ordinal in words (*la
dixième année*) and sometimes *l'année~10*.

## Build and gates

- `draft/pilot-quant-fr/build-s2/one_quant_book_16_desk_fr.pdf`: 373 pp (English 347). Errors 0, undefined 0, overfull
  0, nullfont 0, missing characters 0, invalid-in-math 0, zero-height 0, `.fls` 60/60. TeX Live 2026. Final build into
  `build/` at the close of session 2.
- `tools/check_translation.sh desk fr`: PASSED, gate 12 included. Book 16's block in `tools/check_latin_prose.py`
  allows figure nodes spelt the same in French (*pod*, *capital*, *options*, *prime broker*), the US registration
  categories and *due diligence*.
- Linker `--check`: every file matches the config. Links: fr 1,160 (924 course + 236 solutions), en 854.
- `pdfsweep.py` against the French Book 15 PDF: the top English-only word types are names (*Sharpe*, *Euler*,
  *Shapley*, *Brier*, *Nash*, *Cournot*, *Virtu*), desk English kept (*drawdown*, *pods*, *garden leave*, *repo*,
  *carry*, *hedge*) and code identifiers from listings (*comp*, *revenue*, *hard*). No English figure label.

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 5, 16, 24), the sweep and number reports.
- Figures: **every captioned figure (109)**, on a contact sheet; every repaired figure re-read, cropped from the rebuilt
  PDF (Fig. 1.1 twice). The first sheet missed the twelve figures of chs. 28–30 (their captions sat beside the picture,
  see below); `sheet.py` now finds a caption at the start of any line.
- Numbers: per line in the run directory before install (`numrun2.py`, new: `numrun.py` with numbers that only moved to
  a neighbouring line cancelled, and `\euro`/`\pounds` glued to a digit masked), then per file (`numfile.py`). Every
  remaining difference is *year N* or *day N* written as an ordinal, a 12-hour clock written as a 24-hour one (*21~h*
  for *9 p.m.*), a number word (*quatorze banques*), or a currency moved after the amount.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Content invented by the model | 1 | solutions 15: a *suivi de tendance* row with the momentum numbers, before the real momentum row |
| Content dropped | 2 | ch. 18 *Le principe de conception est que*; ch. 2 *, celui* |
| Figure collisions and overflows | 13 figures | Figs. 1.1, 4.1, 4.3, 11.3, 14.2, 16.4, 19.3, 25.3, 30.3: nodes on two lines, spread, tick labels wrapped (`figfix.py`) |
| English figure text | 2 figures | Fig. 19.4's team boxes (*product team*); Fig. 21.2's rows, CSV keys: French `yticklabels` over an explicit `ytick` list in the keys' order |
| Labels in English word order | 7 here, 6 in Book 17 | *(\$ million)* → *(millions de \$)* (`unitlabel_fr.py`, new) |
| Currency before the number | 0 here, 49 in Books 1 and 9, 29 in Book 17 | `\euro69\,900` → `69\,900~\euro`, `\pounds5\,429 million` → *5\,429~millions de livres* (`currency_fr.py`, new) |
| Definition on a bare lowercase noun | 8 here, 48 over eleven books | `\emph{culture du risque} est` → *La \emph{…}* (`bare_def_lower.py`, new, article from a gender table) |
| English left by the model | 3 | `\section{Exercises}`; a weekend-problem title; an English half-line beside its translation (solutions 23) |
| Overfull boxes | 9 | eight tables re-specified (`fixes.py`), a 1.5 cm tick label, *coordi\-nation* |
| Typography | 3 | plain spaces before `:`/`;` in a TikZ node; guillemets without `~` |

## English-canon defects

- **Fixed:** in chs. 28–30 of the English (and so of the French), `\omcaption` followed `\end{tikzpicture}` with no
  paragraph break, so the twelve captions ran on beside their pictures, *Figure* stranded at the right of the figure.
  Every other chapter breaks the paragraph. `\par` added after each `\end{tikzpicture}` (both languages, line counts
  kept).
- None found in the sampled passages' content.
