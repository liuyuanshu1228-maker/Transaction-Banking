"""Illustrative client cost and separate provider economics, all in USD cents."""

import argparse
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path

from src.client_solutions import PROFILES, assess_client
from src.data_generation import AS_OF
from src.database import load
from src.payments import bps, rounded


@dataclass(frozen=True)
class Terms:
    fee_minor: int
    spread_bps: int
    reconciliation_minutes: int
    funding_days: int
    buffer_minor: int


@dataclass(frozen=True)
class Opportunity:
    monthly_volume: int
    ticket_minor: int
    fx_share_bps: int
    adoption_pct: int = 35
    prospects: int = 20
    labour_hour_minor: int = 3000
    cost_of_funds_bps: int = 400
    client_setup_minor: int = 50_000
    bank_implementation_minor: int = 2_500_000
    bank_service_month_minor: int = 7500
    bank_unit_cost_minor: int = 30


def default_case(metrics):
    count = metrics["count"]
    inputs = Opportunity(count, rounded(Decimal(metrics["volume_minor"]) / count) if count else 0,
                         round(metrics["fx_share"] * 10_000))
    buffer = metrics["buffer_minor"]
    return inputs, Terms(250, 45, 4, 5, buffer), Terms(175, 28, 2, 3, buffer)


def compare_economics(inputs, baseline, proposed):
    for record in (inputs, baseline, proposed):
        if any(type(value) is not int or value < 0 for value in vars(record).values()):
            raise ValueError("Use nonnegative integer counts, USD cents, days, minutes and basis points.")
    if inputs.adoption_pct > 100 or max(inputs.fx_share_bps, inputs.cost_of_funds_bps,
                                        baseline.spread_bps, proposed.spread_bps) > 10_000:
        raise ValueError("Adoption and share or rate inputs exceed their supported ranges.")
    annual_count = inputs.monthly_volume * 12
    principal = annual_count * inputs.ticket_minor
    fx_principal = bps(principal, inputs.fx_share_bps)

    def client(terms, setup):
        capital = rounded(Decimal(principal) * terms.funding_days / 365)
        return dict(processing=annual_count * terms.fee_minor, fx=bps(fx_principal, terms.spread_bps),
                    reconciliation=rounded(Decimal(annual_count) * terms.reconciliation_minutes
                                           * inputs.labour_hour_minor / 60),
                    carrying=bps(capital, inputs.cost_of_funds_bps), setup=setup,
                    working_capital=capital, buffer=terms.buffer_minor)

    original, alternative = client(baseline, 0), client(proposed, inputs.client_setup_minor)
    cost_keys = ("processing", "fx", "reconciliation", "carrying", "setup")
    savings = sum(original[k] - alternative[k] for k in cost_keys)
    adopted = Decimal(inputs.prospects) * inputs.adoption_pct / 100
    revenue = rounded(adopted * (alternative["processing"] + alternative["fx"]))
    operating = rounded(adopted * (annual_count * inputs.bank_unit_cost_minor
                                  + 12 * inputs.bank_service_month_minor))
    recurring = revenue - operating
    return dict(baseline=original, proposed=alternative, client_savings_minor=savings, adopted=adopted,
                provider_revenue_minor=revenue, provider_operating_minor=operating,
                provider_upfront_minor=inputs.bank_implementation_minor,
                year_one_contribution_minor=recurring - inputs.bank_implementation_minor,
                payback_months=Decimal(inputs.bank_implementation_minor) * 12 / recurring if recurring > 0 else None)


def adoption_cases(inputs, baseline, proposed):
    return [(pct, compare_economics(replace(inputs, adoption_pct=pct), baseline, proposed))
            for pct in sorted({0, 15, inputs.adoption_pct, 65, 100})]


def business_case(profile, as_of, inputs, terms, proposed, result):
    money = lambda value: f"USD {value/100:,.2f}"
    rows = [(label, money(result["baseline"][key]), money(result["proposed"][key]))
            for key, label in (("processing", "Processing expense"), ("fx", "FX conversion cost"),
                               ("reconciliation", "Reconciliation effort"), ("carrying", "Capital carrying cost"),
                               ("setup", "Client setup expense"), ("working_capital", "Working capital tied up"),
                               ("buffer", "Liquidity buffer memorandum"))]
    lines = ["# Commercial opportunity business case", "",
             f"Fictional client: {profile.name} · synthetic source date {as_of}.",
             f"Assumes {inputs.monthly_volume:,} monthly payments at an average {money(inputs.ticket_minor)} "
             f"and {inputs.fx_share_bps/100:g}% FX exposure.", "",
             f"Baseline versus proposed fee per payment: {money(terms.fee_minor)} to {money(proposed.fee_minor)}. "
             f"FX spreads: {terms.spread_bps} to {proposed.spread_bps} bp.", "",
             "| Client measure | Baseline | Proposed |", "| --- | ---: | ---: |"]
    lines += [f"| {label} | {base} | {plan} |" for label, base, plan in rows]
    payback = result["payback_months"]
    lines += ["", f"**First-year client savings:** {money(result['client_savings_minor'])} per modeled client.", "",
              f"**Provider economics:** {inputs.adoption_pct}% adoption across {inputs.prospects} prospects yields "
              f"{result['adopted']:g} expected adopters and {money(result['provider_revenue_minor'])} gross revenue. "
              f"Annual service and processing cost is {money(result['provider_operating_minor'])}. "
              f"After {money(result['provider_upfront_minor'])} rollout cost, first-year contribution totals "
              f"{money(result['year_one_contribution_minor'])}.",
              f"Simple provider payback: {f'{payback:.2f} months' if payback is not None else 'unavailable without positive recurring contribution'}.", "",
              "## Decision", "",
              "Validate corridor-specific fees, FX share, reconciliation effort and attainable adoption before committing "
              "rollout cost. Buffer values are shown separately from carrying costs. Figures are illustrative; the model "
              "excludes taxes, adoption ramp, funding restrictions and market execution risk."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export the default fictional commercial case.")
    parser.add_argument("--output", type=Path, default=Path("reports/commercial_opportunity.md"))
    args = parser.parse_args()
    client = PROFILES[0]
    inputs, baseline, proposed = default_case(assess_client(load(), client, AS_OF))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(business_case(client, AS_OF, inputs, baseline, proposed,
                                        compare_economics(inputs, baseline, proposed)), encoding="utf-8")
