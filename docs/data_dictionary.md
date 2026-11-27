# Data dictionary

All dates use ISO 8601 calendar days. Monetary fields ending in minor store integer cents in the stated currency. FX rates store USD per unit of local currency multiplied by one million.

| Table | Grain | Purpose |
| --- | --- | --- |
| accounts | Account ID | Booking region, currency, opening balance and minimum buffer |
| fx | Date and currency | Dated synthetic mid-market conversion to USD |
| payments | Instruction ID | Booking account, instruction amount and currency, destination, outcome and outcome date |
| cashflows | Receipt ID | Historical external cash receipts in account currency |
| scheduled | Schedule ID | Due date, first known date, cash flow type, currency and amount |
| transfers | Transfer ID | Same-day movement between two accounts, principal in source currency |
