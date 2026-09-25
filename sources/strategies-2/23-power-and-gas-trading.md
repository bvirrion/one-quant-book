# 23. Power and Gas Trading — brief and source ledger

## Brief

- **Hook.** Power bought the day before for delivery tomorrow and power bought an hour before delivery are different products; the spread between them pays traders who forecast the wind better than the market.
- **Sections.** Day-ahead against intraday; Weather-driven positions; Batteries and flexible assets; Risk in power books.
- **Defines.** day-ahead-intraday spread, weather-driven position, battery arbitrage.
- **Uses (defined earlier).** day-ahead market (B3.5), locational marginal price (B3.5), weather derivative (B3.11), spark spread (B3.5), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** forecast-error intraday trade; weather-driven gas position; battery day-ahead arbitrage; spark-spread plant optimisation; negative-price hours.
- **Tutorial.** From Book 3's German hourly power data measure the day-ahead price profile and negative hours, simulate intraday prices with planted wind forecast errors, and optimise a battery against both markets.
- **Build.** `firm.powergas`: day-ahead and intraday price models, forecast-error trades and battery optimisation by dynamic programming; Python.
- **Weekend problem.** The wind forecast — named result: the battery's revenue in day-ahead only and with intraday re-optimisation.
- **Facts to verify.** German power data (as B3, data/markets-3/de_power_hourly_2024_2025.csv); Kiesel and Paraschiv 2017 econometric analysis of 15-minute intraday electricity prices (Energy Economics).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Kiesel, F. Paraschiv, "Econometric analysis of 15-minute intraday electricity prices", Energy Economics 64 (2017) 77-90: trading in the German intraday market has increased, partly because more wind and PV requires generators to balance forecast errors; with 15-minute intraday prices and intraday-updated wind and PV forecasts, intraday prices adjust asymmetrically to renewable forecast errors and to trade volume, depending on a threshold demand quote | RePEc abstract | https://ideas.repec.org/a/eee/eneeco/v64y2017icp77-90.html ; https://doi.org/10.1016/j.eneco.2017.03.002 | 2026-09-25 | abstract: "intraday prices adjust asymmetrically to both forecasting errors in renewables and to the volume of trades dependent on the threshold variable demand quote" | hook; section 1; strat:s2:power-and-gas-trading:forecast; solutions; omsources |
| F2 | F. Ziel, "Modeling the impact of wind and solar power forecasting errors on intraday electricity prices", 14th International Conference on the European Energy Market (EEM) 2017: a regression model of German intraday prices quantifies wind and solar forecast-error effects; no statistically significant evidence that positive and negative errors have different impacts | Crossref metadata; OpenAlex abstract | https://doi.org/10.1109/EEM.2017.7981900 | 2026-09-25 | abstract: "there is no statistically significant evidence that positive wind or solar forecasting errors have a different impact on intraday electricity prices than negative ones" | section 1; exercise 6; solutions; omsources |
| F3 | Germany DE-LU hourly day-ahead prices, generation and load 2024-2025 (Book 3's file data/markets-3/de_power_hourly_2024_2025.csv, Bundesnetzagentur / SMARD.de, CC BY 4.0): mean EUR 78.51 (2024), 89.32 (2025); negative hours 457 and 573; minima -135.45 and -250.32; negative share 23.4% at 13:00 local, 0 at 19:00-20:00; price on residual load slope EUR 3.05/MWh per GW, correlation 0.83; 727 days of 24 hours | computed by s2_powergas.real() | https://www.smard.de | 2026-09-25 | computed statistics (CC BY 4.0 data, attribution Bundesnetzagentur / SMARD.de) | hook; sections 1, 3 and 4; fig:s2:power-and-gas-trading:profile; strat:s2:power-and-gas-trading:negative; strat:s2:power-and-gas-trading:battery; solutions |

## EXCLUDED

- German intraday prices (EPEX continuous or ID3 indices) and day-ahead wind forecasts: licensed; the intraday market and its wind forecast errors are synthetic (planted: EUR 3.05/MWh per GW, error sd 2 GW, hourly autocorrelation 0.9, other noise EUR 6).
- Gas prices and temperature forecasts for the weather-driven position: not fetched; the strategy file states the mechanism only.
- Battery fleet sizes and revenues by market: Book 3 ch. 6 carries the dated figures; not repeated here.
- Named firms' power or battery trading: no citable primary source; no firm named.
