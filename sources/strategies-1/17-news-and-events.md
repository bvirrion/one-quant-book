# 17. News and Events — brief and source ledger

## Brief

- **Hook.** A headline arrives at 10:32:07; machines trade on it in milliseconds, and the price's move is over before a person has read the first sentence.
- **Sections.** Machine-readable news; Scheduled events; Unscheduled events and halts; Reaction speed and who captures the move.
- **Defines.** machine-readable news, trading halt, news reaction window.
- **Uses (defined earlier).** event study (ch7), limit up--limit down (B1.31), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** headline sentiment; scheduled-event drift; post-halt reopening; underreaction to low-attention news.
- **Tutorial.** Generate a synthetic news stream with planted tone and attention on firm.synthmkt, measure the reaction by latency bucket, and trade the drift left for slower traders; model halts and reopening auctions.
- **Build.** `firm.newsevent`: synthetic news stream (timestamps, tone, relevance, attention), event-time reaction by latency, and halt/reopen handling; Python.
- **Weekend problem.** Before a person reads it — named result: the share of the news move captured at each latency, and the drift left for a daily trader.
- **Facts to verify.** Tetlock 2007 (JF); Tetlock, Saar-Tsechansky, Macskassy 2008 (JF); Hirshleifer, Lim, Teoh 2009 driven to distraction (JF); SEC and FINRA trading halt rules (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | P. C. Tetlock, "Giving content to investor sentiment: the role of media in the stock market", Journal of Finance 62(3) (2007) 1139-1168: daily content of a popular Wall Street Journal column, measured quantitatively; high media pessimism predicts downward pressure on market prices followed by a reversion to fundamentals, and unusually high or low pessimism predicts high trading volume | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1540-6261.2007.01232.x | 2026-09-25 | abstract: "high media pessimism predicts downward pressure on market prices followed by a reversion to fundamentals, and unusually high or low pessimism predicts high market trading volume" | section 1; strat:s1:news-and-events:sentiment; omsources |
| F2 | P. C. Tetlock, M. Saar-Tsechansky, S. Macskassy, "More than words: quantifying language to measure firms' fundamentals", Journal of Finance 63(3) (2008) 1437-1467: the fraction of negative words in firm-specific news stories forecasts low earnings; stock prices briefly underreact to the information in negative words; predictability is largest for stories focused on fundamentals | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1540-6261.2008.01362.x | 2026-09-25 | abstract: "(1) the fraction of negative words in firm-specific news stories forecasts low firm earnings; (2) firms' stock prices briefly underreact to the information embedded in negative words" | section 1; section 4; strat:s1:news-and-events:sentiment; omsources |
| F3 | D. Hirshleifer, S. S. Lim, S. H. Teoh, "Driven to distraction: extraneous events and underreaction to earnings news", Journal of Finance 64(5) (2009) 2289-2325: the immediate price and volume reaction to a firm's earnings surprise is much weaker, and post-announcement drift much stronger, when more same-day earnings announcements are made by other firms; a trading strategy on the effect yields substantial alphas | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1540-6261.2009.01501.x | 2026-09-25 | abstract: "the immediate price and volume reaction to a firm's earnings surprise is much weaker, and post-announcement drift much stronger, when a greater number of same-day earnings announcements are made by other firms" | section 2; section 4; strat:s1:news-and-events:attention; omsources |
| F4 | Nasdaq Trader, trading halt codes: T1 "Halt - News Pending", T2 "Halt - News Released", T3 "News and Resumption Times", T5 single-stock trading pause, LUDP "Volatility Trading Pause" (limit up-limit down), MWC1-MWC3 market-wide circuit breaker halts | Nasdaq Trader, Trade Halt Codes page | https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes | 2026-09-25 | page lists codes T1 "Halt - News Pending", T2 "Halt - News Released", T3, LUDP "Volatility Trading Pause", MWC1-MWC3 | section 3; dat:s1:news-and-events:halts; strat:s1:news-and-events:halt |

## EXCLUDED

- Latencies of named news vendors or trading firms, and any firm's use of machine-readable news: no primary source fetched.
- SEC and FINRA halt rule texts (rule numbers and durations): not fetched; the dated box names only the Nasdaq halt codes, and the limit up--limit down and circuit-breaker mechanics are Book 1's.
- The stream's size, the reaction time constant, the attention function and the halt threshold are the chapter's own choices.
