# Translation score: One Quant Book 4, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 4, Quantitative Methods (`methods`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled |
| **Date** | 2026-11-10 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 278 calls (265 translation, 13 repair); glossary, toolchain port and coordinator `claude-opus-5-5` (Opus 5.5) |
| **Canon** | English not verified: the English of Books 1–5 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 278 calls, prompt 1801K + cache read 1194K, output 3986K (thinking 3024K), list price $2.37`. Coordinator (estimate, no transcript count): about 170 tool calls and about 70 page images (the contact sheet of every figure), roughly 15–20M cache read, 1M cache write and 120K output, about $15–25 list; far more than the translation |
| **Scope** | 29 chapters + 29 solution files, 138 sections; glossary `sources/GLOSSARY_BOOK_4_FR.md` (+ `.run.md`); term config `tools/term_config/book4_fr.py` |

## Verdict

Fluent, precise mathematical French; the formulas came back byte-identical (the pilot's own math check re-run on every
installed file finds no difference). The prose is near-native in the sample, with occasional calques and stiff word order
(`la statistique $t$ $\tau$`, *quadratique en le nombre*). The sample and the sweeps found one wrong sense (ch. 18, *the hook's
ghost* rendered as the ghost of a 3.5 % return), one wrong-sense word (*rulebook* → *règlement de marché*), two dropped
clauses and two merged lines, all fixed; the unread remainder certainly holds more of each. A sentence-by-sentence pass is
what would lift it to the 95 tier.

## Build and gates

- `build/one_quant_book_04_methods_fr.pdf`: 372 pp (English 351). Errors 0, undefined 0, overfull 0, nullfont 0, missing
  characters 0, invalid-in-math 0, zero-height 0, `.fls` 58 / 58 on disk. TeX Live 2026.
- `tools/check_translation.sh methods fr`: PASSED (one-word tier advisory: names and cognates, *Feller*, *Girsanov*,
  *Feynman--Kac*, *Invariances*, *Estimation*, *Philox*, *Kelly*, *Hill*, *adjoint*).
- Linker `--check`: every file matches the config. Links: fr 2176 on 191 targets, en 1739 on 175; every English target
  reached. Over-frequencies read and accepted (right sense, the English writes `$H_0$` or a pronoun where the French repeats
  the term): *loi a priori / a posteriori* 52/0, *hypothèse nulle* 33/1, *conditionnement* (condition number, ch. 25 only)
  25/15, *loi stationnaire* 20/4, *équivalent certain* 12/1, *prix de réserve* 14/1, *moindres carrés ordinaires* 10/0.
  Curated: STOP seeded from `book4_en.py` (French equivalents, inert unless defined here) plus *bande* (the AD tape, ch. 28;
  also the hedging band of ch. 10); EXTRA_PROTECT *filtre bootstrap* (the particle filter, ch. 19) and *zéro-coupon*.
- `pdfsweep.py` (reference: the Earth Book 5 French PDF): 1,903 word types, all code identifiers, bibliography titles,
  names, desk English kept by the glossary (spread, forward, strike, payoff, desk) and accent-cut tokens (*march*, *raire*).
  One series-wide item: `\iqroles{trader, researcher}` prints the English role names (also in Book 3's French PDF).

## What was read

- Text: 20 passages (seed 1) and the openings of chapters 3, 16 and 27.
- Figures: **every captioned figure** (119 bands) on a contact sheet of the build (`draft/pilot-methods-fr/work/sheet/`),
  following Book 1's lesson; the four repaired pages re-read on the final build.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Plain space or no space before `: ; ? !` | 108 lines | `\item Quelles sont l'erreur type … ?` (all of ch. 11's problem); 3 the script put inside math, reverted |
