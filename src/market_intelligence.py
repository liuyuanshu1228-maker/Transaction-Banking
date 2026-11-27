from collections import defaultdict
from csv import DictReader
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.forecasting import HORIZON, forecast
from src.payments import convert, rate_index, rounded
from src.scenarios import BASELINE, Scenario

SNAPSHOT = date(2026, 11, 16)
FX_CURRENCIES = ("CNY", "HKD", "SGD")
POLICY = "Fed target midpoint"
PAYMENTS = "Wholesale credits within one business day"
FX_UNITS = {f"USD/{currency}": f"{currency} per USD" for currency in FX_CURRENCIES}
UNITS = {POLICY: "Percent per year", PAYMENTS: "Percent of measured payments", **FX_UNITS}
OBSERVATIONS = Path(__file__).resolve().parents[1] / "data/market/observations.csv"


def published_observations(cutoff, path=OBSERVATIONS):
    cutoff = date.fromisoformat(str(cutoff))
    rows = []
    seen = set()
    with Path(path).open(newline="", encoding="utf-8") as source:
        for row in DictReader(source):
            series = row["series"]
            value = Decimal(row["value"])
            published = date.fromisoformat(row["published_on"])
            period = row["observed_on"]
            observed = date(int(period), 1, 1) if series == PAYMENTS else date.fromisoformat(period)
            key = (series, period)
            if (key in seen or UNITS.get(series) != row["unit"] or not value.is_finite()
                or value <= 0 or observed > published or not row["source_url"].startswith("https://")):
                raise ValueError(f"Invalid or duplicate market observation {key}")
            seen.add(key)
            if published <= cutoff:
                rows.append(dict(row, value=value))
    return sorted(rows, key=lambda row: (row["series"], row["observed_on"]))


def observations_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["series"]].append(row)
    summary = []
    for series in (POLICY, *FX_UNITS, PAYMENTS):
        points = groups[series]
        if len(points) < 2:
            continue
        first, last = points[0], points[-1]
        move = last["value"] - first["value"]
        if series in FX_UNITS:
            change = f"{move / first['value']:+.2%}"
            implication = "A higher quote raises the local-currency cost of a fixed USD payable."
        else:
            change = f"{move:+.2f} percentage points"
            implication = ("Reprice floating-rate funding and cash yield separately."
                           if series == POLICY else "Compare end-to-end credit timing by corridor.")
        summary.append((series, f"{first['observed_on']} to {last['observed_on']}: "
                        f"{first['value']} to {last['value']} {last['unit'].lower()} ({change}). {implication}",
                        first["source_url"], last["source_url"]))
    return summary


def sensitivity(data, as_of, fx_bps, rate_bps, *, receipt_delay=0, spread_shock_bps=0,
                debt_minor=100_000_000, savings_minor=50_000_000):
    """Use synthetic forecast flows and reprice distinct USD debt and cash notionals."""
    as_of = str(date.fromisoformat(str(as_of)))
    if set(fx_bps) - set(FX_CURRENCIES) or any(type(v) is not int or not -9999 <= v <= 10_000
                                               for v in fx_bps.values()):
        raise ValueError("Use supported FX quotes and integer shocks greater than -10,000 bp.")
    if type(rate_bps) is not int or any(type(v) is not int or v < 0 for v in (debt_minor, savings_minor)):
        raise ValueError("Use integer basis points and nonnegative integer USD cent notionals.")
    if type(receipt_delay) is not int or not 0 <= receipt_delay <= HORIZON:
        raise ValueError("Receipt delay must be 0 to 30 calendar days.")
    if type(spread_shock_bps) is not int or not 0 <= spread_shock_bps <= 1000:
        raise ValueError("Additional FX spread must be 0 to 1,000 basis points.")
    base_rates = rate_index(data["fx"])
    stressed = dict(base_rates)
    for currency, shift in fx_bps.items():
        key = (as_of, currency)
        # Public quotes use local units per USD. The ledger stores the reciprocal in ppm.
        stressed[key] = Decimal(base_rates[key]) * 10_000 / (10_000 + shift)

    def measure(rates, case):
        projected = forecast(data, as_of, case, forecast_rates=rates)
        daily_gaps = defaultdict(int)
        fx_cost = 0
        for row in projected:
            currency = row["currency"]
            daily_gaps[row["day"]] += convert(row["shortfall_minor"], currency, "USD", as_of, rates)
            fx_cost += convert(row["fx_cost_minor"], currency, "USD", as_of, rates)
        last = projected[-1]["day"]
        return dict(day30_cash_minor=sum(r["closing_usd_minor"] for r in projected if r["day"] == last),
                    peak_funding_minor=max(daily_gaps.values()), fx_cost_minor=fx_cost)

    baseline = measure(base_rates, BASELINE)
    scenario = measure(stressed, Scenario(receipt_delay=receipt_delay, spread_bps=spread_shock_bps))
    incremental = rounded(Decimal(savings_minor - debt_minor) * rate_bps * HORIZON / 3_650_000)
    scenario["day30_cash_minor"] += incremental
    return baseline, scenario, incremental
