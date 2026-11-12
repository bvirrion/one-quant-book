# Translation score: One Quant Book 20, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 20, Interviews III: Code (`interviews-3`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; the book has no figures; its 399 listings are the English files, untouched (gate 12) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 193 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 16–20 (session 2 of the Books 11–20 run), no subagents |
| **Canon** | English read by the expert readers of 2026-11-03 (`sources/BATCH_BOOKS_18-20.md`); answers and program outputs not re-run. No English defect found on the way. |
| **Tokens** | `all: 193 calls, prompt 1849K + cache read 1392K, output 2808K (thinking 1590K), list price $1.79`. Coordinator: shared with Books 16–20; weekly plan 84 % after Book 19 and 84 % after this book's step 9 (see `sources/TRANSLATION_BOOKS_11-20_FR.md`) |
| **Scope** | 9 chapters + 9 answer files, preface, tracks table; glossary `sources/GLOSSARY_BOOK_20_FR.md` (+ `.run.md`); no term links (the interview books are not in the linker) |

## Verdict

Clear French around code that stays English: *pointeur pendant*, *référence de transmission*, *objet dans un état
déplacé*, *comportement indéfini*, *faux partage*, *pile monotone*, *tas indexé*, *produit bande passante-délai*,
*antijointure*, *grand livre en partie double*. Identifiers, tool messages (*heap-use-after-free*, *terminate called*),
listing code and the listing files' paths stay as printed; listing captions are French. Answers use the infinitive or
*on*, as the series card asks. The sample held one slip, fixed: *le mauvais côté du carnet pour le côté acheteur* for
"the wrong end of the book for bids". Three chapter openings (chs. 2, 7, 8) held three more: *Corrigez-le* for "Fix
each" (two cases), and *vous* / *vos* in two chapter summaries, which speak in *on*. The answer heading of ch. 2 had
kept the English title (*Python and pandas*), which no gate reports.

## Build and gates

- `draft/pilot-quant-fr/build-s2/one_quant_book_20_interviews_3_fr.pdf`: 421 pp (English 391). Errors 0, undefined 0,
  overfull 0, invalid-in-math 0, zero-height 0, `.fls` 20/18 (the preface and the tracks table). TeX Live 2026. Final
  build into `build/` at the close of session 2.
- `tools/check_translation.sh interviews-3 fr`: PASSED, gate 12 included (every `\omcode` triple and `\texttt`
  identifier as the English). The prose gate flagged the tracks row of ch. 3, *C++*, identical in both languages: it now
  skips a `\hyperref` row.
- `tools/check_interview_book.py interviews-3 --final`: GREEN (390 answers); `--cross`: GREEN.
- `pdfsweep.py` against the French Book 15 PDF: 1,406 English-only word types, nearly all code (*include*, *cout*,
  *mutex*, *noexcept*, *constexpr*), the listing paths printed above each listing (*interviews*, *algorithms*,
  *debugging*), sanitizer and compiler messages, and the tag words that stay (*junior*, *hedge fund*). In prose, outside
  `\texttt`: four `\index` entries left English (*monotone stack*, *dynamic programming*, *sliding window*, *augmenting
  path*), fixed by `index_fr.py`, and *slots* for Python's `__slots__` instances (kept).

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 2, 7, 8), the sweep, number and PDF-sweep reports.
- Numbers: per line in the run directory (`numrun2.py`, 115 lines) and per file after the sweeps (`numfile.py`, 9
  files): decimal commas the sweep restored, number words (*une vingtaine* for "about 20", *aucune* for 0).

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Question tags, tracks | 110 lines | `ivfix_fr.py` |
| Punctuation and spacing | 379 lines | `typo_apply.py` |
| Imperative in an answer | 8 + 77 lines | `answer_imperative.py`, `vous_imperative.py`; it had made *parcourer* of *parcourez* (two lines, fixed) and did not know 17 capitalised verbs (*Triez*, *Séparez*, *Scindez*, …; now listed) |
| Decimal commas | 11 lines | `fix_common.py` |
| English `\index` entries | 4 | `index_fr.py`'s table extended |
| English answer heading | 1 | solutions 2: *Chapitre … --- Python and pandas* and its running head |
| Overfull boxes | 17 | long `\texttt` identifiers in French lines: `\emergencystretch` in the French entry file (17 → 3), the three left wrapped in `sloppypar` (`fixes.py`) |
| Wording | 4 | the sample's one and the openings' three above |

## English-canon defects

None found in the sampled passages, the openings or the reports.
