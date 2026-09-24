# 24. Credit Indices and Tranches — brief and source ledger

## Brief

- **Hook.** In the first quarter of 2012 a bank's investment office tripled the net notional of its credit index book to about USD 157 billion; its position in one old index series was 10 to 15 days of the whole market's volume, and the losses reached USD 6.2 billion.
- **Sections.** The index families and their rolls; Index versus constituents; Tranches; Index options.
- **Defines.** credit index, index series, intrinsic spread, index skew, tranche, attachment point, detachment point, base correlation, credit index option.
- **Uses (defined earlier).** credit default swap, on-the-run, roll, survival probability, standard coupon.
- **Tutorial.** Compute an index's intrinsic spread from its constituents and the skew; value tranche expected losses with a one-factor Gaussian model.
- **Build.** `firm.tranche`: index intrinsic and large-pool tranche loss.
- **Weekend problem.** The skew trade — named result: the P&L of an index-versus-intrinsic position when the skew closes.
- **Facts to verify.** CDX/iTraxx roll dates (March/Sept), 125 names; JPMorgan 2012 losses (Senate report, SEC order); S&P/IHS Markit ownership of indices; tranche market post-2008.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | JPMorgan CIO's Synthetic Credit Portfolio: created 2007 as a hedge; positions in credit indices (CDX: North American and EM; iTraxx: European and Asian) and tranches; IG and HY indices; long risk = selling protection; from 2008 net short HY; Dec 2011 instructed to reduce regulatory capital; added long IG positions incl. CDX NA IG Series 9 10-year while adding to HY short; no notional limits; net notional tripled in Q1 2012 to about USD 157bn (132 positions at 31 Mar 2012); loss of about USD 2bn disclosed 10 May 2012, losses grew to nearly USD 6bn; JPMorgan admitted the facts; civil penalty USD 200m | SEC, Order Instituting Cease-and-Desist Proceedings, In the Matter of JPMorgan Chase & Co., Release No. 34-70458, 19 September 2013 | https://www.sec.gov/litigation/admin/2013/34-70458.pdf | 2026-09-24 | "During the first quarter of 2012, CIO tripled the net notional amount of the SCP. As of March 31, 2012, the SCP contained 132 trading positions with a net notional amount of approximately $157 billion." | hook; §2; problem |
| F2 | Markit creates a new series of each index every six months (IG-9 issued Sept 2007, IG-19 Sept 2012), with updated reference entities; roll date sees heavy trading; tranches reference segments of the index loss distribution: equity 0-3%, mezzanine 3-7%, then senior and super senior; equity tranche earns the highest coupon; some participants trade the "skew", the basis between the index price and the prices of its single-name CDS; losses about USD 5.8bn through 30 June 2012; traders believed counterparties knew CIO's positions | JPMorgan Chase & Co., Report of the Management Task Force Regarding 2012 CIO Losses, 16 January 2013 (hosted by Yale Program on Financial Stability) | https://ypfsresourcelibrary.blob.core.windows.net/fcic/YPFS/JPMorgan%20Management%20Task%20Force%20Regarding%202012%20CIO%20Losses%201-16-13.pdf | 2026-09-24 | "some market participants trade the "skew," or the basis between the index CDS price and prices for the single name CDS that make up the index" | §1; §2; §3; hook |
| F3 | Senate PSI hearing record: CIO's CDX.IG.9 net position USD 82.2bn, about 10-15 days of 100% of trading volume; total losses USD 6.2bn by year-end (Sen. McCain) | US Senate, Hearing 113-96, "JPMorgan Chase Whale Trades: A Case History of Derivatives Risks and Abuses", 15 March 2013 | https://www.govinfo.gov/content/pkg/CHRG-113shrg80222/html/CHRG-113shrg80222.htm | 2026-09-24 | "CDX.IG.9 net position for CIO is $82.2bio, which is approximately 10-15 days of 100% of trading volume" | hook; problem |
| F4 | CDX.NA.IG: 125 most liquid North American entities with IG ratings; equal or approximately equal weights; rolls 20 September and 20 March (or next business day); tenors 1 to 10 years; cleared at ICE Clear Credit | ICE, Markit CDX.NA.IG contract specifications | https://www.ice.com/products/28555645/Markit-CDXNAIG | 2026-09-24 | "One hundred twenty five (125) of the most liquid North American entities with investment grade credit ratings" | §1; dat:m2:credit-indices-and-tranches:indices |
| F5 | CDX.NA.IG swap: IG indices traded on spread; fixed coupon 100 bp paid quarterly; upfront fee in points; credit events bankruptcy and failure to pay; credit event settlement under the 2009 Supplement (Big Bang) | Bloomberg SEF, submission to the CFTC for the CDX.NA.IG 5Y contract, 1 November 2013 | https://data.bloomberglp.com/professional/sites/4/cds-index-contract-north-america-investment-grade-5y-ice-mat.pdf | 2026-09-24 | "Fixed coupon payments are calculated at a spread of 100 bps and exchanged on a quarterly basis." | §1 |
| F6 | ICE Clear Credit clears European-style CDS index options with physical delivery on 5Y CDX.NA.IG, CDX.NA.HY, iTraxx Europe and iTraxx Europe Crossover, up to 9 months to expiry | ICE, CDS index options clearing | https://www.ice.com/credit-derivatives/options | 2026-09-24 | "European style CDS Index Swaptions (Options) with physical delivery" | §4; dat:m2:credit-indices-and-tranches:indices |

## EXCLUDED

- Index administrator ownership (S&P Global after the IHS Markit merger): not needed beyond the name; not stated.
- iTraxx Europe composition and CDX HY coupon: not fetched from a primary source; the chapter states only the CDX IG facts.
- Tranche market size after 2008 and base-correlation quotes: no public source; the chapter's correlations are illustrative.
- Senate PSI report PDF: the Senate site refuses automated download; the hearing record on govinfo and the SEC order are used.

