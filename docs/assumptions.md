# Financial assumptions

## Cash and FX

- Each account has one operating currency, an opening balance before the first historical day and a fixed local minimum buffer. Singapore's synthetic receipt scale and buffer make an account-specific stress gap observable in the default snapshot.
- All monetary calculations book integer cents. FX rates are USD per major unit of the quoted currency in millionths. To convert A to B, multiply by the USD rate for A and divide by the USD rate for B. Round half up to the target cent.
- Daily cash equals opening cash plus external receipts and transfer credits, less settled principal, settled charges and transfer debits. The next opening equals the preceding close.
- Transfers debit the source and credit the target on the same day using that day's midpoint. Transfers are excluded from external flows. Rounded target and USD cents can cause small translation residuals. FX movements also affect USD cash across dates even when local cash is unchanged.

## Payments

- Reporting cohorts use instruction dates. Status is observed at the as-of date. A later outcome remains pending in earlier views.
- Only settled instructions debit cash. Domestic instructions incur 3 units of account currency. Cross-border instructions incur 18 units plus 8 bp of account-currency principal. Cross-currency instructions incur a further 35 bp indicative spread. Charges post on the settlement date.
- Instructed volume uses instruction-date FX. Settled principal and costs use settlement-date FX. The portfolio cost metric sums translated fee components, so per-item and aggregate rounding may differ by cents.
- Settlement delay is elapsed calendar days for settled instructions. The default data includes synthetic failures and pending instructions with no booked fees or refund assumptions.

## Forecast and stress

- The 30-day forecast starts the next day after the reporting close and uses only scheduled rows known at that close with a future original due date. Unscheduled pending items have no assumed settlement date. Schedules are concentrated near the end of the historical sample.
- The model holds as-of FX fixed throughout the forecast. It adds receipts, subtracts suppliers and their fees, and books a one-time expense in the chosen account on the scenario day. Forecast USD supplier invoices use the foreign-payment fee schedule.
- Scenario delays move dates by calendar days. Shifted amounts beyond day 30 fall outside the displayed forecast window. Positive fees apply additional basis points to supplier principal and a spread shock applies only to cross-currency suppliers.
- The conservative case delays receipts by five days, adds an SGD 15,000 expense on day seven, adds 10 bp of variable fees and raises FX spread by 25 bp.
- A breach occurs when closing cash is strictly below its local buffer. A shortfall is the local buffer less closing cash when breached. Group surplus can coexist with an account shortfall.

Market pricing, payment routing, taxes, transfer eligibility, holidays, operational cutoffs and approvals are outside the simulation.
