# Corporate Cash & Cross-Border Payments Analytics

**Synthetic Data — Educational Portfolio Demonstration**

A transaction banking portfolio project for a fictional treasury team in Hong Kong, Shanghai and Singapore. It combines payment operations, multi-currency cash reconciliation and 30-day liquidity planning in a single Streamlit app. The project is independent and unaffiliated with any bank.

## What the simulation shows

The default seed produces 210 days of history, 630 payment instructions and 630 daily account balances through **29 July 2025**.

| Measure | Default portfolio result |
| --- | ---: |
| Group cash at closing FX | USD 4,550,443.28 |
| Instructions settled by the reporting date | 91.9% |
| Modeled cost of settled payments | USD 17,877.19 |
| Expected cash on forecast day 30 | USD 4,749,348.34 |
| Conservative cash on forecast day 30 | USD 4,307,682.00 |
| Conservative buffer breaches | 21 account-days |

Holding exchange rates at the as-of midpoint, the conservative case finishes USD 441,666.34 below the expected case. The largest modeled gap is SGD 136,034.46 in Singapore on 5 August 2025. This is a synthetic funding signal, and the day-30 difference includes cash timing within a finite forecast horizon.

## Run locally on Windows

Use PowerShell and Python 3.11+. The commands use the virtual environment interpreter directly.

```powershell
git clone https://github.com/liuyuanshu1228-maker/Transaction-Banking.git
cd Transaction-Banking
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.database
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dashboard also runs from a deterministic in-memory SQLite database when the local database file is absent. The data command creates `data/synthetic/treasury.sqlite` and preserves any existing file. To generate another seed or copy, use `python -m src.database --seed 43 --output data/synthetic/alternate.sqlite` from an activated environment.

## Global Payments Solutions portfolio review

The [alignment review](docs/gps_alignment.md) maps the project to payment operations, liquidity, product fit and client communication. The portfolio uses synthetic records and illustrative pricing and service-time assumptions.

## Citi Services portfolio extension

The China Summer Analyst role emphasizes market research, macroeconomic analysis, client opportunities and product commercialisation. The two new pages exercise those responsibilities through a dated market brief and a fictional go-to-market case. [Citi role description](https://jobs.citi.com/job/shanghai/services-summer-analyst-china-2027/287/102161042768)

- [Market Intelligence Brief](docs/market_intelligence_brief.md) covers selected Fed and H.10 observations plus FSB wholesale payment evidence.
- [Product commercialisation case](docs/product_commercialisation_case.md) evaluates a marketplace collections pilot from client and provider perspectives.
- [English client proposal](reports/client_product_proposal.pptx) is a separate, editable three-slide PowerPoint. The original treasury reports remain part of the portfolio.

## Bank of America GPS relevance

The portfolio demonstrates transferable work in treasury advisory, payments, working capital and commercial analysis. It is an independent educational project. [Bank of America Global Payments Solutions](https://careers.bankofamerica.com/en-us/company/organization/global-payments-solutions)

- **Research.** Inspect dated Federal Reserve observations or import a provenance-tagged rates and FX CSV. Compare published data with the synthetic company's open exposures and cash sensitivities.
- **Advisory.** Trace a recommendation to a seeded client cohort, a payment KPI or a stress gap. Export a seven-slide editable proposal for the selected case.
- **Commercial analysis.** Compare client cost savings and provider contribution independently, then stress adoption before discussing payback.

[Industry research brief](reports/industry_research_brief.md) · [Client treasury proposal](reports/client_treasury_proposal.pptx) · [Commercial case](reports/commercial_opportunity.md) · [Methodology](docs/gps_client_methodology.md) · [Three-minute walkthrough](docs/gps_demo.md) · [CV suggestions](docs/gps_cv.md)

AI assistance was used for coding, drafting and test development. The repository records reproducible inputs and executable checks.

## Dashboard

| Section | What to inspect |
| --- | --- |
| Executive Overview | Group and regional cash, cash buffers, 30-day external receipts, settled outflows and costs |
| Payment Analytics | An instruction-date cohort with corridor filters, status rates, currency mix, fee components and settlement delay, plus virtual collections, settlement comparison and educational exception review |
| Liquidity Forecast | Expected and conservative paths plus day-level account shortfalls and movement detail |
| Scenario Lab | Receipt and supplier delays, an account-specific expense, additional bank fees and FX spread shock |
| Business Recommendations | Client executive summary for liquidity, collections, payment routing and cost, with evidence and decision limits |
| Market Intelligence | Dated public evidence and separate 30-day sensitivity for rates, FX quotes, spreads and collection delays |
| Client & Product Strategy | Compare three fictional segments and standalone offers using first-year fees, client value and cost to serve |
| Market & Industry Intelligence | Review the fictional company's cash and currency exposures, official data provenance and market sensitivities |
| Client Solutions | Compare seeded payment and liquidity evidence for three clients and export a tailored proposal |
| Commercial Opportunity | Compare client costs and provider economics under configurable prices, costs and adoption |

Open the Scenario Lab and increase receipt delay. The comparison shows exactly which receipts move and the effect on daily cash. For a specific account, read the local currency columns, then use the USD columns for group comparison.

## Payment product demonstrations

- **Virtual accounts.** Three demo identifiers map to master account SG. The latest ten posted Singapore receipts include missing and unknown identifiers plus a repeated bank reference. The dashboard shows both count and amount rates. The default sample matches eight of ten unique receipts.
- **Settlement comparison.** Run an SGD or USD outgoing instruction against the same Singapore opening cash. Two hypothetical methods use one and 2,880 minutes, SGD 1 and SGD 6 fixed fees, and 20 and 35 bp spreads when the instruction needs FX. The chart shows when available cash falls and whether settlement puts it below the buffer.
- **Exception review.** Review synthetic collection exceptions and incomplete fictional verification. Clear or escalate a case and inspect the session event log. The demonstration uses simple rules and has no external identity check.

## Reports and checks

- [Excel treasury analysis](reports/treasury_analysis.xlsx) includes nine sheets with account, instruction, ledger, forecast, virtual receipt attribution and settlement options.
- [Three-slide treasury briefing](reports/treasury_briefing.pptx) covers the business problem, calculated findings and actions.
- [Model assumptions](docs/assumptions.md), [data dictionary](docs/data_dictionary.md) and [business case](docs/business_case.md) describe the calculations and controls.

```powershell
.\.venv\Scripts\python.exe -m src.reporting --database data/synthetic/treasury.sqlite
.\.venv\Scripts\python.exe -m src.product_proposal
.\.venv\Scripts\python.exe -m compileall -q app.py src tests
.\.venv\Scripts\python.exe -m pytest -q
```

Report generation writes the two sample filenames under `reports/`. Use `--output` to keep a separate snapshot. The suite covers reproducibility, SQLite constraints, settlement accounting, FX, transfers, forecast leakage, scenario shocks, Streamlit interactions and Office output contents.

## Reproduce the GPS deliverables

```powershell
.\.venv\Scripts\python.exe -m src.industry_research
.\.venv\Scripts\python.exe -m src.client_treasury_proposal
.\.venv\Scripts\python.exe -m src.commercial_opportunity
```

Use the three new pages with the default 29 July 2025 synthetic ledger date. The research cutoff is independent of the ledger date. In Client Solutions, change segments and download the current proposal. In Commercial Opportunity, change adoption and compare provider contribution against client savings. To capture screenshots, run the app locally, reset the controls to their defaults, and capture the main pane with the disclosure and units visible. Use only the sample data for portfolio screenshots.

## Architecture

```text
src/data_generation.py + src/database.py
    -> synthetic instructions, dated FX, receipts, transfers and scheduled flows
    -> src/payments.py + src/treasury.py
    -> src/forecasting.py + src/scenarios.py + src/recommendations.py
    -> app.py (Streamlit) + src/reporting.py (Excel and PowerPoint)
