# 16. Auctions and the Close — brief and source ledger

## Brief

- **Hook.** At ten to four the exchange publishes a buy imbalance of two hundred thousand shares in a stock; in the next ten minutes someone will sell them into the auction, and the price at which they do is set by whoever shows the best offer.
- **Sections.** The closing auction as a liquidity event; Reading the imbalance publication; Offsetting imbalances: pricing the order; The auction and the continuous book before it; Opening auctions and reopenings.
- **Defines.** imbalance-offsetting order, auction impact curve.
- **Uses (defined earlier).** call auction (B1.13), closing price (B1.13), indicative price (B1.13), order imbalance (B1.13), uncrossing price (B1.13), market-on-close order (B1.13), limit-on-close order (B1.13), basis trade at index close (B1.21), trade at settlement (B1.21), imbalance publication (B10.10, by outline), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** closing-auction imbalance liquidity provision; opening-auction liquidity provision; close hedged with trade-at-settlement futures.
- **Tutorial.** Uncross synthetic closing books with firm.auction, publish imbalances on a schedule, and price imbalance-offsetting orders from the auction impact curve and the post-close reversal; measure the provider's P&L and its sensitivity to the reversal assumption.
- **Build.** `firm.auctionmm`: indicative price and imbalance publications on a schedule, the auction impact curve, offsetting-order sizing and pricing, post-close mark-outs; Python, on firm.auction.
- **Weekend problem.** Two hundred thousand to sell — named result: the offsetting provider's expected P&L per share against the imbalance size, and the share of the closing move that reverts overnight.
- **Facts to verify.** Nasdaq Net Order Imbalance Indicator and closing cross rules (dated); NYSE closing auction imbalance publication times (dated); Closing auction share of US and European volume, exchange statistics (dated); Bogousslavsky and Muravyev 2023 Who trades at the close? (JFE); Jegadeesh and Wu 2022 Closing auctions: nasdaq versus NYSE (JFE) or equivalent.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Bogousslavsky and Muravyev (2023): closing auctions 7.5% of daily US volume in 2018, up from 3.1% in 2010; closing prices typically match pre-close bid or ask; price impact lower than continuous trading; deviations revert quickly and almost completely on average; auction-to-intraday volume spikes on S&P 500 additions and increases permanently | Journal of Financial Markets 66, 2023, 100852 | https://econpapers.repec.org/article/eeefinmar/v_3a66_3ay_3a2023_3ai_3ac_3as1386418123000502.htm | 2026-09-25 | abstract: "account for a striking 7.5% of daily volume in 2018, up from 3.1% in 2010"; "Auction price deviations revert quickly and almost completely, on average" | §1; strategy files |
| F2 | Nasdaq crosses FAQ: 3:50-3:55 p.m. reference price, paired shares, imbalance shares and side every 10 s; 3:55-4:00 every second with near and far indicative clearing prices; MOC before 3:55; LOC before 3:58, late LOCs re-priced vs 3:50/3:55 reference; modify/cancel before 3:50; IO orders offset MOC imbalance | Nasdaq, "The Nasdaq Opening and Closing Crosses: Frequently Asked Questions" (PDF created 4 Nov 2025) | https://nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf | 2026-09-25 | pdftotext: "Between 9:25 and 9:28 a.m. and 3:50 and 3:55 p.m., Nasdaq disseminates the following information every 10 seconds"; "Between 9:28 and 9:30 a.m. and 3:55 and 4:00 p.m., ... every second"; "Market-on-close (MOC) orders must be received prior to 3:55 p.m."; "LOC orders must be received prior to 3:58 p.m."; "for the closing cross prior to 3:50 p.m." | dat:hf:auctions-and-the-close:nasdaq |

## EXCLUDED

- NYSE imbalance publication times; Jegadeesh-Wu 2022: not fetched; Nasdaq is the one example.
- The 85%-by-next-morning reversal figure appears in the working-paper summary but not in the published abstract; the chapter uses 15% staying only as an assumption with sensitivity (0, 15%, 50%).
