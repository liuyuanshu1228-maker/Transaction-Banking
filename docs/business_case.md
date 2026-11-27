# Corporate treasury business case

A fictional multinational operates accounts in Hong Kong, Shanghai and Singapore. Treasury needs an auditable operating cash view, payment operations needs an exception queue, and finance needs to know when a scheduled cash shortfall requires escalation.

| Decision | Evidence | Potential action |
| --- | --- | --- |
| Can each account meet operating buffers? | Account-day balances, known upcoming payments and minimum cash gaps | Confirm receivables and prepare contingent funding for the affected account |
| Where are payment exceptions concentrated? | Corridor, instruction age and observed status | Triage aged pending records and investigate failed instructions |
| Which costs warrant review? | Fixed fee, variable fee and FX spread on settled principal | Compare corridor-level all-in prices and evaluate eligible payment batching |

The default conservative case shows 21 breached account-days and a peak SGD 136,034.46 shortfall. A treasury analyst would confirm incoming cash and test a funding amount against the specific local gap. Group USD cash alone cannot answer whether funds can be moved to the affected entity in time.

For a live rollout, the analyst would reconcile to bank statements, validate payment-status mappings, obtain current commercial terms, confirm entity-level constraints and calibrate the forecast on approved historical schedules. The current project is an independent educational simulation.
