# 26. Culture and Decision-Making — brief and source ledger

## Brief

- **Hook.** In a forecasting tournament run for the US intelligence community from 2011 to 2015, teams of volunteers who wrote down probabilities, were scored on them and argued in the open beat the other entrants year after year. Writing a number down and being scored on it is most of what a betting culture is.
- **Sections.** Betting cultures: probabilities, not opinions; Scoring forecasts and decisions; Post-mortems and pre-mortems; How good firms disagree.
- **Defines.** decision journal, Brier score, outcome bias, pre-mortem, red team, forecast aggregation.
- **Uses (defined earlier).** forecast calibration (B7.15), calibration curve (B7.15), edge (B2.29), Kelly criterion (B2.29), garden of forking paths (B4.12), research review (B7.1), pre-registration (B7.1), blameless review (B15.28).
- **Tutorial.** A year of a desk's decision journal (synthetic forecasters with different skill and bias recording probabilities): compute each one's Brier score and its decomposition into reliability and resolution, draw calibration curves, then compare aggregating five independent forecasts (mean, mean of log-odds, extremised) with one forecast made after a discussion that correlates the errors. End state: calibration curves, and a table of Brier scores by aggregation rule.
- **Build.** `firm.decisionlog`: a decision journal (decision, options, probabilities, expected values, outcome, dates), the Brier score and Murphy's decomposition, calibration binning, forecast aggregation (linear, log-odds, extremised), and an outcome-bias check (decisions judged by outcome against by process); Python.
- **Weekend problem.** Five opinions or one -- named result: the Brier-score improvement from aggregating five independent forecasts against one discussed forecast whose errors are correlated at a given level.
- **Facts to verify.** Mellers et al. 2014 (Psychological Science) and Tetlock and Gardner 2015: the Good Judgment Project results in the IARPA tournament; Brier 1950 (Monthly Weather Review); Murphy 1973 (J. Applied Meteorology) decomposition; Satopaa et al. 2014 (Int. J. Forecasting): log-odds aggregation and extremising; Klein 2007 (Harvard Business Review): the pre-mortem; Baron and Hershey 1988 (JPSP): outcome bias; Janis 1972, Victims of groupthink.
- **Data.** Synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | B. A. Mellers et al., "Psychological Strategies for Winning a Geopolitical Forecasting Tournament", Psychological Science 25(5), 1106-1115, 2014: five university-based research groups competed in a two-year geopolitical forecasting tournament; the authors' group found that probability training, teaming (sharing information and discussing rationales) and tracking (top performers in elite teams) improved both calibration and resolution; combined with statistical aggregation, their approach produced the best forecasts two years in a row | OpenAlex abstract | https://doi.org/10.1177/0956797614524255 | 2026-09-28 | "Five university-based research groups competed"; "a 2-year geopolitical forecasting tournament"; "probability training, team collaboration, and tracking improved both calibration and resolution"; "produced the best forecasts 2 years in a row" | hook; section 1 |
| F2 | G. W. Brier, "Verification of forecasts expressed in terms of probability", Monthly Weather Review 78(1), 1950 | OpenAlex | https://doi.org/10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2 | 2026-09-28 | bibliographic | section 2 |
| F3 | A. H. Murphy, "A New Vector Partition of the Probability Score", Journal of Applied Meteorology 12, 1973: the partition of the Brier score into uncertainty, reliability and resolution | OpenAlex abstract | https://doi.org/10.1175/1520-0450(1973)012<0595:ANVPOT>2.0.CO;2 | 2026-09-28 | "The new partition consists of three terms: 1) a measure of the uncertainty ... 2) a measure of the reliability of the forecasts; and 3) a new measure of the resolution" | section 2 |
| F4 | V. A. Satopaa et al., "Combining multiple probability predictions using a simple logit model", International Journal of Forecasting, 2014 | OpenAlex | https://doi.org/10.1016/j.ijforecast.2013.09.009 | 2026-09-28 | bibliographic | section 2 |
| F5 | J. Baron and J. C. Hershey, "Outcome bias in decision evaluation", Journal of Personality and Social Psychology 54(4), 1988 | OpenAlex | https://doi.org/10.1037/0022-3514.54.4.569 | 2026-09-28 | bibliographic | section 3 |

## EXCLUDED

- Tetlock and Gardner (2015), Klein (2007) and Janis (1972): cited as ideas without restating their findings; not fetched.
- The IARPA sponsorship and the 2011-2015 dates of the tournament: not in the retrieved abstract; not stated.

