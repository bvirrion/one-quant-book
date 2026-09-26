# 19. Deep Hedging and Machine Learning in Pricing — brief and source ledger

## Brief

- **Hook.** With a transaction cost of 5 basis points, delta-hedging a one-month option every day costs more than the option's whole vega; a network that learns when not to trade keeps most of the hedge for a third of the cost.
- **Sections.** Hedging under frictions as a learning problem; Deep hedging; Surrogate pricers and differential learning; Calibration networks; Where learned pricing breaks.
- **Defines.** deep hedging, convex risk measure, entropic risk measure, indifference price, surrogate model, differential machine learning, deep calibration.
- **Uses (defined earlier).** Heston model (B5.10), hedging P\&L (B5.4), discrete hedging error (B5.4), hedging band (B5.26), delta hedging (B1.26), expected shortfall (B6.21), calibration (B4.24), algorithmic differentiation (B4.28), certainty equivalent (B4.9), Monte Carlo method (B4.26), no-trade region (B4.10), multilayer perceptron (ch7), Adam (ch7), early stopping (ch5), stochastic gradient descent (B4.24), reverse mode (B4.28).
- **Tutorial.** Deep-hedge an at-the-money call under Heston paths from Book 5's engine with proportional costs, minimising an entropic and an expected-shortfall objective; compare with Black-Scholes delta, a Whalley-Wilmott band and the no-cost optimum; train a surrogate of Book 5's Heston pricer with and without differential labels and time a batch of prices against the original; fit a small calibration network. Data: synthetic (Book 5's firm.heston and firm.pricing).
- **Build.** `firm.deephedge`: a deep-hedging trainer (policy network over time, state and holdings; proportional costs; entropic and expected-shortfall objectives), indifference prices, a differential-learning surrogate of any firm.pricing engine, and a calibration network with an accuracy check against the true calibrator; Python on PyTorch.
- **Weekend problem.** Hedging with frictions -- named result: the indifference price as a function of the cost level, and the learned no-trade band's width against the Whalley-Wilmott band.
- **Facts to verify.** Buehler, Gonon, Teichmann and Wood 2019 deep hedging (Quantitative Finance); Horvath, Muguruza and Tomas 2021 deep learning volatility (Quantitative Finance); Huge and Savine 2020 differential machine learning (arXiv 2005.02347); Hernandez 2016 model calibration with neural networks (Risk / SSRN); Whalley and Wilmott 1997 an asymptotic analysis of an optimal hedging model for option pricing with transaction costs (Mathematical Finance); Follmer and Schied 2002 convex measures of risk (Finance and Stochastics); Hodges and Neuberger 1989 optimal replication of contingent claims under transaction costs.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | H. Buehler, L. Gonon, J. Teichmann, B. Wood, "Deep hedging", Quantitative Finance 19(8) 2019 (arXiv:1802.03042): hedging under frictions with deep learning and convex risk measures | Crossref/OpenAlex record; arXiv API | https://doi.org/10.1080/14697688.2019.1571683 | 2026-09-25 | arXiv abstract: "a framework for hedging a portfolio of derivatives in the presence of market frictions such as transaction costs" | def. deep hedging; omsources |
| F2 | S. Imaki, K. Imajo, K. Ito, K. Minami, K. Nakagawa, "No-transaction band network", arXiv:2103.01775 2021 | arXiv API | https://arxiv.org/abs/2103.01775 | 2026-09-25 | title and abstract (a network architecture for efficient deep hedging) | sec. deep hedging; omsources |
| F3 | A. E. Whalley, P. Wilmott, "An asymptotic analysis of an optimal hedging model for option pricing with transaction costs", Mathematical Finance 7(3) 1997 | Crossref/OpenAlex record | https://doi.org/10.1111/1467-9965.00034 | 2026-09-25 | title, journal, year as registered | sec. deep hedging (band); omsources |
| F4 | H. Föllmer, A. Schied, "Convex measures of risk and trading constraints", Finance and Stochastics 6(4) 2002 | Crossref/OpenAlex record | https://doi.org/10.1007/s007800200072 | 2026-09-25 | title, journal, year as registered | def. convex risk measure; omsources |
| F5 | B. Huge, A. Savine, "Differential machine learning", arXiv:2005.02347 2020: training with AAD derivatives for pricing and risk approximations | arXiv API | https://arxiv.org/abs/2005.02347 | 2026-09-25 | abstract: "Differential machine learning combines automatic adjoint differentiation (AAD) with modern machine learning" | def. differential machine learning; omsources |
| F6 | B. Horvath, A. Muguruza, M. Tomas, "Deep learning volatility", Quantitative Finance 21(1) 2021 (arXiv:1901.09647): network-based calibration within milliseconds for the whole surface | Crossref/OpenAlex record; arXiv API | https://doi.org/10.1080/14697688.2020.1817974 | 2026-09-25 | arXiv abstract: "a neural network based calibration method that performs the calibration task within a few milliseconds" | def. deep calibration; omsources |
| F7 | A. Hernandez, "Model calibration with neural networks", SSRN 2812140 2016 | Crossref/OpenAlex record | https://doi.org/10.2139/ssrn.2812140 | 2026-09-25 | title, year as registered | def. deep calibration; omsources |

## EXCLUDED

- The hook's 2.25, 0.115, 0.123 and 0.099 and every risk, band, error and calibration figure are computed on Book 5's firm.heston paths and pricer with the chapter's networks, tested in code/ml/19-deep-hedging-and-machine-learning-in-pricing/tests/test_solutions.py.
- The brief's hook ("more than the option's whole vega"; "a third of the cost"): not what the simulation shows; replaced by the measured cost (more than one volatility point) and the measured saving (0.099 against 0.123).
- Hodges and Neuberger 1989: planned, not cited (the indifference price is defined through the risk measure).
- Timing a batch of surrogate prices against the Fourier pricer: not reported (machine-dependent timings belong to chapter 26's protocol); the chapter reports accuracy only.
