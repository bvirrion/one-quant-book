# 20. Automated Market Makers — brief and source ledger

## Brief

- **Hook.** A pool of ether and dollars quotes no prices: its price moves only when someone trades against the rule that the product of its two balances stays constant.
- **Sections.** Constant-product market makers; Concentrated liquidity; Stableswap; Impermanent loss and loss-versus-rebalancing; Just-in-time liquidity, aggregators and intent-based routing.
- **Defines.** decentralised exchange, automated market maker, liquidity pool, constant-product market maker, concentrated liquidity, stableswap, impermanent loss, loss-versus-rebalancing, just-in-time liquidity, DEX aggregator, intent-based routing.
- **Uses (defined earlier).** market maker, adverse selection, mid price, bid--ask spread, realised volatility, gamma, smart contract, gas, token, stablecoin, cross-venue arbitrage, geometric Brownian motion (Book 4).
- **Tutorial.** Implement a constant-product swap with fees, compare an LP position with holding, and simulate arbitrageurs against a lognormal price to measure loss-versus-rebalancing against its closed form sigma squared over eight per unit time.
- **Build.** `firm.amm`: AMM library (constant product, concentrated-liquidity positions in square-root-price and tick arithmetic, stableswap invariant solver), integer fixed point, in Python and Rust.
- **Weekend problem.** Should you provide liquidity? — named result: the daily volume-to-liquidity ratio at which fee income covers loss-versus-rebalancing for a stated volatility and fee tier.
- **Facts to verify.** Uniswap v2 fee 0.30 percent and v3 fee tiers, launch May 2021 (Uniswap docs/whitepapers); Uniswap v4 launch and hooks (Uniswap release); Curve stableswap whitepaper (Egorov 2019); Milionis, Moallemi, Roughgarden and Zhang (2022) loss-versus-rebalancing; UniswapX and CoW Protocol batch auctions (their docs); DEX share of spot volume (a dated public dataset).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Uniswap v2: traders pay a 30-basis-point fee on trades, which goes to liquidity providers | Uniswap v2 Core whitepaper | https://uniswap.org/whitepaper.pdf | 2026-09-24 | "pay a 30-basis-point fee on trades, which goes to liquidity providers" | dat:m3:automated-market-makers:uniswap; firm.amm |
| F2 | Uniswap v3 Core whitepaper dated March 2021; initial fee tiers 0.05%, 0.30%, 1% with tick spacings 10, 60, 200; price ticks log base 1.0001; square-root prices | Uniswap v3 Core whitepaper | https://uniswap.org/whitepaper-v3.pdf | 2026-09-24 | "The initial fee tiers and tick spacings supported are 0.05% (with a tick spacing of 10 ...), 0.30% (... 60 ...), and 1% (... 200 ...)" | dat:m3:automated-market-makers:uniswap; §2; firm.amm |
| F3 | Uniswap v4 operational 31 January 2025; hooks are modular plugins for custom logic for pools, swaps, fees and LP positions | Uniswap Labs blog, "Uniswap v4 is here" | https://blog.uniswap.org/uniswap-v4-is-here | 2026-09-24 | "modular plugins that allow developers to build custom logic for pools, swaps, fees, and LP positions" | dat:m3:automated-market-makers:uniswap |
| F4 | StableSwap invariant A n^n sum x_i + D = A D n^n + D^(n+1)/(n^n prod x_i); amplification coefficient; comparison figure with x = y = 5; simulated optimum A = 85 (May-October 2019, three stablecoins) | M. Egorov, StableSwap paper (2019) | https://curve.fi/files/stableswap-paper.pdf | 2026-09-24 | "Optimial 'amplification coefficient' ('leverage'): A = 85" | def stableswap; fig invariants; firm.amm |
| F5 | LVR: instantaneous LVR = (sigma^2 P^2 / 2) x*'(P); for constant product l/V = sigma^2/8; at 5% daily vol about 3.125 bp a day; risk-neutral expectations of impermanent loss and LVR are equal but LVR contains no market risk | Milionis, Moallemi, Roughgarden, Zhang, arXiv:2208.06046 v6 | https://arxiv.org/pdf/2208.06046 | 2026-09-24 | "the ETH-USDC LP pool loses approximately sigma^2/8 = 3.125 (bp) in pool value to LVR daily" | prop lvrcp; §4; exercises |
| F6 | UniswapX: signed orders specifying outputs, fillers compete to fill with own liquidity or routing; Dutch auction decays from maximum to minimum price; gas-free for swappers, no cost for failed swaps | Uniswap developer docs, UniswapX overview | https://developers.uniswap.org/docs/liquidity/uniswapx/overview | 2026-09-24 | "Swappers generate signed orders which specify the outputs of their swap, and fillers compete to satisfy these orders" | dat:m3:automated-market-makers:intents |
| F7 | CoW Protocol: meta-DEX aggregation with trade intents and batch auctions; solvers find execution; coincidence of wants within batches; otherwise on-chain and off-chain liquidity (AMMs, aggregators such as 1inch and Paraswap, private market makers) | CoW Protocol documentation | https://docs.cow.fi/cow-protocol | 2026-09-24 | "leverages trade intents and fair combinatorial batch auctions to find users better prices" | dat:m3:automated-market-makers:intents |
| F8 | Uniswap v3 deployed to Ethereum mainnet; post dated 5 May 2021 | Uniswap Labs blog, "Uniswap v3 Mainnet launch" | https://blog.uniswap.org/launch-uniswap-v3 | 2026-09-24 | "May 05, 2021"; "We're thrilled to announce that Uniswap v3 has been deployed to the Ethereum mainnet!" | dat:m3:automated-market-makers:uniswap |
| F9 | DEX spot volume 6.0% of CEX spot volume in Jan 2021; all-time high 37.4% in June 2025; around 20% for five months to Nov 2025 (21.19% in the data table) | CoinGecko Research, "DEX to CEX Volume Ratios", updated 17 Apr 2026 | https://www.coingecko.com/research/publications/dex-to-cex-ratio | 2026-09-24 | "DEX spot trading volumes starting out at just 6.0% of CEX spot volumes in January 2021"; "a new all-time high of 37.4%"; "maintained around the 20.0% level" | dat:m3:automated-market-makers:uniswap |

## EXCLUDED

- DEX share of spot volume (a dated public dataset): not fetched; not used. **restored → F9 (CoinGecko's dated series, attributed).**
- Uniswap v3's mainnet launch month (May 2021): only the whitepaper's March 2021 date is cited. **restored → F8.**
- Pool sizes, volumes and volatilities of the problem and exercises are illustrative. **illustrative by design, not a sourcing gap.**
