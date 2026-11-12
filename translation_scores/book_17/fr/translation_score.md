# Translation score: One Quant Book 17, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 17, The Industry: Firms, Roles and Careers (`industry`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 346 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 16–20 (session 2 of the Books 11–20 run), no subagents |
| **Canon** | English not verified: the English of Book 17 has had no fresh-reader verification pass, and solutions were not recomputed. One English defect was fixed on the way (below), and the same one in Book 9. |
| **Tokens** | `all: 346 calls, prompt 2153K + cache read 2050K, output 4679K (thinking 3532K), list price $2.79`. Coordinator: shared with Books 16–20; weekly plan 82 % after Book 16 and 83 % after this book's step 9 (see `sources/TRANSLATION_BOOKS_11-20_FR.md`) |
| **Scope** | 30 chapters + 30 solution files; glossary `sources/GLOSSARY_BOOK_17_FR.md` (+ `.run.md`); term config `tools/term_config/book17_fr.py` |

## Verdict

Fluent French for a book about firms, jobs and pay: *teneur de marché pour compte propre*, *plateforme multigérants*,
*salaire de base*, *rémunération totale*, *attribution différée*, *clause de good leaver*, *déchéance*, *prime
d'arrivée*, *équivalent certain*, *demandes de certification des conditions de travail* (labour condition
applications), *niveau de salaire*, *salaire en vigueur* (prevailing wage), *fonctions de contrôle*, *déclaration des
responsabilités*, *salles de trading partagées* (arcades), *programmes de trader financé*. Job titles the trade keeps in
English stay English (*trader*, *quant developer* in quotation, *sales-trader*, *garden leave*), as do the names of
filings, forms, US occupation codes and cited documents. The sample held five slips, all fixed: *y occupe-t-il* for
"employs", an inverted question left inside an indirect one (*de combien … dépasse-t-elle … chez chacun.*), *le cap
H-1B* for the *plafond* the chapter uses, a dropped article (*avec probabilité de*), and imperatives in exercises. Three
chapter openings (chs. 6, 19, 25) held two more: a stray *en* (*les 149 plus grands en employaient*) and *directeurs des
fonctions* for "the chief officers". Residual: *Codage* and *Programmation* both head coding exercises (25 files across
the series use the first, 465 the second).

## Build and gates

- `draft/pilot-quant-fr/build-s2/one_quant_book_17_industry_fr.pdf`: 361 pp (English 339). Errors 0, undefined 0,
  overfull 0, invalid-in-math 0, zero-height 0, `.fls` 60/60. TeX Live 2026. Nullfont 3 and missing characters 3, both
  also in the English build: one stray character in the code of Fig. 13.3, which prints correctly. Final build into
  `build/` at the close of session 2.
- `tools/check_translation.sh industry fr`: PASSED, gate 12 included. Book 17's block in `tools/check_latin_prose.py`
  allows the firm, exchange and city names in figure nodes, legends and `\foreach` lists, the node keys of Fig. 18.1,
  the job title *Trader* and `\text{base}` in a formula.
- Linker `--check`: every file matches the config. Links: fr 873 (735 course + 138 solutions), en 620.
- `pdfsweep.py` against the French Book 15 PDF: the top English-only word types are names (*Sharpe*, *York*, *Hong
  Kong*, *Virtu*, *Jane Street*, *Quadrature*), the names of filings, forms and US agencies (*RAUM*, *FINRA*, *XBRL*,
  *EDGAR*, *OEWS*, *IPEDS*), trade English kept (*bonus*, *package*, *hedge fund*, *drawdown*, *garden leave*, *good
  leaver*, *carried interest*), English glosses in parentheses (*revenue pool*, *fixed income*) and code identifiers.
  *revenue* is once the French participle (*est revenue au plus grand associé*). No English figure label.

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 6, 19, 25), the sweep and number reports.
- Figures: **every captioned figure (86)**, on a contact sheet (19 sheets); every repaired figure re-read, cropped from
  the rebuilt PDF (Figs. 14.2 and 28.1 twice).
- Numbers: per line in the run directory before install (`numrun2.py`): two restored years in ch. 3, three decimal
  points and a thousand in ch. 5, a `\pounds` amount in ch. 7. Then per file (`numfile.py`): every remaining difference
  is a currency glued to its number in the English (`\euro485.8`), an axis width or tick-label width changed by the
  figure repairs, a 24-hour clock time (*7~h* for *07:00*), or *2000+* in an English quotation printed as *2\,000*.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Section rejected by the checks after Haiku's last pass | 4 sections in 3 files | chs. 9, 12 (two), 14: the flagged line is English that stays (names of filings and forms), accepted with `accept.py --english-ok` |
| English left by the model | 2 | `\section{Exercises}` (ch. 9); an English half-line beside its translation (ch. 12) |
| Leaked prefix | 1 | ch. 19: a table row that came back starting `1=`, which its English twin does not; it stopped the build (*Misplaced \omit*); `sweeps_all.sh` now reports any line starting `N=` or `N|` whose English twin does not |
| English figure text from CSV keys | 30 tick lists, 2 `\foreach` | `ticklabels from table` prints the CSV's English keys: explicit French lists in the CSV's row order (`figfr.py`) |
| Figure collisions and overflows | 14 figures | tick labels touching (Figs. 12.3, 13.2, 28.1), y labels longer than the axis (Figs. 14.2, 18.4, 22.1, 27.2), a node and an x label (`figfix.py`, `figfix2.py`) |
| Currency before the number | 33 here, 53 in Books 1, 3, 8, 9, 11, 15 | `\$157\,698` → `157\,698~\$`, `\$182 milliards` → *182~milliards de dollars* (`currency_fr.py`, now also `\$`) |
| Labels in English word order | 6 here, 2 in Books 11 and 15 | *(\$ milliers)* → *(milliers de \$)* (`unitlabel_fr.py`, now also *milliers*) |
| Imperative in an exercise | 10 here, 3 in Books 3 and 13 | weekend-problem items *Définissez …*, *Citez …* → infinitive (`imperative_fr.py`'s verb list extended) |
| Overfull boxes | 15 | nine tables re-specified (`fixes.py`, `fixes2.py`), a running header (ch. 14's title shortened, solutions heading too), two axis widths |
| Typography and wording | 9 | ch. 11 *L'\emph{Inline XBRL}*, ch. 7 *Le \emph{FICC}*, guillemets, *directeur\\général* in a node |
| Inconsistent naming | 1 | Fig. 29.1's legend named the two programmes in English, Fig. 29.2 in French: French in both |

## English-canon defects

- **Fixed:** in solutions 12 of the English (and so of the French), `$1\,369/2\,100=\euro0.65$`: `\euro` is not a math
  command, so the PDF printed **£**0.65 million for Optiver's revenue per head, in euros. `\text{\euro}` in both
  languages (math still identical, gate 12). The same construction in Book 9's solutions 28 (`\times \euro400$`) was
  fixed the same way; both books' builds showed it as *invalid-in-math 2*, which earlier runs took for a harmless
  baseline.
- None found in the sampled passages' content.
