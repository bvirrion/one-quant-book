# Translation score: One Quant Book 18, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 18, Interviews I: Maths, Probability and Speed (`interviews-1`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures all read (11, on a contact sheet) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 248 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 16–20 (session 2 of the Books 11–20 run), no subagents |
| **Canon** | English not verified beyond the two expert-reader rounds of 2026-11-03 (`sources/BATCH_BOOKS_18-20.md`); answers not recomputed. One English-canon defect fixed during Book 19 (comma thousands, below). |
| **Tokens** | `all: 248 calls, prompt 1984K + cache read 1308K, output 3177K (thinking 2010K), list price $2.00`. Coordinator: shared with Books 16–20; weekly plan 83 % after Book 17 and 84 % after this book's step 9 (see `sources/TRANSLATION_BOOKS_11-20_FR.md`) |
| **Scope** | 33 chapters + 33 answer files (chapter 1 has none), preface, tracks table, 36 generated drill files in `parts/interviews-1/generated/fr/`; glossary `sources/GLOSSARY_BOOK_18_FR.md` (+ `.run.md`); no term links (the interview books are not in the linker) |

## Verdict

Natural French for interview questions and their answers: *variables indicatrices*, *espérance*, *temps d'arrêt*,
*principe de réflexion*, *sommes de Nim*, *induction à rebours*, *stratégie mixte*, *paradoxe de l'inspection*,
*algorithme des cotes*, *erreurs types*, *processus autorégressif d'ordre 1*. Questions address the candidate with
*vous* and imperatives (*Calculez*, *Montrez*, *Estimez*); answers, *iqwrong* and *iqwhy* lines and the chapter
summaries use the infinitive or *on*, as the series card asks. The question tags are the card's fixed table (roles,
*teneur de marché*, *toutes*, *junior*, *confirmé*). The sample held three slips, all fixed: *Julius Caesar* left in
English, *un signal leur est sans lien* for "a signal is unrelated to them", and an *iqwrong* opening on a participle
(*En utilisant …*). Three chapter openings (chs. 9, 15, 22) held two more: *étalez-les* after *et* (*et les
étalez*) and *un mélange* for "a mix" in game theory (*une stratégie mixte*). A label quoted in a question (*«~mixte~»*)
came back as *«~mélange~»* in its answer (ch. 16), found from the PDF sweep and fixed.

## Build and gates

- `draft/pilot-quant-fr/build-s2/one_quant_book_18_interviews_1_fr.pdf`: 423 pp (English 393). Errors 0, undefined 0,
  overfull 0, invalid-in-math 0, zero-height 0, `.fls` 67/65 (the preface and the tracks table are read from `fr/` but
  are not chapter files). TeX Live 2026. Final build into `build/` at the close of session 2.
- `tools/check_translation.sh interviews-1 fr`: PASSED, gate 12 included. The gate's "solutions missing" check now
  skips a chapter with no English answer file (chapter 1), which it used to flag.
- `tools/check_interview_book.py interviews-1 --final`: GREEN (732 answers); `--cross`: GREEN. Its duplicate-label scan
  now skips the language subdirectories, which held the French twins of every label.
- `pdfsweep.py` against the French Book 15 PDF: 442 English-only word types, the top ones the tag words that stay
  (*junior*, *hedge fund*), words that are also French (*chance*, *faces*, *triangle*, *modulo*, *optimal*), names
  (*Sharpe*, *Poisson*, *Bayes*, *Newton*, *Markov*, *Hoeffding*, *Wishart*, *Welford*) and `\index` terms. After the
  `ivgen_fr.py` fix below no drill family is English.

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 9, 15, 22), the sweep and number reports, the PDF sweep.
- Figures: all 11, on a contact sheet (3 sheets); Fig. 7 re-read, cropped from the rebuilt PDF.
- Numbers: per line in the run directory (`numrun2.py`, 89 lines): every difference is a number word (*deux*, *nulle*
  for 0), a 24-hour clock time or a spacing change, except one *60~000* (a tilde for the thousands space), fixed and
  swept series-wide.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| Question tags, generated paths | 192 lines | `ivfix_fr.py`: the `\iqroles`/`\iqfirm`/`\iqlevel` words from the card's fixed table, `\input{…/generated/…}` pointed at `generated/fr/` |
| English drill families | 43 files | `ivgen_fr.py`'s family regex lacked `re.M`, so every generated drill kept its English family name; fixed and re-run |
| Imperative in an answer | 21 + 36 lines here, 34 over the series | `answer_imperative.py` (line start) and `vous_imperative.py` (anywhere in an answer, `\ivtrains` and `\iqfollow` answers): *Utilisez …* → *Utiliser …*, *N'oubliez pas* → *Ne pas oublier* |
| English `\index` entries | 24 lines | *Legendre's formula*, *Chinese remainder theorem* left English (`index_fr.py`, a table) |
| Tilde for thousands | 2 here, 5 in Books 1, 2, 6, 14 | `60~000` → `60\,000` (`tilde_thousands.py`) |
| TeX accents | 4 files | `\'e`, `\'o` in answers 08, 11, 17, 22 → *é*, *ó* |
| Overfull boxes | 6 | five paragraphs whose math cannot break in French wrapped in `sloppypar`; ch. 19's running header, 1 pt past the width truncate lets through (`\texorpdfstring` with a narrower space) |
| Figure collision | 1 | Fig. 7: *première coupure* ran into the ½ tick label (moved down) |
| Wording | 6 | the sample's three and the openings' two above; the *mixte*/*mélange* label pair |

## English-canon defects

- **Fixed (found during Book 19):** the English wrote thousands with a comma (99 tokens: `1,000 observations`,
  `\$1,048,576`), against `sources/INTERVIEW_BOOKS.md` (thin space); in French each one reads as a decimal (19 were
  left in the French, *1,023~\$*). `draft/pilot-quant-fr/comma_thousands.py` gave both languages `\,` (87 lines).

## Found after this book's close (during Book 19)

- The tracks table's 21 `\hyperref` labels carried `~:` from the punctuation sweep, so its links were dead; the build
  log does not count a dead `\hyperref`. Made again; `sweeps_all.sh` now makes the table after the fixers.
- *lair la case vide* (answers 3): `vous_imperative.py`'s *-issez* rule on *laissez*; fixed, rule narrowed.
