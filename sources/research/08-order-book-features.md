# 8. Order-Book Features — brief and source ledger

## Brief

- **Hook.** Three lots rest at the best bid and forty at the best ask. Which way does the next mid-price change go, and with what probability?
- **Sections.** Imbalance at the touch; Depth beyond the touch; Order-flow imbalance; The microprice; Queue depletion and cancellations; Predictor cards.
- **Defines.** queue imbalance, depth imbalance, depth profile, order-flow imbalance, microprice, weighted mid price, queue depletion rate, cancellation rate.
- **Uses (defined earlier).** mid price (B1.1), bid--ask spread (B1.1), market-by-order (B1.19), level 2 (B1.28), birth--death process (B4.8), hitting probability (B4.8), Hawkes process (B4.7), predictor card (ch6), information coefficient (ch6), tape (ch2).
- **Tutorial.** On firm.tape, estimate the probability of an up-move against queue imbalance and compare it with the birth--death race; regress mid changes on order-flow imbalance; compare the microprice and the mid as forecasts of the mid a second later.
- **Build.** `firm.lobfeat`: streaming order-book feature engine (imbalances, OFI, microprice, depletion and cancellation rates) updated per message, in C++20 with a Rust twin and a Python reference, all three checked on one shared message fixture.
- **Weekend problem.** Three lots against forty — named result: the empirical up-move probability at each imbalance bucket against the birth--death model's prediction, and the OFI regression's R-squared.
- **Facts to verify.** Cont, Kukanov, Stoikov 2014, the price impact of order book events (J. Financial Econometrics); Stoikov 2018, The micro-price (Quantitative Finance); Gould and Bonart 2016, queue imbalance as a one-tick-ahead price predictor (Market Microstructure and Liquidity); Cont, Stoikov, Talreja 2010 (Operations Research); Huang, Lehalle, Rosenbaum 2015 queue-reactive model (JASA); Cartea, Donnelly, Jaimungal 2018 order-book signals (Applied Mathematical Finance).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Cont, A. Kukanov, S. Stoikov, "The price impact of order book events", J. Financial Econometrics 12(1) (2014) 47-88: NYSE TAQ data for 50 US stocks; over short intervals price changes mainly driven by order flow imbalance; linear relation with slope inversely proportional to market depth | arXiv abstract 1011.6402; Crossref record | http://arxiv.org/abs/1011.6402 | 2026-09-24 | "using the NYSE TAQ data for 50 U.S. stocks. We show that, over short time intervals, price changes are mainly driven by the order flow imbalance"; "a linear relation between order flow imbalance and price changes, with a slope inversely proportional to the market depth" | section 3; def. OFI; card |
| F2 | M. D. Gould and J. Bonart, "Queue imbalance as a one-tick-ahead price predictor in a limit order book", Market Microstructure and Liquidity 2(2) (2016) 1650006: logistic regressions for 10 liquid Nasdaq stocks; strongly significant; considerable improvement for large-tick stocks, moderate for small-tick | arXiv abstract 1512.03492; Crossref record | http://arxiv.org/abs/1512.03492 | 2026-09-24 | "for each of 10 liquid stocks on Nasdaq. In each case, we find a strongly statistically significant relationship"; "considerable improvement in binary and probabilistic classification for large-tick stocks" | section 1; card |
| F3 | S. Stoikov, "The micro-price: a high-frequency estimator of future prices", Quantitative Finance 18(12) (2018) 1959-1966: the micro-price is empirically a better predictor of short-term prices than the mid-price or the weighted mid-price | EconPapers abstract; Crossref record | https://econpapers.repec.org/RePEc:taf:quantf:v:18:y:2018:i:12:p:1959-1966 | 2026-09-24 | "The micro-price estimated using high-frequency data is empirically a better predictor of short-term prices than the mid-price or the weighted mid-price" | section 4 |
| F4 | R. Cont, S. Stoikov, R. Talreja, "A stochastic model for order book dynamics", Operations Research 58(3) (2010) | Crossref record (SSRN version) | https://doi.org/10.2139/ssrn.1273160 | 2026-09-24 | bibliographic record only | omsources |
| F5 | W. Huang, C.-A. Lehalle, M. Rosenbaum, "Simulating and analyzing order book data: the queue-reactive model", JASA 110(509) (2015) 107-122 | Crossref record | https://doi.org/10.1080/01621459.2014.982278 | 2026-09-24 | bibliographic record only | omsources |

## EXCLUDED

- Cartea, Donnelly and Jaimungal (2018), planned: not fetched; not cited.
- Stoikov's exact estimator (the limit of iterated expectations), planned as a definition: only the abstract's comparative claim was verified; the book defines its own one-step microprice.
- All probabilities, R-squared values, rates and forecast errors are computed on firm.tape and tested.
