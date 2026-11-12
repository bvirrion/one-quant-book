# Translation score: One Quant Book 14, French (`fr`)

| Field | Value |
|-------|--------|
| **Book** | One Quant Book 14, Networks, Hardware and Trading Infrastructure (`networks`) |
| **Language** | French (`fr`) |
| **Overall score** | **88 / 100**, sampled: 20 passages, seed 1, not read in full |
| **Ship status** | **Pilot tier**: gates green; not read sentence by sentence; figures sampled (in fact all read, on a contact sheet) |
| **Date** | 2026-11-12 |
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section, 304 calls (translation, retries and repairs); glossary and coordinator `claude-opus-5-5` (Opus 5.5), one coordinator for Books 11–15, no subagents |
| **Canon** | English not verified: the English of Book 14 has had no fresh-reader verification pass, and solutions were not recomputed. |
| **Tokens** | `all: 304 calls, prompt 1898K + cache read 1669K, output 3706K (thinking 2669K), list price $2.25`. Coordinator: shared with Books 11–15, see `sources/TRANSLATION_BOOKS_11-20_FR.md` |
| **Scope** | 29 chapters + 29 solution files; glossary `sources/GLOSSARY_BOOK_14_FR.md` (+ `.run.md`); term config `tools/term_config/book14_fr.py` |

## Verdict

Fluent technical French for trading networks: *trame*, *commutateur cut-through*, *duplication de couche 1*, *horloge grand
maître*, *horloge transparente*, *contournement du noyau*, *salle d'interconnexion*, *facteur de tracé*, *plancher de latence*,
*point de terminaison privé*, *mise en concurrence des routes*; vendor, building and product names stay as written, and desk
English is kept where the trade keeps it (*store-and-forward*, *wire-to-wire*, *ticker plant*, *feed handler*, *tap*). The sample
held four slips, all fixed: *qu'une fois le dernier bit est arrivé*, *il est un compilateur*, a missing `~` before a colon, and
a *99e centile* without `\up{e}`. It also showed the handoff rendered three ways (*point d'échange*, which in a networks book reads
as an internet exchange point; *point de transfert*; *point de remise*); now *point de remise* throughout. Three chapter openings
(chs. 10, 19, 27) held one more: *le long du géodésique* (the noun is feminine), fixed in three places. Residual: the firm is
*la société* 209 times and *la firme* 126 times, both correct French desk usage, not harmonised.

## Build and gates

- `draft/pilot-quant-fr/build-s1/one_quant_book_14_networks_fr.pdf`: 373 pp (English 349). Errors 0, undefined 0,
  overfull 0, nullfont 0, missing characters 0, invalid-in-math 0, zero-height 0, `.fls` 58/58. TeX Live 2026. Final build
  into `build/` at the close of session 1, after the series-wide sweeps: 372 pp, 0/0/0.
- `tools/check_translation.sh networks fr`: PASSED, gate 12 included. The one-word advisory tier lists 23 cognates and
  names (*cycle*, *cage*, *obstacle*, *quantile*, *Tokyo*, `us-east-1`); Book 14's identifier block in
  `tools/check_latin_prose.py` allows seven chart tokens (`use`, `az`, `participant`, `zone`, `colocation`, `ticker`, `plant`).
- Linker `--check`: every file matches the config.
- Links: fr 853 (622 course + 231 solutions), en 685.
- `pdfsweep.py` against the French Book 10 PDF: the top English-only word types are cognates (*fibre*, *site*, *ports*,
  *routes*), place names (*Aurora*, *Carteret*, *Mahwah*, *Slough*), units (*gbit*) and desk English kept (*wire-to-wire*,
  *gossip*, *pipeline*, *store-and-forward*).

## What was read

- Text: 20 passages (seed 1), three chapter openings (chs. 10, 19, 27), the sweep reports.
- Figures: **every captioned figure (97)**, on a 20-page contact sheet; every repaired figure re-read, cropped from the
  rebuilt PDF, twice for Figs. 9.1, 13.3, 15.3, 18.2 and 28.1.
- Numbers: per line in the run directory (`numrun.py`) before install, then per file (`numfile.py`) after; every remaining
  difference is a figure coordinate, a column width, an inline table that replaced a CSV column, or a line wrap.

## Defects found and fixed, by class

| Class | Count | Example |
|---|---:|---|
| **Wrong-sense rendering** | 1 term, 15 places | the handoff as *point d'échange* (an IXP in French networking) and *point de transfert*; now *point de remise* |
| English figure text | 43 `sites` lines + 2 | the frame labels of Fig. 1.x, the IGMP figure, Fig. 15.2's designs; on the contact sheet: Fig. 18.3's ticks (*endpoint*, *edge*), Fig. 24.3's *London* |
| Figure collisions and overflows | 13 | Figs. 4.2, 6.3, 7.1, 9.1 (cables drawn from a fixed x through the wider French node), 13.3, 15.2, 15.3, 18.2, 19.1, 21.3, 22.3, 28.1, and a legend in ch. 2 |
| Legend split by a comma | 1 | Fig. 13.3, braced |
| Overfull boxes | 13 | eight tables re-specified, one hyphenation, one legend, one TikZ text, two `\sloppy` |
| Typography outside math | 133 lines | |
| English role names in `\iqroles{}` | 61 lines | |
| Weekend-problem part labels | 30 lines | |
| Definition opening on a bare noun | 17 | `bare_def_fix.py` (13) and by hand (*L'IGMP snooping*, *L'incast*, *La virtualisation d'E/S à racine unique*, *L'anycast*) |
| Ordinals without `\up{e}` | 22 in Book 14 | *99e centile* → `99\up{e}~centile`; run over every French book (80 in all) |
| Gender and grammar (sample, openings) | 4 | *le long de la géodésique*, *qu'une fois le dernier bit arrivé*, *c'est un compilateur* |

## English-canon defects (reported, not fixed)

None found in the sampled passages.
