# 14. Blockchains for Traders — brief and source ledger

## Brief

- **Hook.** A trader withdraws stablecoins from an exchange to capture a price gap on a chain; the transfer waits for confirmations, and when it lands the gap is gone.
- **Sections.** Ledgers, consensus and finality; Transactions, gas and the fee market; The mempool; Base layers, rollups, sequencers and bridges; Stablecoins: mint and redeem.
- **Defines.** blockchain, consensus protocol, proof of work, proof of stake, validator, finality, private key, token, smart contract, oracle, gas, base fee, priority fee, mempool, rollup, sequencer, bridge, stablecoin, depeg.
- **Uses (defined earlier).** settlement, settlement cycle, delivery versus payment, money-market fund, Treasury bill.
- **Tutorial.** Simulate the EIP-1559 base-fee rule under a demand shock (target half-full blocks, change capped at one-eighth a block) and the inclusion delay of a transaction as a function of its priority fee.
- **Build.** `firm.gasfee`: fee and confirmation model (base-fee projection, transaction cost in dollars, confirmation or finality time per chain for the transfer planner).
- **Weekend problem.** The gas spike — named result: the base-fee multiplier after a run of full blocks, and the break-even priority fee for a time-sensitive arbitrage transaction.
- **Facts to verify.** Bitcoin 10-minute block target and the six-confirmation convention (Bitcoin whitepaper and docs); Ethereum Merge 15 September 2022; slots 12 s, 32-slot epochs, finality after two epochs (ethereum.org); EIP-1559 parameters and London upgrade date; EIP-4844 (Dencun, March 2024); USDT and USDC supply (issuer transparency pages, dated); USDC depeg March 2023 and the SVB exposure (Circle statement); Circle mint and redeem terms; Ronin bridge exploit March 2022 and FBI attribution; rollup sequencer centralisation (L2BEAT).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | EIP-1559: BASE_FEE_MAX_CHANGE_DENOMINATOR = 8, ELASTICITY_MULTIPLIER = 2; integer update formulas (increase at least 1 wei); base fee burned; miner (proposer) receives only the priority fee | EIP-1559 specification | https://eips.ethereum.org/EIPS/eip-1559 | 2026-09-24 | "BASE_FEE_MAX_CHANGE_DENOMINATOR = 8"; "the base fee is not given to anyone (it is burned)" | prop basefee; firm.gasfee |
| F2 | Ethereum proof of stake: 12-second slots, 32-slot epochs, finality after two epochs (~12.8 minutes); the Merge completed 15 September 2022 | ethereum.org, "Proof-of-stake (PoS)" and "The Merge" | https://ethereum.org/developers/docs/consensus-mechanisms/pos/ | 2026-09-24 | "Time in proof-of-stake Ethereum is divided into slots (12 seconds) and epochs (32 slots)" (search excerpt) | dat:m3:blockchains-for-traders:times |
| F3 | Bitcoin: blocks targeted every ten minutes; the six-confirmation convention follows the whitepaper's reversal-probability calculation | S. Nakamoto, Bitcoin whitepaper (2008) | https://bitcoin.org/bitcoin.pdf | 2026-09-24 | whitepaper section 11 (calculations) and difficulty target | dat:m3:blockchains-for-traders:times |
| F4 | March 2023: Circle unable to withdraw $3.3bn of USDC reserves from SVB (around 8%); USDC traded as low as 86 cents; most holders cannot redeem from Circle; issuance and redemption constrained by US banking hours | Federal Reserve FEDS Notes, 17 December 2025 | https://www.federalreserve.gov/econres/notes/feds-notes/in-the-shadow-of-bank-run-lessons-from-the-silicon-valley-bank-failure-and-its-impact-on-stablecoins-20251217.html | 2026-09-24 | "unable to withdraw $3.3 billion of USDC reserves from SVB (around 8% of total reserves at the time)"; "At its trough, USDC traded at 86 cents to the dollar" | dat:m3:blockchains-for-traders:stable |
| F5 | Ronin bridge: exploit disclosed 29 March 2022 (173,600 ETH and 25.5m USDC); on 14 April 2022 US Treasury (OFAC) tied it to North Korea's Lazarus group; about $625m at the time of disclosure ($540m at the time of theft) | CoinDesk, 14 April 2022; Elliptic analysis | https://www.coindesk.com/policy/2022/04/14/us-officials-tie-north-korean-hacker-group-to-axies-ronin-exploit | 2026-09-24 | "tied the North Korea-based hacking group, Lazarus, to the Ronin Network exploit" (search excerpt) | §4 |
| F6 | Total stablecoin supply $302.8bn on 10 September 2026; USDT $183.4bn, USDC $74.2bn | StablecoinBeat tracker (aggregator) | https://stablecoinbeat.com/tracker/ | 2026-09-24 | "As of September 10, 2026, the total stablecoin market stood at $302.8 billion" (search excerpt) | dat:m3:blockchains-for-traders:stable |
| F7 | Ethereum block 26,048,449 (timestamp 1790266631 = 2026-09-24 16:17:11 UTC): gasLimit 60,000,000; gasUsed 22,082,507; baseFeePerGas 1.4915 gwei | Public Ethereum JSON-RPC node (publicnode.com), eth_getBlockByNumber latest | https://ethereum-rpc.publicnode.com | 2026-09-24 | JSON result: number 0x18d7..., gasLimit 60000000, gasUsed 22082507, baseFeePerGas 1491529172 wei | dat:m3:blockchains-for-traders:times |
| F8 | L2BEAT scaling summary: 101 projects; "Sequencer Failure" risk value: Self sequence 67, No mechanism 21, Enqueue via L1 7, Decentralized Sequencer Set 3, Force via L1 2, Log via L1 1 | L2BEAT API, scaling summary | https://l2beat.com/api/scaling/summary | 2026-09-24 | counts of projects[*].risks[name = Sequencer Failure].value | dat:m3:blockchains-for-traders:l2beat |

## EXCLUDED

- Gas limit, ether price, trade gas usage and the demand function are illustrative; the current Ethereum block gas limit is not stated. **current gas limit restored → F7; the example's gas usage, price and demand stay illustrative by design.**
- Rollup sequencer centralisation across specific rollups (L2BEAT): not fetched; the text says "on most rollups it is a single operator", generically. **restored → F8 (L2BEAT's data, counted).**
