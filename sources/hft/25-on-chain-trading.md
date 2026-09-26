# 25. On-Chain Trading — brief and source ledger

## Brief

- **Hook.** A large swap on a decentralised exchange moves its pool price away from the centralised exchanges; within the same block, searchers compete to arbitrage it back, and most of what they earn is bid away to the builder that includes their bundle.
- **Sections.** Exchange-to-chain arbitrage; Atomic arbitrage and searching; Liquidations on lending protocols; Just-in-time and hedged liquidity provision; Bundles, builders and bidding; sandwiching and the law.
- **Defines.** atomic arbitrage, bundle bid, hedged liquidity provision.
- **Uses (defined earlier).** CEX--DEX arbitrage (B3.22), maximal extractable value (B3.22), searcher (B3.22), block builder (B3.22), transaction bundle (B3.22), back-running (B3.22), sandwich attack (B3.22), proposer--builder separation (B3.22), order-flow auction (B3.22), just-in-time liquidity (B3.20), loss-versus-rebalancing (B3.20), concentrated liquidity (B3.20), liquidation bonus (B3.23), health factor (B3.23), flash loan (B3.23), priority fee (B3.14).
- **Strategy files.** CEX-DEX arbitrage; atomic DEX-DEX arbitrage; lending-protocol liquidation searching; just-in-time liquidity provision; bundle bidding in builder auctions; hedged concentrated-liquidity market making.
- **Tutorial.** On firm.amm pools priced against a simulated centralised exchange, find the arbitrage after each block, simulate competing searchers bidding for inclusion, and measure the share of the opportunity paid to the builder; then run a hedged liquidity position and measure its loss-versus-rebalancing.
- **Build.** `firm.searcher`: CEX-DEX and atomic cycle detection, liquidation opportunity scanner, a first-price bundle auction among searchers, hedged liquidity-provision P&L; Python, on firm.amm, firm.sandwich and firm.gasfee.
- **Weekend problem.** Bid away to the builder — named result: the share of arbitrage profit paid to builders as the number of competing searchers grows, and the hedged liquidity provider's net return after loss-versus-rebalancing.
- **Facts to verify.** Daian et al. 2020 Flash Boys 2.0 (IEEE S&P); Milionis, Moallemi, Roughgarden, Zhang 2022 Automated market making and loss-versus-rebalancing (arXiv); Heimbach, Pahari, Schertenleib 2024 Non-atomic arbitrage in decentralized finance (IEEE S&P or arXiv); Flashbots MEV-Boost documentation (dated); US v. Peraire-Bueno (SDNY 2024) and its outcome (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Daian et al., Flash Boys 2.0 (arXiv 1904.05234, 2019; IEEE S&P 2020): widespread and rising arbitrage bots on DEXes that pay high fees and optimise latency to front-run users; priority gas auctions; fees for priority ordering pose a systemic risk to consensus-layer security; miner extractable value | arXiv abstract | https://arxiv.org/abs/1904.05234 | 2026-09-25 | arXiv API summary: "Like high-frequency traders on Wall Street, these bots exploit inefficiencies in DEXes, paying high transaction fees and optimizing network latency to frontrun"; "priority gas auctions (PGAs)"; "high fees paid for priority transaction ordering poses a systemic risk to consensus-layer security" | §2; strategy file |
| F2 | Milionis, Moallemi, Roughgarden and Zhang: LP returns decompose into a market (beta-like) component and a microstructure (alpha-like) component, accrued fees minus losses to arbitrageurs | arXiv 2208.06046 (latest version abstract) | https://arxiv.org/abs/2208.06046 | 2026-09-25 | "LP returns decompose into a beta-like component reflecting market risk exposure, and an alpha-like component reflecting microstructural forces: accrued fees minus losses to arbitrageurs" | §5; strategy files (the sigma^2 V / 8 rate is derived in the chapter's solutions, not quoted) |
| F3 | US v. Peraire-Bueno: mistrial after the jury could not agree; Judge Jessica G. Clarke; charges of conspiracy to commit wire fraud, wire fraud and conspiracy to commit money laundering; alleged MEV-Boost exploit netting $25 million in 12 seconds | The Block, 8 November 2025 | https://www.theblock.co/news/regulation/2025-11-08-massive-overstep-mistrial-declared-for-mev-brothers-accused-of-25-million-fraud-on-ethereum-378101 | 2026-09-25 | "ended in a mistrial after the jury could not agree on how to apply the law in the case"; "The alleged exploit of MEV-Boost software that netted the brothers $25 million in just 12 seconds" | dat:hf:on-chain-trading:law |

## EXCLUDED

- Heimbach, Pahari and Schertenleib (2024) and the Flashbots MEV-Boost documentation: not fetched; proposer-builder separation by pointer to Book 3 ch. 22.
- The exact day of the mistrial declaration (7 November 2025 in secondary reports) is not in the fetched article; the chapter says "November 2025".
