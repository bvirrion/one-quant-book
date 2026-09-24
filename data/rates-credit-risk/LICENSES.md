# Data used by One Quant Book 6 (rates-credit-risk)

| file / constant | source | licence | used in |
|---|---|---|---|
| `ECB_2026_09_22`, `ECB_SPOT_2026_09_22` in `code/rates-credit-risk/01-curve-construction/python/rc_curves.py` | ECB Data Portal, euro-area AAA yield curve (Svensson parameters and spot rates, 22 September 2026) | ESCB statistics reuse policy: free reuse with the source quoted ("Source: ECB statistics"), not modified | ch. 1 |
| `treasury_par_yields.csv` | US Treasury, Daily Treasury Par Yield Curve Rates, 2016-01-04 to 2026-09-23 (columns 1Y-30Y) | US Government work, public domain (17 U.S.C. 105) | ch. 3 |
| `henry_hub_daily_2020_2021.csv` | US Energy Information Administration, Henry Hub Natural Gas Spot Price, daily (series RNGWHHD), 2020-12-01 to 2021-04-30, from https://www.eia.gov/dnav/ng/hist/rngwhhdD.htm (accessed 2026-09-24) | US Government work, public domain (17 U.S.C. 105); EIA asks for attribution | ch. 16 |
| `ecb_fx_2016_2026.csv` | ECB reference exchange rates, US dollar/euro and Japanese yen/euro, daily, 2016-01-04 to 2026-09-23, ECB Data Portal API (series EXR.D.USD.EUR.SP00.A and EXR.D.JPY.EUR.SP00.A, accessed 2026-09-24) | ESCB statistics reuse policy: free reuse with the source quoted ("Source: ECB statistics") | ch. 21 |
| `stress_2008.csv` | US Treasury daily par yields (2Y, 10Y), 2008 (home.treasury.gov daily Treasury par yield curve CSV), joined with ECB reference rates USD/EUR and JPY/EUR for 2008 | US Government work, public domain (17 U.S.C. 105); ECB statistics reuse policy ("Source: ECB statistics") | ch. 22 |