| `\index{}` key broken across a line | 11 | `\index{propriété de\nMarkov forte}` |
| Missed elision, inside a line and across a break | 16 | `Le \emph{exposant`, `que estime`, `quitter le\nintervalle` |
| Definition on a bare noun | 13 | `\emph{Winsorisation} de niveau` → `La \emph{winsorisation}` |
| Percent spacing (`\,\%`, `5\%`) | 7 lines | `4.5\,\%` → `4.5~\%` |
| Decimal comma | 10 lines | ch. 11 `2,32`, ch. 26 `0{,}9` |
| `\cref` article missing or of the wrong gender | 9 | sentence-initial `\Cref{fig}` ×5, `Par \cref{thm}`, `au \cref{tut}` (a *Section*), repair.py's `du \cref{prop}` |
| Ordinals | 16 | `2e éd.`, `10e centile`, `336e` → `\up{e}`; `premier juin`, `1~juin` → `1\up{er} juin` (×3) |
| English left in titles, headings, legends, labels | 13 | `Weekend problem --- overlapping positions…`, `\section{Problem: Two Measures, One Price}`, ch. 5 numeraire table (kept English by the run: the draw check forbade the model to touch it), 4 legends, Fig. 18.1 axis labels, `\foreach` *close*, `$t$ (years)` |
| Lost, merged or added text | 7 | ch. 24 sentence *The lasso of chapter 16 is the textbook case* dropped; s05 clause dropped; ch. 16 and ch. 7 lines merged with English left on the next line; s19 *30* dropped; ch. 18 *the hook's ghost* → *le fantôme de ce rendement de 3.5 %* (wrong sense); repair.py turned ch. 1's *Interview questions* heading into *Exercices* |
| Wrong word or sense | 3 | ch. 9 *rulebook* → *règlement de marché* (now *politique d'investissement*); *la gamma* (×9, now *le gamma*); ch. 6 *aplatissement* vs *kurtosis* |
| Chapter title and solution header disagreeing | 4 | ch. 1, 12, 25, 27 |
| Figure collisions | 2 | Fig. 23.3 legend over the curve (moved below), Fig. 27.3 y-label taller than the plot |
| Overfull boxes from longer French | 5 | ch. 1 table header; ch. 15, 17, 25, 29 paragraphs with long inline formulas (reworded) |
| Consistency | 8 | `germe fixé` → `graine fixée` (4), `ECB` → `BCE` (2), `one-two-one` → `1-2-1` (to match the legend and solutions), clock times `15:50`/`09:30` → `15~h~50`/`9~h~30` |

## `NUMDIFF` differences accepted

16 files at first; the real losses (s05, s19, ch. 24 and the decimal commas) were fixed. The final residual on `parts/`,
12 files, all accepted:

- ch. 1: `ten to four` → `15~h~50` and `09:30` → `9~h~30`; ch. 2: *One minus* → *Le complément à 1*;
- ch. 19 and s19: `100 times the Q` → *un $Q$ cent fois plus grand*; ch. 29: *won 30 of the last 30* → *les 30 dernières*;
- ch. 20 and s20: `one-two-one` → `1-2-1`; ch. 23: *Twenty-one* → *21*, *each extra 1 %* → *chaque point*, and Fig. 23.3's
  legend position (`(0.03,0.97)` → `(0.5,-0.3)`, two columns);
- s15, s17, s23: number words written as digits (*fourth moment* → *moment d'ordre 4*, *near one* → *près de 1*, *phase one*
  → *phase 1*).

## Conventions

Desk usage per the run file: French term where French desks use one (*erreur type*, *demi-vie*, *loi a priori*,
*rétrécissement*), English otherwise (bootstrap, lasso, ridge, elastic net, spread, payoff, drawdown). Decimal point kept,
`~:` `~;` `~?` `~!`, `5~\%`, an article before `\cref` by the gender of the printed noun (*la Figure*, *le Théorème*, *la
Proposition*, *l'Exercice*, *la Section* for a tutorial), `(livre~N, chapitre~M)`, ordinals with `\up`, amounts as `1.80~\$`.
*le gamma* (masculine) throughout. Interview questions are sometimes in the *vous* imperative (*Énoncez…*), exercises in
the infinitive.

## Upgrade path

A sentence-by-sentence pass over all 58 files, then re-score and update the `Model` row.

## Main-session edits after close (2026-11-10)

Shared fixes after the coordinators closed, applied to every French book and rebuilt 0/0/0 (TeX Live 2026): cleveref conjunctions in French (`et`, `à`; `\cref{a,b}` had printed "and"); a running-header mark not split by `\omTocMark` printed beside the full-width `\truncate` box, wrapping the book title; the last index page balanced by multicol no longer runs into the foot (`\maxbalancingoverflow` 0 in the index); `\iqroles` translated by script where English was left; gate 12 now also compares every math span with English on disk.

Book 4 specifics: 58 `\iqroles` translated. Final: 372 pp, 0/0/0, 58/58 files.
