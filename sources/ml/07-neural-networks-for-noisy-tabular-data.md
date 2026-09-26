# 7. Neural Networks for Noisy Tabular Data — brief and source ledger

## Brief

- **Hook.** Two researchers train the same small network on the same data and report ICs of 0.021 and 0.034; the only difference is the random seed, and the architecture change they are arguing about is worth 0.004.
- **Sections.** The multilayer perceptron and backpropagation; Optimisers, normalisation and regularisation; Seeds as a source of variance; Ensembles; Networks against boosting on tabular data.
- **Defines.** neural network, multilayer perceptron, activation function, backpropagation, mini-batch, epoch, Adam, dropout, weight decay, batch normalisation, layer normalisation, deep ensemble.
- **Uses (defined earlier).** stochastic gradient descent (B4.24), momentum method (B4.24), gradient descent (B4.24), reverse mode (B4.28), algorithmic differentiation (B4.28), ridge regression (B4.16), pseudo-random number generator (B4.26), bitwise reproducibility (B4.25), early stopping (ch5), learning rate (ch5), baseline model (ch4), gradient boosting (ch5), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Train a small PyTorch MLP on the Chapter 4 panel with Adam, dropout, weight decay and early stopping on purged folds; retrain it with twenty seeds and measure the seed-to-seed spread of the out-of-sample IC against the gap between two architectures; average five and twenty seeds; compare with ridge and LightGBM. Data: synthetic.
- **Build.** `firm.nettab`: a deterministic PyTorch training loop (seeded, one thread, deterministic algorithms), MLP builder with normalisation and dropout options, purged early stopping, seed ensembles, state save and load with a content hash; Python.
- **Weekend problem.** Twenty seeds -- named result: the seed standard deviation of the out-of-sample IC against the architecture gap, and the number of seeds to average before the gap is resolved at two standard errors.
- **Facts to verify.** Rumelhart, Hinton and Williams 1986 backpropagation (Nature); Kingma and Ba 2015 Adam (ICLR); Srivastava et al. 2014 dropout (JMLR); Ioffe and Szegedy 2015 batch normalization (ICML); Ba, Kiros and Hinton 2016 layer normalization (arXiv); Lakshminarayanan, Pritzel and Blundell 2017 deep ensembles (NeurIPS); Loshchilov and Hutter 2019 decoupled weight decay (ICLR); PyTorch reproducibility documentation.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | D. P. Kingma, J. Ba, "Adam: a method for stochastic optimization", ICLR 2015 | arXiv abstract | https://arxiv.org/abs/1412.6980 | 2026-09-25 | "an algorithm for first-order gradient-based optimization of stochastic objective functions, based on adaptive estimates of lower-order moments" | def. Adam; omsources |
| F2 | I. Loshchilov, F. Hutter, "Decoupled weight decay regularization", ICLR 2019: L2 regularisation and weight decay are equivalent for SGD but not for adaptive methods such as Adam | arXiv abstract | https://arxiv.org/abs/1711.05101 | 2026-09-25 | "L2 regularization and weight decay regularization are equivalent for standard stochastic gradient descent ... but as we demonstrate this is not the case for adaptive gradient algorithms, such as Adam" | def. weight decay; iq 2; omsources |
| F3 | N. Srivastava et al., "Dropout: a simple way to prevent neural networks from overfitting", JMLR 15 (2014) | JMLR page (title) | https://jmlr.org/papers/v15/srivastava14a.html | 2026-09-25 | page title as cited | def. dropout; omsources |
| F4 | S. Ioffe, C. Szegedy, "Batch normalization: accelerating deep network training by reducing internal covariate shift", ICML 2015; J. L. Ba, J. R. Kiros, G. E. Hinton, "Layer normalization", arXiv 2016 | arXiv records | https://arxiv.org/abs/1502.03167 ; https://arxiv.org/abs/1607.06450 | 2026-09-25 | titles as registered; "A recently introduced technique called batch normalization uses the distribution of the summed input to a neuron over a mini-batch" | def. batch and layer normalisation; omsources |
| F5 | B. Lakshminarayanan, A. Pritzel, C. Blundell, "Simple and scalable predictive uncertainty estimation using deep ensembles", NeurIPS 2017 | arXiv abstract | https://arxiv.org/abs/1612.01474 | 2026-09-25 | "Quantifying predictive uncertainty in NNs is a challenging and yet unsolved problem" | def. deep ensemble; omsources |
| F6 | D. E. Rumelhart, G. E. Hinton, R. J. Williams, "Learning representations by back-propagating errors", Nature 323 (1986) | Crossref/OpenAlex record | https://doi.org/10.1038/323533a0 | 2026-09-25 | title, journal, year as registered | def. backpropagation; omsources |
| F7 | PyTorch 2.14 reproducibility notes: completely reproducible results are not guaranteed across releases, commits or platforms; use_deterministic_algorithms makes PyTorch use deterministic algorithms where available and raise otherwise | PyTorch documentation, Reproducibility | https://docs.pytorch.org/docs/2.14/notes/randomness.html | 2026-09-25 | "Completely reproducible results are not guaranteed across PyTorch releases, individual commits, or different platforms" | build rules; iq 4 |
| F8 | Gu, Kelly and Xiu (2020): networks slightly ahead of trees on US stocks (Table 1: NN3 0.40%, GBRT 0.34%, RF 0.33%) | as chapter 1, F1 | https://www.nber.org/system/files/working_papers/w25398/w25398.pdf | 2026-09-25 | as chapter 1, F1 | section 6 |

## EXCLUDED

- Every IC, R-squared, Sharpe ratio, epoch and seed count is computed on firm.mlsynth (chapter 4's panel) and tested in code/ml/07-.../tests/test_solutions.py; the hook's two researchers are two seeds of the chapter's small network.
