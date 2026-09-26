# 13. Text: From Bag of Words to Embeddings — brief and source ledger

## Brief

- **Hook.** A headline says a company ``beat'' and its shares fall; a dictionary scores it positive, a model trained on returns learns that ``beat but guided lower'' is negative, and neither knows which of three companies called Apex the headline is about.
- **Sections.** From documents to vectors; Sentiment from dictionaries and from returns; Topics and events; Embeddings; Entity linking to securities.
- **Defines.** tokenisation, bag of words, n-gram, term frequency--inverse document frequency, word embedding, topic model, latent Dirichlet allocation, named-entity recognition, entity linking, event extraction.
- **Uses (defined earlier).** dictionary method (B7.12), document embedding (B7.12), sentiment score (B7.12), machine-readable news (B8.17), news reaction window (B8.17), security master (B7.4), ticker change (B7.4), identifier mapping (B7.4), point-in-time data (B7.3), logistic regression (ch4), lasso (B4.16), singular value decomposition (B4.25), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Generate a synthetic news corpus from templates (companies with aliases and ticker changes from firm.secmaster, planted events and sentiment, negations and guidance clauses) tied to firm.synthmkt returns; compare a dictionary, tf-idf with a regularised logistic regression, a return-supervised word list in the style of SESTM and SVD embeddings; link mentions to permanent identifiers point in time. Data: synthetic corpus; a small sample of public-domain EDGAR 8-K item headings for tokenisation examples.
- **Build.** `firm.textml`: tokeniser, n-gram bag of words and tf-idf, dictionary and return-supervised sentiment, SVD word embeddings, a small LDA through scikit-learn, and a point-in-time entity linker on firm.secmaster aliases; Python.
- **Weekend problem.** Which Apex? -- named result: entity-linking precision with and without point-in-time aliases, and the IC of the return-supervised text model against the dictionary's.
- **Facts to verify.** Tetlock 2007 giving content to investor sentiment (JF); Loughran and McDonald 2011 when is a liability not a liability? (JF) and the licence of their word lists; Ke, Kelly and Xiu 2019 predicting returns with text data (NBER WP 26186); Blei, Ng and Jordan 2003 latent Dirichlet allocation (JMLR); Mikolov et al. 2013 word2vec (arXiv/NeurIPS); Gentzkow, Kelly and Taddy 2019 text as data (J. Economic Literature); SEC EDGAR access and fair-access policy (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | P. C. Tetlock, "Giving content to investor sentiment: the role of media in the stock market", Journal of Finance 62(3) 2007 | Crossref/OpenAlex record | https://doi.org/10.1111/j.1540-6261.2007.01232.x | 2026-09-25 | title, journal, year as registered | omsources |
| F2 | T. Loughran, B. McDonald, "When is a liability not a liability?", Journal of Finance 66(1) 2011: general word lists misclassify financial words; almost three-fourths of the Harvard dictionary's negative words are typically not negative in 10-Ks (1994-2008) | Crossref/OpenAlex record | https://doi.org/10.1111/j.1540-6261.2010.01625.x | 2026-09-25 | abstract: "almost three-fourths of the words identified as negative by the widely used Harvard Dictionary are words typically not considered negative in financial contexts" | text sec. 2; iq 2; omsources |
| F3 | Z. T. Ke, B. T. Kelly, D. Xiu, "Predicting returns with text data", NBER WP 26186 2019: a supervised framework building a sentiment score adapted to return prediction | NBER via Crossref/OpenAlex | https://doi.org/10.3386/w26186 | 2026-09-25 | abstract: "our supervised learning framework constructs a sentiment score that is specifically adapted to the problem of return prediction" | text sec. 2; build stretch; omsources |
| F4 | M. Gentzkow, B. Kelly, M. Taddy, "Text as data", Journal of Economic Literature 57(3) 2019 | Crossref/OpenAlex record | https://doi.org/10.1257/jel.20181020 | 2026-09-25 | title, journal, year as registered | omsources |
| F5 | D. M. Blei, A. Y. Ng, M. I. Jordan, "Latent Dirichlet allocation", NIPS 14 (MIT Press, 2002): each document a mixture of topics | Crossref/OpenAlex record | https://doi.org/10.7551/mitpress/1120.003.0082 | 2026-09-25 | abstract: "each document is generated as a mixture of topics" | def. LDA; omsources |
| F6 | T. Mikolov, K. Chen, G. Corrado, J. Dean, "Efficient estimation of word representations in vector space", arXiv:1301.3781 2013 | arXiv API | https://arxiv.org/abs/1301.3781 | 2026-09-25 | title and abstract: continuous vector representations of words from very large data sets | def. word embedding; omsources |

## EXCLUDED

- Every information coefficient, linking rate, cosine and topic is computed on firm.textml.news_corpus (synthetic headlines with planted effects) and tested in code/ml/13-text-from-bag-of-words-to-embeddings/tests/test_solutions.py. Apex and every other company name are invented.
- Blei, Ng and Jordan's JMLR 2003 article (planned): no registry record retrieved; the NIPS 2002 version is cited instead.
- Loughran-McDonald word-list licence (planned): not needed, the chapter's lists are hand-built for the synthetic corpus and the published lists are not used.
- Public-domain EDGAR 8-K item headings for tokenisation examples, and the SEC EDGAR fair-access policy (planned dated box): dropped, the tokenisation example uses a synthetic headline and the chapter downloads nothing.
- The brief's firm.synthmkt returns: replaced by a reaction return per headline (planted effect plus noise), which is what the scores are compared on.
