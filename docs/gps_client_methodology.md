# Research, advisory and commercial methodology

## Research provenance and limits

The official snapshot reuses the selected Federal Reserve releases already recorded in [the market observation table](../data/market/observations.csv). The file includes release dates, native quotes and source URLs. The research UI adds the supplier name, retrieval date and reuse notes. Federal Reserve Board material is generally public domain unless indicated otherwise. [Federal Reserve disclaimer](https://www.federalreserve.gov/disclaimer.htm)

Upload CSV columns in this order for convenience. Header names determine field mapping.

```text
series,observed_on,published_on,retrieved_on,unit,value,source_name,source_url,licensing_notes
```

Use ISO dates and HTTPS URLs. Supported series are `Fed target midpoint` in `Percent per year`, plus `USD/CNY`, `USD/HKD` and `USD/SGD` in `CNY per USD`, `HKD per USD` and `SGD per USD`. Publication date determines data visibility. Uploaded provenance is user-supplied and must be checked against the source. The fallback contains synthetic inputs only. Market data provides context and does not reprice the historic synthetic ledger. The corporate scenario uses the shared 30-day forecast and the assumptions in the [market methodology](citi_methodology.md).

## Client segmentation and recommendations

Harbor Components uses the shared treasury dataset. Meridian Services uses seed 44 and reports on Shanghai and Singapore accounts. Jade Disbursements uses seed 43. Its domestic fixture splits each HKD instruction into 20 integer-cent transactions while preserving total instructed principal. Fee and settlement calculations run on the resulting records. Jade excludes foreign supplier schedules and intercompany transfers. Every dashboard client uses a trailing 30-calendar-day instruction cohort evaluated as of the ledger cutoff. Singapore attribution uses up to ten unique receipts, plus a synthetic duplicate feed row where available. Median delay covers settled instructions only.

The cash need is the maximum same-day sum of individual buffer shortfalls after five days of receipt delay, translated into USD and shown gross before netting. A positive gap triggers liquidity advice, an FX value share of at least 25% triggers currency review, and unmatched receipts trigger collection advice. Failed/pending payments support exception triage. Trade-finance discovery requires importer/exporter context and FX exposure. Invoice terms, acceptance and counterparty checks would be needed to size a facility. The proposal uses the same calculation and recommendation functions as the dashboard.

## Commercial formulas

- Annual modeled volume is the selected monthly input × 12. The default monthly input uses the trailing synthetic 30-day count as a run-rate proxy. Amounts are integer USD cents.
- Processing cost equals annual payment count × fee. FX cost equals annual volume × average payment size × FX share × spread in basis points divided by 10,000. Labour effort equals annual count × minutes × hourly labour cost divided by 60.
- Capital tied up equals annual instructed principal × funding days divided by 365. The carrying expense is this balance × assumed annual cost of funds. Required buffers are memo balances and excluded from savings to avoid overlap.
- First-year client savings equal modeled baseline costs less proposed costs and client setup expense. The client and provider models have separate setup expenses. Provider revenue equals proposed processing fees and FX spread × expected adopters. Expected adopters are prospect count × assumed adoption.
- Provider contribution deducts modeled recurring servicing and processing costs plus upfront rollout cost. Simple payback is upfront rollout cost divided by monthly recurring contribution. It is unavailable when recurring contribution is zero or negative.
- The baseline and proposal assume immediate adoption, stable volumes, and no tax, ramp, churn or discounting. The portfolio includes no observed client conversion, pricing or revenue. Funding availability, actual corridor access and regulatory eligibility require separate diligence.