src/market_intelligence.py + src/product_strategy.py
    -> market and product dashboards + src/product_proposal.py
src/virtual_accounts.py + src/settlement.py + src/controls.py
    -> standalone product demonstrations using historical source data
src/industry_research.py + src/client_solutions.py + src/commercial_opportunity.py
    -> industry brief, client proposal and commercial case
    -> dedicated Streamlit pages with shared treasury calculations
```

The ledger stores integer cents and FX conversion uses Decimal with half-up cent rounding. Realized settlement and reporting translations use dated midpoints. The forecast starts from historical closing cash and uses only schedules known as of that close. Account buffers use local currency. The group rollup translates each position to USD before summation.

The model uses calendar days, simplified fee schedules and fixed forecast FX. It excludes unscheduled pending instructions, live market data, holidays, correspondent routing and bank cutoffs. Results illustrate a decision workflow and contain no client data or observed savings.

## 60-second interview walkthrough

> I built a synthetic treasury case for a company operating HKD, CNY and SGD accounts. I started with one problem: can the treasury team explain today's cash balance and identify a funding gap before it occurs? I modeled payment instructions and settlements separately, reconciled daily cash at account level and converted balances into USD using dated FX. Then I built a 30-day forecast from cash flows known on the reporting date. In the default stress case, receipt delays and higher costs reduce modeled day-30 group cash by about USD 442,000, and Singapore falls below its local operating buffer. I can trace that shortfall back to the daily movements and show the cash buffer result in Streamlit or Excel. I verified the accounting with manually checkable test cases.

## CV bullet options

- Built a Python, SQLite and Streamlit treasury analytics portfolio using 210 days of reproducible synthetic data across three APAC operating accounts.
- Implemented settlement-date cash reconciliation, multi-currency USD rollups, and a 30-day liquidity stress model for timing, expense and pricing shocks.
- Validated the financial engine and interactive dashboard with pytest and generated a nine-sheet Excel report and three-slide PowerPoint briefing from the same calculations.

MIT License.
