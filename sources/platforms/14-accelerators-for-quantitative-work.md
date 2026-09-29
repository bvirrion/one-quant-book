# 14. Accelerators for Quantitative Work — brief and source ledger

## Brief

- **Hook.** A bank's overnight counterparty-risk Monte Carlo moved to graphics processors and ran many times faster; the same bank's intraday pricing of single trades did not move at all, because each request spent longer crossing to the device than computing on it.
- **Sections.** What a graphics processor is good at; The roofline model; Monte Carlo and risk on a device; Training, and what the machine-learning book already said; Deciding with a cost model.
- **Defines.** roofline model, arithmetic intensity, memory-bound kernel, compute-bound kernel, host--device transfer, thread divergence.
- **Uses (defined earlier).** accelerator (B12.23), mixed-precision training (B12.23), data parallelism (B12.23), Monte Carlo method (B4.26), counter-based generator (B4.26), SIMD (B13.14), floating-point number (B4.25), adjoint mode (B4.28), expected exposure (B6.17), credit valuation adjustment (B6.18).
- **Tutorial.** Measure on this laptop's CPU the throughput of four kernels -- path generation, a basket payoff over paths, exposure aggregation, a dense matrix product -- and their arithmetic intensity; place them on a roofline built from the laptop's measured bandwidth and peak, and on a roofline of a cited data-centre graphics processor; predict end-to-end speed-ups with host--device transfer included, for a large batch and a single request. End state: the two rooflines with the kernels placed, and a chart of predicted speed-up against batch size.
- **Build.** `firm.roofline`: kernel descriptors (flops, bytes moved, transfer bytes), a measured CPU roofline, device specifications as data with sources, the end-to-end model (transfer, launch, compute, Amdahl), and the CPU reference kernels with their tests; Python. No GPU is used or required.
- **Weekend problem.** Faster overnight, not intraday -- named result: the predicted end-to-end speed-up of an exposure Monte Carlo and of a single-trade price request on a cited device, and the batch size at which the device breaks even.
- **Facts to verify.** Williams, Waterman and Patterson 2009, Roofline (Communications of the ACM); a data-centre GPU's published peak FP64/FP32 throughput and memory bandwidth (vendor datasheet, dated); PCIe and NVLink published bandwidths (dated); a public bank or vendor account of GPU use for XVA or risk Monte Carlo (paper, talk or press, dated); STAC-A2 benchmark description (dated); Amdahl 1967, validity of the single-processor approach (AFIPS).
- **Data.** Measured on this laptop's CPU; device figures from cited datasheets.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | NVIDIA H100 SXM: FP64 34 TFLOPS, FP64 Tensor Core 67, FP32 67, 80 GB at 3.35 TB/s, NVLink 900 GB/s, PCIe Gen5 128 GB/s, up to 700 W | NVIDIA H100 product page | https://www.nvidia.com/en-us/data-center/h100/ | 2026-09-28 | "FP64: 34 teraFLOPS"; "FP64 Tensor Core: 67 teraFLOPS"; "FP32: 67 teraFLOPS"; "GPU Memory: 80GB"; "GPU Memory Bandwidth: 3.35TB/s"; "NVLink Interconnect: 900GB/s"; "PCIe Gen5: 128GB/s"; "Up to 700W (configurable)" | dat:pl:accelerators-for-quantitative-work:h100; firm.roofline DEVICES |
| F2 | STAC-A2: "the industry standard for testing technology stacks used for compute-intensive analytic workloads involved in pricing and risk management" | STAC Research, STAC-A2 page | https://docs.stacresearch.com/a2 | 2026-09-28 | quoted sentence | dat:pl:accelerators-for-quantitative-work:stac |
| F3 | Williams, Waterman and Patterson, Roofline, CACM 52(4) 65-76, 2009 | Crossref, DOI 10.1145/1498765.1498785 | https://api.crossref.org/works/10.1145/1498765.1498785 | 2026-09-28 | title "Roofline", authors, volume 52, issue 4, pages 65-76, 2009 | def roofline model; omsources |
| F4 | Amdahl, Validity of the single processor approach to achieving large scale computing capabilities, AFIPS Spring Joint Computer Conference 1967, p. 483 | Crossref, DOI 10.1145/1465482.1465560 | https://api.crossref.org/works/10.1145/1465482.1465560 | 2026-09-28 | title, author, proceedings, page 483, 1967 | section Monte Carlo and risk; omsources |

## EXCLUDED

- Kernel launch latency: no datasheet figure; the chapter uses 10 microseconds as a stated assumption and sweeps 1-50 us.
- A public bank or vendor account of GPU XVA (brief): not searched; the hook names no bank and is the chapter's own model result.
- PCIe per-direction bandwidth: the product page gives 128 GB/s without direction; used as the most favourable reading.

