# 16. Generative Models and Synthetic Data — brief and source ledger

## Brief

- **Hook.** A generative network trained on twenty years of daily returns produces paths that pass every stylised-fact test on the desk's checklist; a strategy trained on a million of them has a Sharpe ratio of 2 on the generated paths and of zero on the real ones, because the generator had learned the market's shape and not its predictability.
- **Sections.** What a generative model is for; Variational autoencoders and adversarial networks; Diffusion models; Judging synthetic data; The ways synthetic data mislead.
- **Defines.** generative model, variational autoencoder, generative adversarial network, mode collapse, diffusion model, classifier two-sample test, train-on-synthetic test-on-real.
- **Uses (defined earlier).** stylised fact (B7.5), moving-block bootstrap (B4.13), stationary bootstrap (B4.13), GARCH model (B4.18), Hawkes process (B4.7), Kullback--Leibler divergence (B4.11), autoencoder (ch9), memorisation (ch14), agent-based model (B10.27), multilayer perceptron (ch7), Adam (ch7), early stopping (ch5), stochastic gradient descent (B4.24), reverse mode (B4.28), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Fit a block bootstrap, a GARCH model, a small VAE and a small GAN (one-dimensional convolutions) to firm.synthmkt index returns with planted crashes; score each generator on a stylised-fact scorecard and a classifier two-sample test; train a predictor on generated paths and test it on real ones; check memorisation by nearest-neighbour distance to the training windows. Data: synthetic.
- **Build.** `firm.genmkt`: generators (block bootstrap, GARCH, VAE, GAN, a small diffusion model on windows), a stylised-fact scorecard (reusing Book 10's agent-based-market checks once frozen), the classifier two-sample test, train-synthetic-test-real and a nearest-neighbour memorisation check; Python on PyTorch.
- **Weekend problem.** Paths that never happened -- named result: each generator's scorecard pass count and two-sample-test accuracy, and the train-synthetic-test-real gap in Sharpe ratio.
- **Facts to verify.** Kingma and Welling 2014 auto-encoding variational Bayes (ICLR); Goodfellow et al. 2014 generative adversarial nets (NeurIPS); Ho, Jain and Abbeel 2020 denoising diffusion probabilistic models (NeurIPS); Wiese, Knobloch, Korn and Kretschmer 2020 Quant GANs (Quantitative Finance); Buehler, Horvath, Lyons, Perez Arribas and Wood 2020 a data-driven market simulator for small data environments (arXiv); Lopez-Paz and Oquab 2017 revisiting classifier two-sample tests (ICLR); Cont 2001 empirical properties of asset returns (Quantitative Finance); Esteban, Hyland and Ratsch 2017 TSTR evaluation (arXiv).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | D. P. Kingma, M. Welling, "Auto-encoding variational Bayes", arXiv:1312.6114 2014 | arXiv API | https://arxiv.org/abs/1312.6114 | 2026-09-25 | title and abstract | def. variational autoencoder; omsources |
| F2 | I. Goodfellow et al., "Generative adversarial nets", arXiv:1406.2661 2014: a generative model and a discriminative model trained simultaneously | arXiv API | https://arxiv.org/abs/1406.2661 | 2026-09-25 | abstract: "we simultaneously train two models: a generative model G ... and a discriminative model" | def. GAN; omsources |
| F3 | J. Ho, A. Jain, P. Abbeel, "Denoising diffusion probabilistic models", arXiv:2006.11239 2020 | arXiv API | https://arxiv.org/abs/2006.11239 | 2026-09-25 | title and abstract | def. diffusion model; omsources |
| F4 | M. Wiese, R. Knobloch, R. Korn, P. Kretschmer, "Quant GANs: deep generation of financial time series", Quantitative Finance 20(9) 2020 | Crossref/OpenAlex record | https://doi.org/10.1080/14697688.2020.1730426 | 2026-09-25 | title, journal, year as registered | sec. VAE/GAN; exo 7; omsources |
| F5 | H. Buehler, B. Horvath, T. Lyons, I. Perez Arribas, B. Wood, "A data-driven market simulator for small data environments", arXiv:2006.14498 2020 | arXiv API | https://arxiv.org/abs/2006.14498 | 2026-09-25 | title and abstract | sec. VAE/GAN; omsources |
| F6 | D. Lopez-Paz, M. Oquab, "Revisiting classifier two-sample tests", arXiv:1610.06545 2017 | arXiv API | https://arxiv.org/abs/1610.06545 | 2026-09-25 | title and abstract: two-sample tests built from binary classifiers | def. classifier two-sample test; omsources |
| F7 | R. Cont, "Empirical properties of asset returns: stylized facts and statistical issues", Quantitative Finance 1(2) 2001 | Crossref/OpenAlex record | https://doi.org/10.1080/713665670 | 2026-09-25 | title, journal, year as registered | sec. judging (scorecard); omsources |
| F8 | C. Esteban, S. L. Hyland, G. Rätsch, "Real-valued (medical) time series generation with recurrent conditional GANs", arXiv:1706.02633 2017: evaluate on a real test set a model trained on synthetic data | arXiv API | https://arxiv.org/abs/1706.02633 | 2026-09-25 | abstract: "evaluate on a real test set the performance of a model trained on the synthetic data, and vice-versa" | def. TSTR; omsources |

## EXCLUDED

- The hook's 10.7 and 0.5 and every scorecard count, two-sample accuracy, TSTR/TSTS figure and distance are the chapter's own generators on a synthetic GJR-GARCH-t series with planted crashes and momentum (firm.genmkt), tested in code/ml/16-generative-models-and-synthetic-data/tests/test_solutions.py; nothing is claimed about any published generator's performance.
- The brief's firm.synthmkt index returns: replaced by firm.genmkt.real_index, whose structure (crashes, momentum) is set for this chapter's tests.
- Book 10's agent-based-market checks in the scorecard: left as a stretch (Book 10 chapter 27 not yet frozen); the scorecard is the chapter's own six-fact list.
