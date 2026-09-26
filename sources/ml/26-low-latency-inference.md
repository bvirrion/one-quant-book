# 26. Low-Latency Inference — brief and source ledger

## Brief

- **Hook.** A gradient-boosted model of five hundred trees takes 40 microseconds per prediction through its library's Python interface and well under 2 microseconds as generated C++, measured on the same laptop; the model did not change.
- **Sections.** The inference budget; Compiling trees; Small networks: layout, fusion and quantisation; Batching against latency; Inference in C++, in Rust and on programmable hardware.
- **Defines.** inference latency, model compilation, operator fusion, quantisation, post-training quantisation, quantisation-aware training, dynamic batching.
- **Uses (defined earlier).** latency budget (B13.1), tail latency (B13.1), coordinated omission (B13.5), cache line (B13.3), vector instruction (B13.14), branch prediction (B13.2), floating-point number (B4.25), fused multiply-add (B4.25), gradient boosting (ch5), multilayer perceptron (ch7), model artefact (ch25), feature store (ch24), training--serving skew (ch24), model registry (ch25).
- **Tutorial.** Export the Chapter 5 LightGBM model to JSON and compile it two ways (generated nested branches, flat arrays walked in a loop) to C++20 and Rust; quantise a small MLP to int8 after training and with quantisation-aware training, and implement it in C++20 and Rust; check bitwise or tolerance parity on shared test vectors; measure median and tail latency with Book 13's method and the accuracy lost to quantisation; trace latency against batch size. Timings measured on a laptop (Intel Core Ultra 7 155H) under WSL2, no isolated cores; tests assert only orderings and parity. Data: synthetic.
- **Build.** `firm.mlinfer`: a Python exporter (LightGBM JSON to code; MLP to int8 weights with scales), C++20 and Rust inference kernels for trees and quantised MLPs with no heap allocation on the hot path, parity test vectors, and a latency harness; Python + C++20 + Rust.
- **Weekend problem.** Two microseconds for a forest -- named result: the ratio of the compiled model's tail latency to the library call's, and the IC lost to int8 quantisation with and without quantisation-aware training.
- **Facts to verify.** Jacob et al. 2018 quantization and training of neural networks for efficient integer-arithmetic-only inference (CVPR); Nagel et al. 2021 a white paper on neural network quantization (arXiv); Asadi, Lin and de Vries 2014 runtime optimizations for tree-based machine learning models (IEEE TKDE); Lucchese et al. 2015 QuickScorer (SIGIR); Treelite documentation (tree compiler); ONNX Runtime documentation; Duarte et al. 2018 fast inference of deep neural networks in FPGAs for particle physics, hls4ml (JINST); published latency figures for machine-learning inference on programmable hardware in trading (conference talks or vendor documents; dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | B. Jacob et al., "Quantization and training of neural networks for efficient integer-arithmetic-only inference", arXiv:1712.05877 2018 | arXiv API | https://arxiv.org/abs/1712.05877 | 2026-09-26 | title and abstract | def. quantisation; omsources |
| F2 | M. Nagel et al., "A white paper on neural network quantization", arXiv:2106.08295 2021 (post-training quantisation and quantisation-aware training) | arXiv API | https://arxiv.org/abs/2106.08295 | 2026-09-26 | title and abstract | def. PTQ/QAT; omsources |
| F3 | N. Asadi, J. Lin, A. P. de Vries, "Runtime optimizations for tree-based machine learning models", IEEE TKDE (online 2013, 2014) | Crossref/OpenAlex record | https://doi.org/10.1109/TKDE.2013.73 | 2026-09-26 | title, journal as registered | def. model compilation; omsources |
| F4 | C. Lucchese et al., "QuickScorer: a fast algorithm to rank documents with additive ensembles of regression trees", SIGIR 2015 | Crossref/OpenAlex record | https://doi.org/10.1145/2766462.2767733 | 2026-09-26 | title, year as registered | def. model compilation; omsources |
| F5 | J. Duarte et al., "Fast inference of deep neural networks in FPGAs for particle physics", arXiv:1804.06913 2018 | arXiv API | https://arxiv.org/abs/1804.06913 | 2026-09-26 | title and abstract | sec. programmable hardware; omsources |

## EXCLUDED

- Latencies are measured once by bench_infer.py (C++ and Rust benches in firm.mlinfer) on the author's laptop and recorded with .meta sidecars; tests assert only orderings and the arithmetic the text does. The brief's "500 trees, 40 microseconds, under 2 microseconds" hook: replaced by the measured 300-tree figures (265 and 2.6 microseconds).
- Treelite and ONNX Runtime documentation: not cited; the chapter compiles its own forest and network.
- Published latency figures for ML inference on programmable hardware in trading (planned dated box): no public source found that the chapter could verify; the programmable-hardware paragraph cites the particle-physics work instead and makes no claim about trading firms.
