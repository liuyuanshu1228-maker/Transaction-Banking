from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from statistics import median

FX_SPREAD_BPS = 35
WIRE_FEE_BPS = 8
WIRE_FIXED_MINOR = 1800
DOMESTIC_FIXED_MINOR = 300


def rounded(value):
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def bps(amount, rate):
    return rounded(Decimal(amount) * rate / 10_000)


def rate_index(rows):
    return {(row["day"], row["currency"]): row["usd_ppm"] for row in rows}


def convert(amount, source, target, day, rates):
    if source == target:
        return amount
    return rounded(Decimal(amount) * rates[(str(day), source)] / rates[(str(day), target)])


def charges(principal, cross_border, cross_currency, fee_shock_bps=0, spread_shock_bps=0):
    fixed = WIRE_FIXED_MINOR if cross_border else DOMESTIC_FIXED_MINOR
    variable = bps(principal, (WIRE_FEE_BPS if cross_border else 0) + fee_shock_bps)
    spread = bps(principal, FX_SPREAD_BPS + spread_shock_bps) if cross_currency else 0
    return fixed, variable, spread


def payment_rows(data, as_of):
    as_of = str(as_of)
    accounts = {a["id"]: a for a in data["accounts"]}
    rates = rate_index(data["fx"])
    result = []
    for row in data["payments"]:
        if row["instructed"] > as_of:
            continue
        account = accounts[row["account"]]
        outcome = row["outcome_day"]
        observed = outcome is not None and outcome <= as_of
        status = row["status"] if observed else "pending"
        cross_border = account["region"] != row["destination"]
        currency = account["currency"]
        convert_day = outcome if status == "settled" else row["instructed"]
        principal = convert(row["principal_minor"], row["currency"], currency, convert_day, rates)
        fixed, variable, spread = charges(principal, cross_border, row["currency"] != currency)
        if status != "settled":
            fixed = variable = spread = 0
        settled = principal if status == "settled" else 0
        result.append(dict(row, status=status, outcome_day=outcome if observed else None,
                           corridor=f"{account['region']} → {row['destination']}", cross_border=cross_border,
                           account_currency=currency, settled_minor=settled, fixed_minor=fixed,
                           variable_minor=variable, spread_minor=spread, fee_minor=fixed + variable + spread,
                           instructed_usd_minor=convert(row["principal_minor"], row["currency"], "USD",
                                                         row["instructed"], rates),
                           settled_usd_minor=convert(settled, currency, "USD", convert_day, rates),
                           fixed_usd_minor=convert(fixed, currency, "USD", convert_day, rates),
                           variable_usd_minor=convert(variable, currency, "USD", convert_day, rates),
                           spread_usd_minor=convert(spread, currency, "USD", convert_day, rates),
                           delay_days=(date.fromisoformat(outcome) - date.fromisoformat(row["instructed"])).days
                           if status == "settled" else None))
    return result


def payment_metrics(rows):
    counts = {status: sum(r["status"] == status for r in rows) for status in ("settled", "failed", "pending")}
    total = len(rows)
    delays = [row["delay_days"] for row in rows if row["delay_days"] is not None]
    components = {key: sum(row[key] for row in rows) for key in
                  ("fixed_usd_minor", "variable_usd_minor", "spread_usd_minor")}
    return dict(count=total, **{f"{s}_rate": n / total if total else 0 for s, n in counts.items()},
                volume_usd_minor=sum(r["instructed_usd_minor"] for r in rows),
                settled_usd_minor=sum(r["settled_usd_minor"] for r in rows),
                fees_usd_minor=sum(components.values()), **components,
                median_delay=median(delays) if delays else None)
