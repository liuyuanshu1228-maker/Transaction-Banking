# Market and commercialisation methodology

## Public data sources

The versioned [observation table](../data/market/observations.csv) records the source URL, selected observation date or report year, publication date, frequency, units and value. The dashboard filters on publication date, including the H.10 lag between Friday observations and Monday releases. The research cutoff is independent of the synthetic ledger date. The sample is sparse and is intended for historical comparison.

| Series | Source and measurement |
| --- | --- |
| USD policy target | Midpoint of the Fed's announced target range at three selected decisions. Percent per year. [Federal Reserve](https://www.federalreserve.gov/newsevents/pressreleases/monetary20250618a.htm) |
| USD/CNY, USD/HKD, USD/SGD | Local currency per USD, selected Friday daily figures in H.10 weekly releases. [Federal Reserve H.10](https://www.federalreserve.gov/releases/h10/20250728/) |
| Wholesale payment speed | Percent of measured, non-forward-dated wholesale payments credited within one business day, by FSB report year. The metric uses the report's Swift data coverage. [FSB 2026 report](https://www.fsb.org/2026/11/g20-roadmap-for-enhancing-cross-border-payments-consolidated-progress-report-for-2026/) |

## Synthetic scenario

The baseline uses the original synthetic forecast and closing ledger. Each FX quote shift is specified in basis points relative to local currency per USD. The scenario divides the ledger's reciprocal USD-per-local rate by the quote multiplier. It reprices known future cash flows and group translation with that rate. Historical local cash stays booked at its historical amount. Additional spread affects cross-currency supplier costs. Delayed receipts outside 30 days drop out of the display horizon.

The rate shock applies full pass-through to assumed USD 500,000 rate-sensitive cash and USD 1,000,000 floating debt on ACT/365. Incremental net interest adjusts consolidated cash on day 30. The gross funding requirement takes the maximum daily sum of local buffer shortfalls translated to USD before the interest adjustment, with no surplus netting. These are conditional scenario results. The model excludes live rates, interest curves, forward hedges, correlations and funding availability.

## Commercialisation assumptions

- Segment sizes, volumes, currency shares, manual processing and idle cash are fictional. All fee and value figures use USD and a 12-month horizon. Displayed adopted client counts are expected equivalents.
- Payment value assumes a 25 bp reduction on modeled foreign-currency principal. Virtual account value assumes 70% fewer manual cases and USD 3 of effort per case. Liquidity value assumes 20% of modeled idle cash can earn 3% per year.
- Annual client fees equal 12 months of subscription and usage fees. Net client value deducts the full modeled offer fee from gross benefit. Fee income multiplies annual fees by expected adopters. Cost to serve applies the service-cost factor to ongoing per-client cost and onboarding, then adds fixed annual platform cost.
- The recommendation chooses the highest net client value among offers meeting the product fit threshold and showing positive per-client provider contribution before fixed cost. Evaluate cohort break-even separately before investment. The product comparison treats each offer as a standalone alternative.
- Estimates omit taxes, rollout and churn, financing and acquisition costs, and migration effort beyond the onboarding line. Effort value requires actual redeployment of time. No figures represent observed pricing or commercial performance.
