# 18. Emerging-Market FX and Non-Deliverable Forwards — brief and source ledger

## Brief

- **Hook.** On 15 January 2015 at 09:30 Zurich time the euro fell from 1.20 francs to below 0.90 within minutes.
- **Sections.** Convertibility and capital controls; Onshore and offshore markets; Non-deliverable forwards; Pegs, bands and interventions; The franc unpeg.
- **Defines.** convertibility, capital control, non-deliverable forward, fixing source, onshore market, offshore market, currency peg, currency band, FX intervention.
- **Uses (defined earlier).** outright forward, forward points, benchmark fix, cash settlement.
- **Tutorial.** Settle an NDF against its fixing and compute the onshore–offshore basis from two forward curves.
- **Build.** `firm.ndf`: NDF settlement and onshore/offshore basis.
- **Weekend problem.** The floor that broke — named result: the loss on a 20:1 leveraged EURCHF long at the first quoted price after the unpeg.
- **Facts to verify.** SNB 15 Jan 2015 announcement (floor 1.20 since Sept 2011); EURCHF low on the day; broker losses (FXCM, public filings/press); CNY vs CNH, PBoC fixing band; EMTA NDF fixing sources; HKD band 7.75-7.85.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SNB, 6 Sep 2011: sets a minimum rate of CHF 1.20 per euro, will "no longer tolerate" a lower rate, "prepared to buy foreign currency in unlimited quantities"; SNB, 15 Jan 2015: discontinues the minimum rate, lowers the rate on sight deposits above the exemption threshold by 0.5 points to -0.75%, moves the three-month Libor target range to -1.25% to -0.25% | SNB press releases 6 Sep 2011 and 15 Jan 2015 (PDFs) | https://www.snb.ch/public/asset/en/www-snb-ch/publications/communication/press-releases/2015/pre_20150115/publications0_en/pre_20150115.en.pdf | 2026-09-23 | "The Swiss National Bank (SNB) is discontinuing the minimum exchange rate of CHF 1.20 per euro." | hook; §5 |
| F2 | ECB EURCHF reference rates: 1.1111 on 5 Sep 2011, 1.2036 on 6 Sep 2011; never below 1.20 between 7 Sep 2011 and 14 Jan 2015; 1.2010 on 14 Jan 2015, 1.0280 on 15 Jan 2015, 0.9816 on 23 Jan 2015 (lowest of January), 1.0468 on 30 Jan 2015 | ECB Data Portal EXR.D.CHF.EUR.SP00.A (data/markets-2/eurchf_ecb_2010_2016.csv) | https://data-api.ecb.europa.eu/service/data/EXR/D.CHF.EUR.SP00.A | 2026-09-23 | downloaded series | hook; fig; problem |
| F3 | FXCM, 19 Jan 2015: customer debit balances after the franc's move on 15 Jan 2015 obliged its regulated entities to add capital; 16 Jan 2015 credit agreement with Leucadia for a USD 300 million two-year term loan, net proceeds about USD 279 million to replace capital covering negative client balances and pay down revolving debt; initial rate 10%, rising 1.5% a quarter, capped at 17% | FXCM Inc., Form 8-K, Exhibit 99.1 (SEC EDGAR) | https://www.sec.gov/Archives/edgar/data/0001499912/000114420415002640/v398968_ex99-1.htm | 2026-09-23 | "a $300 million, two-year term loan. The net proceeds of the loan (approximately $279 million) will replace capital in FXCM regulated entities to cover negative client balances" | §5; problem |
| F4 | PBoC announcement 2014 No. 5: from 17 Mar 2014 the floating band of RMB against USD on the interbank spot market widened from 1% to 2% around the central parity published by CFETS each day | People's Bank of China announcement, 15 Mar 2014 (search excerpt; gov.cn English release) | http://english.www.gov.cn/policies/latest_releases/2014/08/23/content_281474983027528.htm | 2026-09-23 | "the trading prices of RMB against U.S. dollar will fluctuate within a band of ±2 percent below and above the central parity" | §2; §4 |
| F5 | HKMA: the Linked Exchange Rate System in place since 17 Oct 1983, keeping the Hong Kong dollar within HK$7.75-7.85 per US dollar through a currency board | HKMA, Linked Exchange Rate System | https://www.hkma.gov.hk/eng/key-functions/money/linked-exchange-rate-system/ | 2026-09-23 | "remains stable within a band of HK$7.75-7.85 to one US dollar" | def; §4; dat:m2:emerging-market-fx-and-ndfs:regimes |
| F6 | Hong Kong is an offshore renminbi business centre | HKMA, "The Premier Offshore Renminbi Business Centre" booklet | https://www.hkma.gov.hk/media/eng/publication-and-research/hkrmb/hkma-rmb-booklet.pdf | 2026-09-23 | "Hong Kong is an established international financial centre and the pioneer in offshore renminbi business" | §2 |
| F8 | CNY CNHHK: the USD/CNY (HK) spot rate reported by the Treasury Markets Association, Hong Kong, at about 11:30 a.m. Hong Kong time | EMTA Annex A (June 2023) | https://www.emta.org/media/xa0n2urc/annex-a-to-the-1998-fx-and-currency-option-definitions-june-30-2023.pdf | 2026-09-23 | "reported by the Treasury Markets Association, Hong Kong (www.tma.org.hk) as its USD/CNY (HK) Spot Rate" | §2 |
| F7 | Settlement rate options (Annex A to the 1998 FX definitions, as of 30 Jun 2023): INR FBIL (FBIL reference rate, about 1:30 p.m. Mumbai), BRL PTAX (Banco Central do Brasil, about 1:15 p.m. Sao Paulo), CNY SAEC (PBoC-authorised fixing reported by CFETS, about 9:15 a.m. Beijing), KRW KFTC18 (market average rate reported by Seoul Money Brokerage, about 4:00 p.m. Seoul), TWD TAIFX1 (Taipei Forex, 11:00 a.m. Taipei); each "for settlement in two Business Days" | EMTA, Annex A to the 1998 FX and Currency Option Definitions, June 30, 2023 | https://www.emta.org/media/xa0n2urc/annex-a-to-the-1998-fx-and-currency-option-definitions-june-30-2023.pdf | 2026-09-23 | ""INR FBIL" or "INR01" each means that the Spot Rate ... reported by Financial Benchmarks India Pvt. Ltd." | def fixing source; §3; table |

## EXCLUDED

- Intraday low of EURCHF on 15 Jan 2015 (press: about 0.85): no official source fetched; the text uses the ECB's afternoon reference rate (1.0280) and says so.
- Start date of the CNH market (press: July 2010): not verified in an official source; not used.
- Broker loss figures other than FXCM's own filing: not used.

