from collections import defaultdict
from datetime import date, timedelta

from src.payments import convert, payment_rows, rate_index


def daily_balances(data, as_of):
    as_of = str(as_of)
    rates = rate_index(data["fx"])
    accounts = {row["id"]: row for row in data["accounts"]}
    movements = defaultdict(lambda: [0, 0, 0, 0, 0])
    for row in data["cashflows"]:
        if row["day"] <= as_of:
            movements[row["day"], row["account"]][0] += row["amount_minor"]
    for row in payment_rows(data, as_of):
        if row["status"] == "settled":
            move = movements[row["outcome_day"], row["account"]]
            move[1] += row["settled_minor"]
            move[2] += row["fee_minor"]
    for row in data["transfers"]:
        day, source, target = row["day"], row["source"], row["target"]
        if day <= as_of:
            amount = row["amount_minor"]
            target_amount = convert(amount, accounts[source]["currency"], accounts[target]["currency"], day, rates)
            movements[day, source][4] += amount
            movements[day, target][3] += target_amount

    closing = {key: row["opening_minor"] for key, row in accounts.items()}
    balances = []
    start = date.fromisoformat(min(row["day"] for row in data["fx"]))
    end = date.fromisoformat(as_of)
    for offset in range((end - start).days + 1):
        day = str(start + timedelta(days=offset))
        for key, account in accounts.items():
            opening = closing[key]
            received, paid, fees, incoming, outgoing = movements[day, key]
            closing[key] = opening + received - paid - fees + incoming - outgoing
            currency = account["currency"]
            balances.append(dict(day=day, account=key, region=account["region"], currency=currency,
                                 opening_minor=opening, inflow_minor=received, outflow_minor=paid, fees_minor=fees,
                                 transfer_in_minor=incoming, transfer_out_minor=outgoing, closing_minor=closing[key],
                                 buffer_minor=account["buffer_minor"], breach=closing[key] < account["buffer_minor"],
                                 closing_usd_minor=convert(closing[key], currency, "USD", day, rates),
                                 inflow_usd_minor=convert(received, currency, "USD", day, rates),
                                 outflow_usd_minor=convert(paid, currency, "USD", day, rates),
                                 fees_usd_minor=convert(fees, currency, "USD", day, rates)))
    return balances


def consolidate(rows):
    totals = defaultdict(int)
    for row in rows:
        totals[row["day"]] += row["closing_usd_minor"]
    return [dict(day=day, closing_usd_minor=amount) for day, amount in sorted(totals.items())]
