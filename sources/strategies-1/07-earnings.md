# 7. Earnings — brief and source ledger

## Brief

- **Hook.** Firms announcing a surprise keep drifting in its direction for sixty days; the drift was documented in 1968 and was still there, smaller, in the 2010s.
- **Sections.** Post-earnings-announcement drift; Analyst revisions; Guidance and pre-announcements; The announcement-day options angle; Implementation around event dates.
- **Defines.** event study, post-earnings-announcement drift, earnings-revision strategy, announcement premium, event window.
- **Uses (defined earlier).** standardised unexpected earnings (B7.11), earnings surprise (B7.11), implied volatility (B1.25), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** SUE drift; revision momentum; announcement premium; straddle before announcements; pre-announcement trading.
- **Tutorial.** Trade the planted post-earnings drift of firm.synthmkt with point-in-time surprises: an event-time long--short book, holding periods from 5 to 60 days, and the effect of costs and of the drift's decay after chapter 13's planted break.
- **Build.** `firm.earnstrat`: event calendars from firm.fundpit, SUE and revision signals, event-time portfolio construction with holding windows, and the announcement premium; Python.
- **Weekend problem.** Sixty days of drift — named result: the SUE book's Sharpe ratio at holding periods of 5, 20 and 60 days, and its fall after the planted break.
- **Facts to verify.** Ball and Brown 1968 (J. Accounting Research); Bernard and Thomas 1989 (J. Accounting Research); Chan, Jegadeesh, Lakonishok 1996 momentum strategies (JF); Savor and Wilson 2016 earnings announcements and systematic risk (JF); Chordia, Goyal, Sadka, Sadka, Shivakumar 2009 liquidity and PEAD (FAJ).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Ball, P. Brown, "An empirical evaluation of accounting income numbers", Journal of Accounting Research 6(2) (1968) 159-178 | Crossref metadata | https://doi.org/10.2307/2490232 | 2026-09-25 | Crossref: authors, title, journal, volume, issue, first page, year | section 1; omsources |
| F2 | V. L. Bernard, J. K. Thomas, "Post-earnings-announcement drift: delayed price response or risk premium?", Journal of Accounting Research 27 (1989) 1-36 | Crossref metadata | https://doi.org/10.2307/2491062 | 2026-09-25 | Crossref: authors, title, journal, volume, first page, year | section 1; omsources |
| F3 | L. K. C. Chan, N. Jegadeesh, J. Lakonishok, "Momentum strategies", Journal of Finance 51(5) (1996) 1681-1713: past returns and past earnings surprises each predict large drifts in future returns after controlling for the other; not explained by market risk, size or book-to-market; analysts' forecasts also respond sluggishly to past news | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1540-6261.1996.tb05222.x | 2026-09-25 | abstract: "Past return and past earnings surprise each predict large drifts in future returns after controlling for the other"; "Security analysts' earnings forecasts also respond sluggishly to past news" | section 1; section 2; strat:s1:earnings:sue; strat:s1:earnings:revision; omsources |
| F4 | P. Savor, M. Wilson, "Earnings announcements and systematic risk", Journal of Finance 71(1) (2016) 83-138: firms scheduled to report earnings earn an annualised abnormal return of 9.9%; explained by announcement risk (covariance of firm-specific and market cash-flow news spikes around announcements); the premium is persistent across stocks; early announcers earn more | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/jofi.12361 | 2026-09-25 | abstract: "Firms scheduled to report earnings earn an annualized abnormal return of 9.9%" | section 4; strat:s1:earnings:premium; omsources |
| F5 | T. Chordia, A. Goyal, G. Sadka, R. Sadka, L. Shivakumar, "Liquidity and the post-earnings-announcement drift", Financial Analysts Journal 65(4) (2009) 18-32: the drift occurs mainly in highly illiquid stocks; a long-short surprise strategy returns 0.04% a month (value-weighted) in the most liquid stocks and 2.43% in the most illiquid; transaction costs account for 70-100% of the paper profits | Crossref metadata; OpenAlex abstract | https://doi.org/10.2469/faj.v65.n4.3 | 2026-09-25 | abstract: "provides a monthly value-weighted return of 0.04 percent in the most liquid stocks and 2.43 percent in the most illiquid stocks"; "transaction costs account for 70-100 percent of the paper profits" | hook; section 5; strat:s1:earnings:sue; omsources |
| F6 | C. Martineau, "Rest in peace post-earnings announcement drift", Critical Finance Review 11(3-4) (2022) 613-646: in modern markets prices fully reflect earnings surprises on the announcement date; for large stocks the drift has been non-existent since 2006, and has only recently disappeared for microcaps | Crossref metadata; abstract of the SocArXiv preprint (2021) | https://doi.org/10.1561/104.00000122 ; https://doi.org/10.31235/osf.io/z7k3p | 2026-09-25 | preprint abstract: "For large stocks, PEAD have been non-existent since 2006 but has only disappeared recently for microcap stocks" | hook; section 1; strat:s1:earnings:sue; omsources |

## EXCLUDED

- Ball and Brown (1968), Bernard and Thomas (1989): content not retrieved (keywords only in OpenAlex); cited as the classic references without quoting results (the brief's '60 days' and '1968 documentation' claims are not made).
- Guidance, pre-announcement and options-around-earnings performance records: no primary source fetched; those strategy files say so.
- Named firms: none.

