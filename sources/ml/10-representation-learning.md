# 10. Representation Learning — brief and source ledger

## Brief

- **Hook.** A desk has ten years of order-book data and labels for three months of it, the only period its new execution venue existed; the ten unlabelled years are not useless.
- **Sections.** Representations and autoencoders; Self-supervised objectives; Contrastive learning and augmentations for market data; Pre-training, fine-tuning and the linear probe.
- **Defines.** representation learning, denoising autoencoder, self-supervised learning, contrastive learning, data augmentation, pre-training, fine-tuning, linear probe.
- **Uses (defined earlier).** principal component analysis (B4.22), unsupervised learning (ch1), supervised learning (ch1), autoencoder (ch9), convolutional neural network (ch8), temporal convolutional network (ch8), limit order book (B10.1), order-flow imbalance (B7.8), queue imbalance (B7.8), microprice (B7.8), mid price (B1.1), bid--ask spread (B1.1), trade sign (B7.9), multilayer perceptron (ch7), Adam (ch7), early stopping (ch5), stochastic gradient descent (B4.24), reverse mode (B4.28), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Pre-train a small encoder on many unlabelled firm.tape sessions with a masked-reconstruction and a contrastive objective (augmentations: time shift, jitter, depth masking; never across sessions), then fit a linear probe and a fine-tuned model on a small labelled set; compare with training from scratch as the labelled set grows. Data: synthetic.
- **Build.** `firm.represent`: autoencoders (plain and denoising), a contrastive objective with market-data augmentations, encoders over order-book windows, linear probes and fine-tuning against a from-scratch baseline; Python on PyTorch.
- **Weekend problem.** Learning without labels -- named result: the labelled sample size below which pre-training helps, and the probe's IC against the from-scratch model's at that size.
- **Facts to verify.** Hinton and Salakhutdinov 2006 reducing the dimensionality of data with neural networks (Science); Vincent et al. 2008 denoising autoencoders (ICML); Chen, Kornblith, Norouzi and Hinton 2020 SimCLR (ICML); van den Oord, Li and Vinyals 2018 contrastive predictive coding (arXiv); Yue et al. 2022 TS2Vec (AAAI); Alain and Bengio 2017 linear classifier probes (ICLR workshop).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | G. E. Hinton, R. R. Salakhutdinov, "Reducing the dimensionality of data with neural networks", Science 313 (2006): autoencoders with a small central layer convert high-dimensional data to low-dimensional codes | OpenAlex record with abstract | https://doi.org/10.1126/science.1127647 | 2026-09-25 | "High-dimensional data can be converted to low-dimensional codes by training a multilayer neural network with a small central layer to reconstruct high-dimensional input vectors" | section 1; omsources |
| F2 | P. Vincent, H. Larochelle, Y. Bengio, P.-A. Manzagol, "Extracting and composing robust features with denoising autoencoders", ICML 2008 | OpenAlex record with abstract | https://doi.org/10.1145/1390156.1390294 | 2026-09-25 | "We introduce and motivate a new training principle for unsupervised learning of a representation" | def. denoising autoencoder; omsources |
| F3 | P. Baldi, K. Hornik, "Neural networks and principal component analysis: learning from examples without local minima", Neural Networks 2(1) 1989 | Crossref/OpenAlex record | https://doi.org/10.1016/0893-6080(89)90014-2 | 2026-09-25 | title, journal and year as registered | prop. linear autoencoder; omsources |
| F4 | A. van den Oord, Y. Li, O. Vinyals, "Representation learning with contrastive predictive coding", arXiv 1807.03748 (2018); T. Chen et al., "A simple framework for contrastive learning of visual representations" (SimCLR), arXiv 2002.05709 / ICML 2020 | arXiv abstracts | https://arxiv.org/abs/1807.03748 ; https://arxiv.org/abs/2002.05709 | 2026-09-25 | "we propose a universal unsupervised learning approach to extract useful representations from high-dimensional data"; "This paper presents SimCLR: a simple framework for contrastive learning of visual representations" | def. contrastive learning; omsources |
| F5 | Z. Yue et al., "TS2Vec: towards universal representation of time series", arXiv 2106.10466 (AAAI 2022): contrastive learning over augmented context views for time series | arXiv abstract | https://arxiv.org/abs/2106.10466 | 2026-09-25 | "TS2Vec performs contrastive learning in a hierarchical way over augmented context views" | omsources |
| F6 | G. Alain, Y. Bengio, "Understanding intermediate layers using linear classifier probes", arXiv 1610.01644 (2016): linear classifiers ("probes") trained independently of the model measure how suitable features are | arXiv abstract | https://arxiv.org/abs/1610.01644 | 2026-09-25 | "We use linear classifiers, which we refer to as 'probes', trained entirely independently of the model itself" | def. linear probe; omsources |

## EXCLUDED

- Every IC is computed on firm.tape sessions (synthetic) and tested in code/ml/10-.../tests/test_solutions.py. The hook is a scenario, with no number.
- The InfoNCE mutual-information lower bound (van den Oord et al.) was left out: not in the retrieved abstract.
