# 23. Training Infrastructure — brief and source ledger

## Brief

- **Hook.** A training job on a year of order-book data spends four-fifths of its time waiting for data, and the team is pricing a second accelerator.
- **Sections.** Accelerators and where the time goes; Data loaders for tick data; Mixed precision; Distributed training; Checkpoints and deterministic resumption.
- **Defines.** accelerator, data loader, memory-mapped dataset, mixed-precision training, bfloat16, gradient accumulation, data parallelism, model parallelism, all-reduce, training checkpoint.
- **Uses (defined earlier).** floating-point number (B4.25), machine epsilon (B4.25), bitwise reproducibility (B4.25), compensated summation (B4.25), counter-based generator (B4.26), stochastic gradient descent (B4.24), mini-batch (ch7), epoch (ch7), Adam (ch7).
- **Tutorial.** Store firm.tape sessions as memory-mapped column shards and sample training windows without crossing sessions; compare loader throughput from CSV, NumPy files and memory-mapped shards; train in float32 and with bfloat16 autocast on the CPU and compare losses; show gradient accumulation equals a larger batch; run two-process data-parallel training with the gloo backend and check it matches one process; kill and resume a run bitwise from a checkpoint. Timings are measured on the author's laptop and only ratios are tested. Data: synthetic.
- **Build.** `firm.mltrain`: sharded memory-mapped tick datasets with session-aware window samplers, a trainer with gradient accumulation, bfloat16 autocast, gloo data parallelism for small runs, and checkpoints that capture model, optimiser, sampler and generator states for bitwise resumption; Python on PyTorch.
- **Weekend problem.** Where the time goes -- named result: the data-loading share of step time for each storage format, and the largest loss difference between float32 and bfloat16 training over the run.
- **Facts to verify.** Micikevicius et al. 2018 mixed precision training (ICLR); Kalamkar et al. 2019 a study of BFLOAT16 for deep learning training (arXiv); Li et al. 2020 PyTorch distributed: experiences on accelerating data parallel training (VLDB); Goyal et al. 2017 accurate, large minibatch SGD (arXiv); Shoeybi et al. 2019 Megatron-LM model parallelism (arXiv); a current data-centre accelerator's memory and bandwidth from the vendor's datasheet (dated); PyTorch documentation: DataLoader, autocast, DistributedDataParallel.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | NVIDIA H100 specifications: GPU memory 80 GB (SXM) and 94 GB (NVL); memory bandwidth 3.35 TB/s (SXM) and 3.9 TB/s (NVL); BF16 tensor-core 1,979 teraFLOPS (SXM), with sparsity | NVIDIA data-centre product page | https://www.nvidia.com/en-us/data-center/h100/ | 2026-09-26 | specification table: "80GB", "3.35TB/s", "1,979 teraFLOPS" marked with sparsity | dat:ml:training-infrastructure:h100; omsources |
| F2 | P. Micikevicius et al., "Mixed precision training", arXiv:1710.03740 2018 | arXiv API | https://arxiv.org/abs/1710.03740 | 2026-09-26 | title and abstract | def. mixed-precision training; omsources |
| F3 | D. Kalamkar et al., "A study of BFLOAT16 for deep learning training", arXiv:1905.12322 2019 | arXiv API | https://arxiv.org/abs/1905.12322 | 2026-09-26 | title and abstract | def. bfloat16; omsources |
| F4 | S. Li et al., "PyTorch distributed: experiences on accelerating data parallel training", arXiv:2006.15704 2020 | arXiv API | https://arxiv.org/abs/2006.15704 | 2026-09-26 | title and abstract | def. data parallelism; omsources |
| F5 | P. Goyal et al., "Accurate, large minibatch SGD: training ImageNet in 1 hour", arXiv:1706.02677 2017 (learning-rate scaling and warm-up) | arXiv API | https://arxiv.org/abs/1706.02677 | 2026-09-26 | title and abstract | sec. distributed training; omsources |
| F6 | M. Shoeybi et al., "Megatron-LM: training multi-billion parameter language models using model parallelism", arXiv:1909.08053 2019 | arXiv API | https://arxiv.org/abs/1909.08053 | 2026-09-26 | title and abstract | def. model parallelism; omsources |

## EXCLUDED

- Timings (load, batch, compute, data shares) are measured once by bench_train.py on the author's laptop and recorded with a .meta sidecar; tests check only orderings and the arithmetic the text does with them. The hook's day-long job and accelerator purchase are an illustration.
- The brief's two-process data-parallel run with the gloo backend: not run, because the batch ran under a coordinator rule of no worker processes on a shared, overloaded machine; the all-reduce's arithmetic is checked in one process instead.
- PyTorch documentation pages (DataLoader, autocast, DistributedDataParallel): not cited; the chapter uses torch.autocast on the CPU and states only what it measured.
