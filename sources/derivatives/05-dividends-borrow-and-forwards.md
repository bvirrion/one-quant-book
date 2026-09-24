# 5. Dividends, Borrow and Forwards — brief and source ledger

## Brief

- **Hook.** A share is on every broker's hard-to-borrow list; its one-month puts trade well above the calls at the strike nearest spot, and put-call parity turns the difference into a borrow rate of 35% a year.
- **Sections.** Forwards with discrete dividends and borrow; Dividends in the option model: escrowed, proportional, mixed; Implying forwards, dividends and borrow from parity; Dividend risk and dividend swaps.
- **Defines.** escrowed dividend model, proportional dividend, mixed dividend model, implied dividend, implied borrow rate, dividend risk, dividend swap.
- **Uses (defined earlier).** dividend, ex-dividend date (Book 1 ch. 8), put--call parity (Book 1 ch. 25), securities lending, rebate rate, borrow fee, short sale, locate (Book 1 ch. 6), dividend future (Book 1 ch. 22), cost of carry (Book 1 ch. 21), repo rate (Book 2 ch. 5), binomial model (ch. 2), Black model (ch. 3).
- **Tutorial.** Build an equity forward curve from a synthetic multi-expiry chain: implied dividends and borrow per expiry; then price one option under the three dividend models and plot the differences by strike.
- **Build.** `firm.divfwd`: equity forward-curve builder (discrete cash and proportional dividends, borrow curve, implied from parity); it becomes `MarketData.forward` in chapter 28.
- **Weekend problem.** The hard-to-borrow share — named result: the borrow rate implied by the one-month chain, and the mispricing of a call priced with the forward that ignores it.
- **Facts to verify.** Eurex Euro Stoxx 50 index dividend futures listing date and spec; index dividend swap market practice (exchange or practitioner documents); ECB recommendation of 27 March 2020 on bank dividends and the 2020 dividend-futures fall; Haug, Haug, Lewis 2003 on discrete dividends; hard-to-borrow fee levels (reuse Book 1 ledger).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Eurex EURO STOXX 50 Index Dividend Futures (FEXD): EUR 100 per index point, minimum price change 0.1 (EUR 10); maturities: five nearest quarterly, next two semi-annual, eight following annual months; cash settlement on the cumulative total of the relevant gross dividends; last trading day third Friday | Eurex product page | https://www.eurex.com/ex-en/markets/did/eqt-idx-div-fut/EURO-STOXX-50-Index-Dividend-Futures-946316 | 2026-09-24 | "Determining is the cumulative total of the relevant gross dividends" | dat:dv:dividends-borrow-and-forwards:divfut |
| F2 | ECB recommendation of 27 March 2020 (ECB/2020/19): banks should not pay dividends at least until 1 October 2020; extended on 27 July 2020 to 1 January 2021 | ECB Research Bulletin, 26 May 2023, and EUR-Lex record of ECB/2020/19 | https://www.ecb.europa.eu/press/research-publications/resbull/2023/html/ecb.rb230526~685b91efd3.en.html | 2026-09-24 | "On 27 March 2020 the ECB adopted a recommendation asking euro area banks not to pay out dividends, at least until 1 October 2020" | dat:dv:dividends-borrow-and-forwards:divfut; omsources |
| F3 | EUR-Lex record of Recommendation ECB/2020/19 | EUR-Lex | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52020HB0019 | 2026-09-24 | record of the recommendation (extension to 1 January 2021 per search summary of ECB/2020/35) | dat box |
| F4 | Autocallable hedgers are at inception short delta, long volatility and long dividends and hedge by selling dividend swaps; in the 2020 sell-off 2020 dividends traded at 55% and 2021 dividends at 70% of model predictions | E. Barthe, "Hedging structured products during the corona crisis: where did it go wrong?", Structured Retail Products, 30 April 2020 | https://www.structuredretailproducts.com/academy/expertviewarticle/76023 | 2026-09-24 | "At inception, the trader will be short delta, long volatility and long dividends"; "the real 2020 dividends are trading at 55% of what models were predicting. The 2021 dividends are also lower (at 70%)" | §4; dat box; fig flows |
| F5 | Put-call parity violations on individual stocks are asymmetric in the direction of short-sale constraints and related to the rebate rate spread; JFE 74(2) (2004) 305-342 | Ofek, Richardson, Whitelaw (NBER w9423 / JFE) | https://www.nber.org/papers/w9423 | 2026-09-24 | "violations of put-call parity are asymmetric in the direction of short sales constraints, their magnitudes are strongly related to the rebate rate spread" (abstract, via search) | §3; omsources |
| F6 | Haug, Haug, Lewis, "Back to basics: a new approach to the discrete dividend problem", Wilmott, September 2003, 37-47 | Semantic Scholar record | https://www.semanticscholar.org/paper/Back-to-Basics:-a-new-approach-to-the-discrete-Haug-Haug/414dac84d6185d1840a20e1f38e1858004f5d4d1 | 2026-09-24 | bibliographic record | omsources |

## EXCLUDED

- Launch date of the first listed index dividend future (June 2008): only a secondary source (Wikipedia) found; not stated.
- The claim that issuers' hedging drives dividend futures below analyst forecasts (a Journal of Portfolio Management paper, 2021): the abstract could not be fetched; the chapter relies on F4 only.
