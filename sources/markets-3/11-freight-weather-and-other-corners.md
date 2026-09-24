# 11. Freight, Weather and Other Corners — brief and source ledger

## Brief

- **Hook.** A gas utility's winter profit depends on the temperature; it buys a contract that pays per heating degree day below an agreed total, settled on a weather station at an airport.
- **Sections.** Freight: charters, routes and the Baltic indices; Forward freight agreements; Weather: degree days and weather derivatives; What makes a market tradable at all.
- **Defines.** voyage charter, time charter, time-charter equivalent, route index, forward freight agreement, heating degree day, cooling degree day, weather derivative, burn analysis.
- **Uses (defined earlier).** cash settlement, basis risk, calendar month average, hedger, speculator, open interest, commodity swap.
- **Tutorial.** Compute winter heating-degree-day totals from NOAA daily temperatures (public domain) for one station over thirty winters, price a degree-day swap by burn analysis, and plot the distribution of payouts.
- **Build.** `firm.degreeday`: degree-day indices, burn-analysis pricer for swaps and options, and monthly-average settlement of freight agreements.
- **Weekend problem.** The warm winter — named result: the burn-analysis fair strike of a heating-degree-day swap and the one-in-ten-year payout of a put bought by a gas utility.
- **Facts to verify.** Baltic Exchange ownership (SGX since 2016) and route definitions (Capesize 5TC); FFA clearing venues (SGX, EEX) and settlement on the monthly average; CME weather futures (cities, HDD/CDD definitions, base 65 F); first weather derivative trade 1997 and CME launch 1999; NOAA GHCN-Daily data and its public-domain status; other contract launches and failures (e.g. CME water futures 2020) from exchange notices.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SGX and the Baltic Exchange confirmed completion of the acquisition on 8 November 2016 (agreed 22 August 2016) | Baltic Exchange news, "SGX and the Baltic Exchange confirm completion of acquisition" | https://www.balticexchange.com/en/news-and-events/news/member-news/2016/sgx-and-the-balticexchangeconfirmcompletionofacquisition.html | 2026-09-24 | "announced on 8 November that the acquisition was completed" (search excerpt) | dat:m3:freight-weather-and-other-corners:baltic |
| F2 | Capesize 5TC is a weighted average of five time-charter routes; SGX freight futures settle in cash on the arithmetic average of the Baltic Exchange's daily assessments in the contract month | SGX freight contract specifications; SGX rulebook Appendix 1 (search excerpts) | https://api2.sgx.com/sites/default/files/2026-06/SGX%20Freight%20Time%20Charter%20Options%20Specs%20-%20Full%20Contract%20specs.pdf | 2026-09-24 | "the weighted average of 5 different routes globally is used to derive the daily 5TC Capesize index"; settle "against the arithmetic average price of spot freight published by the Baltic Exchange" (search excerpts) | def route; dat:m3:freight-weather-and-other-corners:ffa |
| F3 | HDD/CDD measure deviations of daily average temperature from 65 F; CME listed HDD futures in September 1999 (CFTC approval August 1999) and CDD in January 2000; OTC weather derivatives from 1997; first standalone OTC deal a Koch Energy/Enron HDD swap for a Milwaukee winter | CME Group, "Overview of weather markets" and "Weather options overview" (search excerpts) | https://www.cmegroup.com/education/lessons/overview-of-weather-markets | 2026-09-24 | "the very first weather futures contracts listed in September 1999 were based upon HDDs"; "CDD based contracts were subsequently introduced in January 2000" (search excerpts) | def dd; dat:m3:freight-weather-and-other-corners:cme |
| F4 | Chicago O'Hare (USW00094846) daily TMAX/TMIN, Nov 1990 to Mar 2026: 36 complete winters, mean 4,912 HDD, sd 477, warmest 2011/12 (3,932), coldest 2013/14 (5,999), trend -125 HDD per decade | NOAA NCEI GHCN-Daily access file; data/markets-3/ohare_tmax_tmin_daily.csv | https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/USW00094846.csv | 2026-09-24 | downloaded file | hook; §3-4; figs; problem |
| F5 | CME Degree Days Index Futures (ch. 403): HDD = max(0, 65°F - daily average), CDD symmetric; index accumulates degree days over the calendar month; 13 listed cities with named automated weather stations (e.g. Chicago O'Hare, WBAN 94846); trading unit $20 times the index; minimum fluctuation 1 index point = $20 | CME Rulebook ch. 403 (Internet Archive copy) | https://web.archive.org/web/2025/https://www.cmegroup.com/rulebook/CME/IV/400/403/403.pdf | 2026-09-24 | "The size of the unit of trading shall be $20 times the respective CME Degree Days Index"; "The minimum price fluctuation ... shall be 1 index point and have a value of $20"; "Chicago O'Hare International Airport (WBAN 94846)" | dat:m3:freight-weather-and-other-corners:cme |

## EXCLUDED

- Exact CME weather contract cities, ticks and index rounding rules today: not fetched; the chapter's contract is an illustrative OTC put with a $20,000 tick. **restored → F5 (the chapter's own contract stays an illustrative OTC put).**
- Iron-ore voyage costs and rates in the TCE example are illustrative. **illustrative by design, not a sourcing gap.**
