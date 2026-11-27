"""Illustrative settlement comparison for one outgoing instruction."""

from src.payments import bps, convert, rate_index
from src.treasury import daily_balances

# Method, calendar minutes, SGD fixed fee in cents, and cross-currency spread in bp.
METHODS = (("Hypothetical real-time", 1, 100, 20), ("Hypothetical conventional", 2880, 600, 35))


def compare_settlement(data, as_of, amount_minor, currency, *, balances=None):
    if type(amount_minor) is not int or amount_minor <= 0 or currency not in {"SGD", "USD"}:
        raise ValueError("Provide a positive integer-cent amount in SGD or USD.")
    balances = daily_balances(data, as_of) if balances is None else balances
    account = next((row for row in balances if row["day"] == str(as_of) and row["account"] == "SG"), None)
    if account is None:
        raise ValueError("A Singapore opening position is required at the reporting date.")
    rate = rate_index(data["fx"])
    principal = convert(amount_minor, currency, "SGD", as_of, rate)
    opening = account["closing_minor"]
    buffer = account["buffer_minor"]
    ticks = [0, *(delay for _, delay, _, _ in METHODS)]
    rows = []
    for method, delay, fixed, spread_bps in METHODS:
        applied_bps = spread_bps if currency != "SGD" else 0
        spread = bps(principal, applied_bps)
        ending = opening - principal - fixed - spread
        rows.append(dict(method=method, delay_min=delay, principal_minor=principal, fee_minor=fixed,
                         spread_bps=applied_bps, spread_minor=spread, opening_minor=opening,
                         ending_minor=ending, shortfall_minor=max(0, buffer - ending),
                         timeline=[dict(minute=tick, balance_minor=opening if tick < delay else ending)
                                   for tick in ticks]))
    return rows
