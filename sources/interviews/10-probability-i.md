# 10. Probability I — brief and source ledger

## Brief

- **Hook.** 'I roll two dice and tell you at least one is a six. What is the chance both are?' Half the room says one sixth, a few say one eleventh, and one candidate asks how the interviewer came to say it, which is the only question that settles the answer.
- **Sections.** Counting: products, arrangements, multisets and the complement; Conditioning and Bayes: the tree, the table and the ratio; Symmetry arguments; Paradoxes and what they test: the information in how you learned a fact.
- **Defines.** symmetry argument, complementary counting.
- **Uses (defined earlier).** conditional expectation (B4.1), Bayesian update (B2.30), prior distribution (B4.14), posterior distribution (B4.14), sanity check (ch5).
- **Question bank.** 14 questions, 5/5/4. Families: counting with and without order (cards, orders in a queue, seat assignments); complementary counting (at least one, birthday-type collisions among order identifiers); conditional probability with a stated protocol (the two-dice-and-a-six family and its protocol-dependent answers); Bayes with base rates (a signal that fires on a fraudulent account, a model flagging a bad fill); symmetry (the chance a given card is the first ace, ties in a random ranking); a card-game variant of a classic paradox (origin cited); a geometric probability question. Roles: trader 7, researcher 5, mle 1, risk 1, bank 1. Firms: market maker 6, proprietary firm 3, systematic fund 2, any 4.
- **Facts to verify.** origins of the classic problems used as variants: Bertrand's box paradox (Bertrand 1889), the boy-or-girl problem (Gardner 1959, Bar-Hillel and Falk 1982 on protocol), the birthday problem (von Mises 1939), Monty Hall (Selvin 1975) -- bibliographic, via Crossref or library catalogues.
- **Data.** Figures: one schematic (a probability tree for the protocol question, two protocols side by side). Code: iv_prob1.py (exact answers by exhaustive enumeration with Fraction, every question; simulation over seeds for each conditional-protocol question).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Bertrand, Calcul des probabilites, Gauthier-Villars, 1889 (the box paradox) | Open Library catalogue | https://openlibrary.org/works/OL5031072W | 2026-09-29 | title, author, first publication 1889 | section 4; omsources |
| F2 | Gardner featured the two-children problem in his May 1959 Mathematical Games column in Scientific American | Wikipedia, Boy or girl paradox (raw text, as a map to the primary reference) | https://en.wikipedia.org/w/index.php?title=Boy_or_girl_paradox&action=raw | 2026-09-29 | "when Martin Gardner featured it in his May 1959 Mathematical Games column in Scientific American" | section 4; omsources |
| F3 | Bar-Hillel and Falk, Some teasers concerning conditional probabilities, Cognition 11(2), 109-122, 1982 | Crossref | https://api.crossref.org/works/10.1016/0010-0277(82)90021-X | 2026-09-29 | title, journal, volume, issue, pages | section 4; omsources |
| F4 | Selvin's 1975 letter to The American Statistician describing the three-door problem; the issue's Letters to the Editor, vol. 29(1), pp. 67-71 | Crossref (issue item); Wikipedia Monty Hall problem (attribution) | https://api.crossref.org/works/10.1080/00031305.1975.10479121 | 2026-09-29 | Crossref: "Letters to the Editor", 29, 1, 67-71; Wikipedia: "Selvin wrote a letter to the American Statistician in 1975" | section 4; omsources |

## EXCLUDED

- von Mises 1939 (birthday problem origin): not cited; the collision question is a variant needing no attribution.

