# 15. Alternative-Data Pipelines — brief and source ledger

## Brief

- **Hook.** A card-spending panel nowcasts a retailer's quarterly sales within 2 % for three years and then misses by 9 %: the panel's bank partner had changed, and the panel's customers were no longer the retailer's.
- **Sections.** Ingestion and validation; Mapping to securities; Panel bias and reweighting; Detecting backfill; From pipeline to predictor.
- **Defines.** ingestion pipeline, schema validation, entity resolution, record linkage, panel bias, panel reweighting, first-seen timestamp.
- **Uses (defined earlier).** alternative data (B7.12), panel drift (B7.12), backfill bias (B7.3), data trial (B7.12), incremental information coefficient (B7.12), knowledge time (B7.3), bitemporal data (B7.3), security master (B7.4), alternative-data strategy (B8.16), nowcast (B8.16), data decay (B8.16), entity linking (ch13), covariate shift (ch12), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Build a synthetic card-spend panel from firm.synthmkt fundamentals (true sales), with panel churn, a demographic tilt that drifts, a partner change, merchant strings to resolve to tickers and a vendor history backfilled after launch; ingest with schema checks, resolve entities, reweight the panel, nowcast sales and compare the backfilled history's IC with the live IC using first-seen timestamps. Data: synthetic.
- **Build.** `firm.altdata`: an ingestion pipeline with schema and range validation into firm.pit, fuzzy entity resolution to firm.secmaster identifiers with a review queue, panel reweighting (raking to known margins), first-seen versus as-of backfill detection, and a nowcast on top of firm.vendoreval; Python.
- **Weekend problem.** The panel that grew -- named result: the nowcast error with and without reweighting after the partner change, and the IC of the backfilled history against the live one.
- **Facts to verify.** Froot, Kang, Ozik and Sadka 2017 what do measures of real-time corporate sales say about earnings surprises and post-announcement returns? (JFE); Kolanovic and Krishnamachari 2017 big data and AI strategies (J.P. Morgan report, public); Fellegi and Sunter 1969 a theory for record linkage (JASA); Deming and Stephan 1940 raking (Annals of Math. Stat.); Katona, Painter, Patatoukas and Zeng 2025 on the capital market consequences of big data: evidence from outer space (JFQA) or equivalent; Dichev and Qian or equivalent evidence on alternative-data decay (to verify).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | I. P. Fellegi, A. B. Sunter, "A theory for record linkage", JASA 64(328) 1969: recognising records in two files that represent identical entities | Crossref/OpenAlex record | https://doi.org/10.1080/01621459.1969.10501049 | 2026-09-25 | abstract: "recognizing those records in two files which represent identical persons, objects or events" | def. record linkage; omsources |
| F2 | W. E. Deming, F. F. Stephan, "On a least squares adjustment of a sampled frequency table when the expected marginal totals are known", Annals of Mathematical Statistics 11(4) 1940 (raking) | Crossref/OpenAlex record | https://doi.org/10.1214/aoms/1177731829 | 2026-09-25 | title, journal, year as registered | def. panel reweighting; omsources |
| F3 | K. A. Froot, N. Kang, G. Ozik, R. Sadka, "What do measures of real-time corporate sales say about earnings surprises and post-announcement returns?", JFE 2017: real-time retail sales proxies from about 50 million mobile devices | Crossref/OpenAlex (JFE record; abstract of NBER w22366) | https://doi.org/10.1016/j.jfineco.2017.04.008 | 2026-09-25 | NBER w22366 abstract: "real-time proxies of retail corporate sales from multiple sources, including ~50 million mobile devices" | sec. pipeline to predictor; omsources |
| F4 | Z. Katona, M. Painter, P. N. Patatoukas, J. Zeng, "On the capital market consequences of big data: evidence from outer space", JFQA 2024: satellite coverage of retailers let investors with the data trade profitably, especially ahead of bad-news reports | Crossref/OpenAlex record | https://doi.org/10.1017/s0022109023001448 | 2026-09-25 | abstract: "Satellite data enabled sophisticated investors ... to formulate profitable trading strategies, especially by targeting the upcoming reports of retailers with bad news" | sec. pipeline to predictor; omsources |

## EXCLUDED

- The hook's 3.3 and 22.5 points and every count, error and IC are the chapter's synthetic panel (firm.altdata.card_panel, ml_altdata), tested in code/ml/15-alternative-data-pipelines/tests/test_solutions.py; the retailers, merchant strings and vendor are invented, the ten distractor strings are generic merchant descriptors.
- Kolanovic and Krishnamachari 2017 (J.P. Morgan report): no registry record; not cited.
- Dichev and Qian or other evidence on alternative-data decay (planned "to verify"): not found in a registry search; decay is left to Book 8 (chapter 16) and Book 7 (chapter 28).
- The brief's firm.synthmkt fundamentals as the true sales: replaced by card_panel's own sales process so that the population cells, panel and truth share one construction.
