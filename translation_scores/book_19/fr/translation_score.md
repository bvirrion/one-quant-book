# Translation score: One Quant Book 19, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 19, Interviews II: Markets, Trading Games and the Final Round (`interviews-2`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; the book has no figures |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 184 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 16–20 (session 2 of the Books 11–20 run), no subagents |
| **Canon** | English read by the expert readers of 2026-11-03 (`sources/BATCH_BOOKS_18-20.md`); answers not recomputed. **One English-canon defect fixed on the way, also in Book 18**: thousands written with a comma (below). |
| **Tokens** | `all: 184 calls, prompt 1438K + cache read 1134K, output 2586K (thinking 1672K), list price $1.59`. Coordinator: shared with Books 16–20; weekly plan 84 % after Book 18 and 84 % after this book's step 9 (see `sources/TRANSLATION_BOOKS_11-20_FR.md`) |
| **Scope** | 21 chapters + 21 answer files, preface, tracks table, 7 generated files in `parts/interviews-2/generated/fr/`; glossary `sources/GLOSSARY_BOOK_19_FR.md` (+ `.run.md`); no term links (the interview books are not in the linker) |

## Verdict

Desk French for market-making games, derivatives arithmetic and the final round: *cours acheteur*, *cours vendeur*,
*fourchette*, *cotation*, *swaption payeuse*, *repo implicite*, *swap à départ différé*, *ordre de balayage
intermarchés*, *dépassements* (VaR exceptions), *barème*, *entretiens blancs*; trade English kept where the desk keeps
it (*straddle*, *butterfly*, *risk reversal*, *fair value*, *carry*, *trade-through*). The interviewer's lines
(`\ivsays`) stay in *vous* imperatives, answers in the infinitive or *on*. The sample held two slips, both fixed: *Quelle
position prendriez-vous* for "What is the position" (a question about what the payer-minus-receiver *is*), and *avec une
probabilité d'un demi*. Three chapter openings (chs. 4, 12, 19) held one more: *ce qu'un recruteur attend d'avoir en
tête* (the interviewer expects the candidate to have the numbers in mind). Residual: ch. 3's answers render "lean" (to
skew one's quotes) as *pencher* / *penchant*, consistently but not as a desk would.

## Build and gates

- `draft/pilot-quant-fr/build-s2/one_quant_book_19_interviews_2_fr.pdf`: 383 pp (English 348). Errors 0, undefined 0,
  overfull 0, invalid-in-math 0, zero-height 0, `.fls` 44/42 (the preface and the tracks table). TeX Live 2026. Final
  build into `build/` at the close of session 2.
- `tools/check_translation.sh interviews-2 fr`: PASSED, gate 12 included.
- `tools/check_interview_book.py interviews-2 --final`: GREEN (667 answers); `--cross`: GREEN.
- `pdfsweep.py` against the French Book 15 PDF: 392 English-only word types, the top ones the tag words that stay
  (*junior*, *hedge fund*), names (*Sharpe*, *Kelly*, *Euler*), trade English kept (*straddle*, *smile*, *carry*,
  *funding*, *drawdown*, *butterfly*, *contango*), words that are also French (*obligation*, *inflation*,
  *illustration*, *stocks*, *coins*, *rival*) and label text (*pitches*). No English sentence.

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 4, 12, 19), the sweep, number and PDF-sweep reports.
- Numbers: per line in the run directory (`numrun2.py`, 628 lines, most of them the decimal commas below) and per file
  after the sweeps (`numfile.py`, 27 files): what remains is number words (*vingt ans*, *le tiers*), "1 cent" said *le
  cent*, and the same quantity said another way (*par point de volatilité* for "per unit of volatility over 100").

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Thousands with a comma (English canon) | 595 lines, English and French | the English wrote `1,000` and `\$40,000` (math `8{,}000` too), against `sources/INTERVIEW_BOOKS.md` (thin space); in math it printed "1, 000", and in French it reads as 1. `comma_thousands.py` makes the same change on the same tokens in both languages, so gate 12 holds |
| Decimal commas | 154 lines | some sections came back with French decimal commas (`1,10`, `4,5`); `fix_common.py` restores the series' point once the English thousands no longer confuse it. It also turned `d_{1,2}` into `d_{1.2}` (gate 12 caught it; fixed by hand) |
| Thin spaces, punctuation | 358 lines | `5\,\%` and a plain space before `?`, `:`, `;` (`typo_apply.py`) |
| Translated command | 1 | `\chapitre{Faire un marché}` for `\chapter`: it stopped the tracks script; `cmd_twin.py` (new) reports any command no English file uses, and found no other in Books 1–19 |
| Dead links in the tracks table | 21 here, 21 in Book 18 | the punctuation sweep put `~:` inside the generated table's `\hyperref[ch:…]` labels; the log does not count a dead `\hyperref`. `sweeps_all.sh` now makes the table again after the fixers |
| Imperative in an answer | 5 + 60 lines | `answer_imperative.py`, `vous_imperative.py` (now keeping `\ivsays` and quoted speech, and with the *-dre*/*-oir* verbs it had turned into *vender*, *prévoyer*; its *-issez* rule had made *lair* of *laissez*, in Books 18 and 19, fixed) |
| Currency before the number | 19 | `currency_fr.py` |
| Tilde for thousands | 74 | `690~000~\$` → `690\,000~\$` (`tilde_thousands.py`) |
| Overfull boxes | 6 | the tracks table (a wrapping first column for French, in `tools/make_interview_tracks.py`), the growth/inflation table of answers 16, a mock-interview round title, three `sloppypar` paragraphs (`fixes.py`) |
| Wording | 3 | the sample's two and the opening's one above |

## English-canon defects

- **Fixed:** Books 18 and 19 wrote thousands with a comma (Book 18 99 tokens, Book 19 432), against their own rules
  (`sources/INTERVIEW_BOOKS.md`: "thin space for thousands (`184\,756`)") and the series' 2026-09-29 sweep, which
  predates them. In math, `1,000` prints with a punctuation space after the comma. Fixed in both languages by
  `draft/pilot-quant-fr/comma_thousands.py`; English builds rechecked at the session close.
