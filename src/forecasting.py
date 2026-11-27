from collections import defaultdict
from datetime import date, timedelta

from src.payments import charges, convert, rate_index
from src.scenarios import BASELINE
from src.treasury import daily_balances

HORIZON = 30


def forecast(data, as_of, scenario=BASELINE, *, forecast_rates=None):
    as_of = date.fromisoformat(str(as_of))
    first = as_of + timedelta(days=1)
    last = as_of + timedelta(days=HORIZON)
    accounts = {a["id"]: a for a in data["accounts"]}
    opening = {r["account"]: r["closing_minor"] for r in daily_balances(data, as_of)
               if r["day"] == str(as_of)}
    if opening.keys() != accounts.keys():
        raise ValueError("Forecast as-of date must have historical closing balances.")
    if scenario.expense_minor and scenario.expense_account not in accounts:
        raise ValueError("Expense account must exist.")
    rates = rate_index(data["fx"]) if forecast_rates is None else forecast_rates
    moves = defaultdict(lambda: dict(receipts_minor=0, suppliers_minor=0, fees_minor=0, fx_cost_minor=0, expense_minor=0))
    for row in data["scheduled"]:
        original_due = date.fromisoformat(row["due_on"])
        if row["known_on"] > str(as_of) or original_due <= as_of:
            continue
        receipt = row["kind"] == "receipt"
        delay = scenario.receipt_delay if receipt else scenario.supplier_delay
        shifted = original_due + timedelta(days=delay)
        if shifted > last:
            continue
        account = accounts[row["account"]]
        currency = account["currency"]
        amount = convert(row["amount_minor"], row["currency"], currency, as_of, rates)
        move = moves[shifted, row["account"]]
        if receipt:
            move["receipts_minor"] += amount
        else:
            foreign = row["currency"] != currency
            move["suppliers_minor"] += amount
            fees = charges(amount, foreign, foreign, scenario.fee_bps, scenario.spread_bps)
            move["fees_minor"] += sum(fees)
            move["fx_cost_minor"] += fees[2]
    if scenario.expense_minor:
        moves[as_of + timedelta(days=scenario.expense_day), scenario.expense_account]["expense_minor"] += scenario.expense_minor

    rows = []
    for offset in range(HORIZON):
        day = first + timedelta(days=offset)
        for key, account in accounts.items():
            move = moves[day, key]
            closing = opening[key] + move["receipts_minor"] - move["suppliers_minor"] - move["fees_minor"] - move["expense_minor"]
            buffer = account["buffer_minor"]
            rows.append(dict(day=str(day), account=key, currency=account["currency"],
                             opening_minor=opening[key], **move, closing_minor=closing,
                             closing_usd_minor=convert(closing, account["currency"], "USD", as_of, rates),
                             buffer_minor=buffer, shortfall_minor=max(0, buffer - closing), breach=closing < buffer))
            opening[key] = closing
    return rows


def compare(baseline, scenario):
    lookup = {(r["day"], r["account"]): r for r in baseline}
    rows = []
    for row in scenario:
        base = lookup[row["day"], row["account"]]
        rows.append(dict(row, baseline_minor=base["closing_minor"],
                         baseline_receipts_minor=base["receipts_minor"], baseline_suppliers_minor=base["suppliers_minor"],
                         baseline_fees_minor=base["fees_minor"],
                         delta_minor=row["closing_minor"] - base["closing_minor"],
                         delta_usd_minor=row["closing_usd_minor"] - base["closing_usd_minor"]))
    return rows
