# 10. Modelling Overnight-Rate Products — brief and source ledger

## Brief

- **Hook.** A caplet on compounded SOFR keeps accruing risk after its period has started: the rate is not known until the last day, and neither is the payoff.
- **Sections.** Backward-looking rates and their options; The generalised forward market model; Low-dimensional Markov models; Meeting dates and jumps in the short rate; Forward-looking term rates.
- **Defines.** backward-looking rate, forward-looking term rate, backward-looking caplet, generalised forward market model, Cheyette model.
- **Uses (defined earlier).** compounding in arrears (B2.1), overnight benchmark rate (B2.1), implied policy path (B2.8), caplet (B2.13), interbank offered rate (B2.1), LIBOR market model (ch8), Heath--Jarrow--Morton framework (ch8), Hull--White model (ch7), caplet volatility (ch4).
- **Tutorial.** Price backward-looking caplets under Hull--White and under the generalised forward market model; plot how the variance accrues through the accrual period and compare with a forward-looking caplet.
- **Build.** `firm.rfrcaplet`: backward-looking caplet and cap pricer with in-period volatility decay; meeting-date step option.
- **Weekend problem.** The SOFR cap on a leveraged loan — named result: the premium gap between a backward-looking cap and a term-rate cap, and the part due to scheduled meeting dates.
- **Facts to verify.** Lyashenko and Mercurio 2019 (paper); ARRC term SOFR recommendation (July 2021) and its scope of use; CME Term SOFR administration (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | On 29 July 2021 the ARRC formally recommended CME Group's forward-looking SOFR term rates, after the SOFR First interdealer convention change of 26 July 2021 | ARRC press release, "ARRC Formally Recommends Term SOFR", 29 July 2021 | https://www.newyorkfed.org/medialibrary/Microsites/arrc/files/2021/ARRC_Press_Release_Term_SOFR.pdf | 2026-09-24 | "formally recommending CME Group's forward-looking Secured Overnight Financing Rate (SOFR) term rates"; "SOFR First initiative" on July 26, 2021 | dat:rc:modelling-overnight-rate-products:term |
| F2 | ARRC best practices: SOFR term rates not supported for derivatives except end users hedging cash products that use them; supported for business loans; overnight SOFR and averages recommended where possible | Dechert OnPoint, "Term SOFR is here - the ARRC recommends CME Group's Term SOFR rates for use", August 2021 (secondary, law-firm summary of ARRC best practices of 21 July 2021) | https://www.dechert.com/knowledge/onpoint/2021/8/term-sofr-is-here---the-arrc-recommends-cme-group-s-term-sofr-ra.html | 2026-09-24 | search summary: "does not support the use of SOFR Term Rates for derivatives markets, except for end users to hedge cash products" | dat:rc:modelling-overnight-rate-products:term, sec. 10.5 |
| F3 | FOMC meetings 2026: Jan 27-28, Mar 17-18, Apr 28-29, Jun 16-17, Jul 28-29, Sep 15-16, Oct 27-28, Dec 8-9; 2027 (tentative): Jan 26-27, Mar 16-17, Apr 27-28, Jun 8-9, Jul 27-28, Sep 14-15, Oct 26-27, Dec 7-8 | Federal Reserve, Meeting calendars | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | 2026-09-24 | calendar table; "Each meeting date is tentative until confirmed at the meeting immediately preceding it" | FOMC list in rc_rfr.py, fig:rc:modelling-overnight-rate-products:profile, dat:rc:modelling-overnight-rate-products:term |
| F4 | Lyashenko and Mercurio (2019) extend the LIBOR market model to forward-looking and backward-looking term rates driven by one process: the generalised forward market model | A. Lyashenko and F. Mercurio, "Looking forward to backward-looking rates: a modeling framework for term rates replacing LIBOR", SSRN 3330240, 2019 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3330240 | 2026-09-24 | abstract | def:rc:modelling-overnight-rate-products:gfmm, omsources |
| F5 | Cheyette (1992): when forward-rate volatilities have a separable form an HJM model is a finite-state Markov system (one-factor, two-state example) | O. Cheyette, "Term structure dynamics and mortgage valuation", Journal of Fixed Income 1(4), 28-41, 1992 | https://www.pm-research.com/content/iijfixinc/1/4/28 | 2026-09-24 | bibliographic record and summaries | def:rc:modelling-overnight-rate-products:cheyette, omsources |

## EXCLUDED

- Term SOFR licensing terms and fees (CME): not needed. The SOFR curve (chapter 1) and the Hull-White parameters are illustrative; the meeting-jump model is a teaching model. Re-checked 2026-09-24: not needed.

