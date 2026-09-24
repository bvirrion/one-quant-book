# 15. FX Spot Microstructure — brief and source ledger

## Brief

- **Hook.** A price streamed at 10:00:00.000 is hit at 10:00:00.003 and rejected at 10:00:00.090: the client asks why.
- **Sections.** Streaming prices and tiered liquidity; Adverse selection; Last look and hold times; Skewing and internalisation; The global code of conduct.
- **Defines.** streaming quote, liquidity tier, adverse selection, last look, hold time, reject rate, quote skewing, FX Global Code.
- **Uses (defined earlier).** internalisation, market maker, single-dealer platform.
- **Tutorial.** Measure a liquidity provider's reject rate and post-trade mark-outs as a function of hold time on a simulated stream.
- **Build.** `firm.lastlook`: last-look TCA (fill ratio, mark-outs, hold times).
- **Weekend problem.** The asymmetric window — named result: the value a symmetric versus asymmetric last-look policy transfers from the client.
- **Facts to verify.** FX Global Code principle 17 (last look); EBS minimum quote life / latency floor; FCA/NY DFS last-look enforcement (Barclays 2015); GFXC disclosure templates.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | NY DFS consent order with Barclays, 17/18 Nov 2015: BARX last look delayed the response to client orders for a "hold time" and rejected them if the price moved beyond a threshold; from at least 2009 through 2014 applied broadly and indiscriminately without checking for latency arbitrage; compared prices at start and end of the hold, thresholds "in the tens and hundreds of milliseconds"; rejections labelled "NACK"; a client on 15 Dec 2010: rejected "9 times out of 10", no evidence of a reply; revised to symmetric in Sept-Oct 2014, one platform (7% of volume) stayed asymmetric until Aug 2015; penalty USD 150,000,000 | New York State Department of Financial Services, Consent Order under Banking Law 44, In the Matter of Barclays Bank PLC | https://www.dfs.ny.gov/system/files/documents/2020/04/ea151117_barclays.pdf | 2026-09-23 | "rejects the order if the market price moves beyond a certain threshold during the hold time" | hook; §3; problem |
| F2 | FX Global Code Principle 17: market participants employing last look should be transparent and disclose; last look is a final opportunity to accept or reject a trade request against the quoted price; should be a risk control to verify validity and/or price; disclose whether and how price changes in either direction affect the decision, the expected time, the purpose; not for information gathering; no trading on the request's information during the window (pricing or hedging) | Global Foreign Exchange Committee, FX Global Code, updated December 2024 | https://www.globalfxc.org/uploads/fx_global.pdf | 2026-09-23 | "Market Participants employing last look should be transparent regarding its use and provide appropriate disclosures to Clients." | def; §5; dat:m2:fx-spot-microstructure:code |
| F3 | The FX Global Code is a set of principles of good practice for the wholesale FX market, maintained by the GFXC (established May 2017, central banks and private participants); it does not impose legal or regulatory obligations; participants sign Statements of Commitment | same, Foreword | https://www.globalfxc.org/uploads/fx_global.pdf | 2026-09-23 | "The Global Code does not impose legal or regulatory obligations on Market Participants" | def FX Global Code; §5 |
| F4 | GFXC released a guidance paper on last look and published disclosure templates (cover sheets) in August 2021 | GFXC press release, 18 Aug 2021 (title, from search results) | https://www.globalfxc.org/press-releases/press-p210818/ | 2026-09-23 | "GFXC releases guidance paper on Last Look, publishes disclosure templates" | §5 |
| F5 | Primary venues introduced speed bumps to protect dealers from HFT strategies; PTFs stream prices directly to customers; execution algorithms 10-20% of spot (2020) | BIS Quarterly Review, Dec 2022 (ledgered in ch. 14, F2) | https://www.bis.org/publ/qtrpdf/r_qt2212y.htm | 2026-09-23 | "primary venues have subsequently introduced "speed bumps" to level the playing field" | §1-2 |

## EXCLUDED

- EBS minimum quote life / latency floor parameters: not fetched from an official source; the text speaks of speed bumps generally (BIS).
- FCA last-look enforcement: none found in the time available; not used.
- Brief hook (a price hit after 3 ms and rejected after 90 ms): a scene, replaced by the client complaint quoted in the NY DFS order (F1).

