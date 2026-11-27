# Data dictionary

The SQLite generator creates each table below. ISO dates use calendar-day granularity. Monetary fields ending in `_minor` store signed or unsigned integer cents as appropriate. Excel exports show major units. Group-valued fields carry the USD label.

| Table | Primary key | Fields and accounting meaning |
| --- | --- | --- |
| `accounts` | `id` | Booking `region`, local `currency`, `opening_minor` before the historical period, `buffer_minor` in local currency |
| `fx` | `day, currency` | `usd_ppm` is USD per currency unit multiplied by 1,000,000 |
| `payments` | `id` | Booking `account`, `instructed` date, instruction `currency` and `principal_minor`, destination region, `status` and nullable `outcome_day` |
| `cashflows` | `id` | `account`, posting `day`, external receipt `amount_minor` in account currency |
| `scheduled` | `id` | `account`, earliest `known_on` date, planned `due_on` date, receipt or supplier `kind`, instruction `currency` and positive `amount_minor` |
| `transfers` | `id` | Posting `day`, `source` and `target` account IDs, `amount_minor` in source currency |
| `daily_balances` | `day, account` | Materialized history with local opening, inflow, outflow, fees, both transfer legs, closing and buffer, plus translated closing USD |

The app recomputes balances from source tables so the ledger and payment visibility use the selected as-of date. Payment detail adds corridor, local settled principal, fee components, dated USD equivalents and elapsed days. Scenario comparison includes expected movement components and scenario-minus-expected closing deltas in local currency and USD.

## Derived demonstration records

| Record | Fields |
| --- | --- |
| Virtual account mapping | Fictional identifier, master account ID, synthetic customer label |
| Receipt attribution | Posting day, synthetic bank reference, posted account, virtual identifier, amount, attribution status and matched customer |
| Settlement option | Assumed minutes and costs, local principal, balance before and after settlement, buffer shortfall and minute-by-minute event points |
| Review event | Session-local sequence, case ID, previous status and selected decision |

The demonstrations derive from or reference historical data. They add no postings or SQLite source tables.
