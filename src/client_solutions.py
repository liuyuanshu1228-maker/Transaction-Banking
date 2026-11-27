"""Derive fictional client advisory metrics from reproducible treasury records."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from src.database import load
from src.forecasting import forecast
from src.payments import convert, payment_metrics, payment_rows, rate_index
from src.scenarios import Scenario
from src.virtual_accounts import demo_receipts, reconciliation_summary


@dataclass(frozen=True)
class Profile:
    name: str
    industry: str
    accounts: tuple[str, ...]
    need: str


PROFILES = (
    Profile("Harbor Components", "Multinational importer/exporter", ("CN", "HK", "SG"),
            "Coordinate USD supplier payments, local cash buffers and industrial collections."),
    Profile("Jade Disbursements", "High-volume domestic payments", ("HK",),
            "Process domestic payouts and resolve payment exceptions."),
    Profile("Meridian Services", "Multi-currency regional operator", ("CN", "SG"),
            "Monitor regional liquidity and reconcile incoming customer receipts."),
)


def client_source(data, profile):
    if profile != PROFILES[1]:
        return data if profile == PROFILES[0] else load(seed=44)
    source = load(seed=43)
    instructions = []
    for payment in source["payments"]:
        if payment["account"] != "HK" or payment["currency"] != "HKD":
            continue
        principal, remainder = divmod(payment["principal_minor"], 20)
        for index in range(20):
            instructions.append(dict(payment, id=len(instructions) + 1,
                                     principal_minor=principal + (index < remainder)))
    return dict(source, payments=instructions,
                scheduled=[r for r in source["scheduled"] if r["account"] == "HK" and r["currency"] == "HKD"],
                transfers=[])


def assess_client(data, profile, as_of):
    as_of = date.fromisoformat(str(as_of))
    source = client_source(data, profile)
    window = str(as_of - timedelta(days=29))
    payments = [r for r in payment_rows(source, as_of)
                if r["account"] in profile.accounts and r["instructed"] >= window]
    measures = payment_metrics(payments)
    corridors = defaultdict(int)
    for row in payments:
        corridors[row["corridor"]] += row["instructed_usd_minor"]
    cross_currency = [r for r in payments if r["currency"] != r["account_currency"]]
    fx_volume = sum(r["instructed_usd_minor"] for r in cross_currency)
    projections = [r for r in forecast(source, as_of, Scenario(receipt_delay=5))
                   if r["account"] in profile.accounts]
    funding, buffers = defaultdict(int), 0
    rates = rate_index(source["fx"])
    for row in projections:
        funding[row["day"]] += convert(row["shortfall_minor"], row["currency"], "USD", as_of, rates)
        if row["day"] == projections[0]["day"]:
            buffers += convert(row["buffer_minor"], row["currency"], "USD", as_of, rates)
    collections = None
    if "SG" in profile.accounts:
        collections = reconciliation_summary(demo_receipts(source, as_of)[1])
    return dict(count=measures["count"], volume_minor=measures["volume_usd_minor"],
                fee_minor=measures["fees_usd_minor"], median_delay=measures["median_delay"],
                exceptions=sum(r["status"] != "settled" for r in payments),
                fx_volume_minor=fx_volume, fx_share=fx_volume / measures["volume_usd_minor"]
                if measures["volume_usd_minor"] else 0, corridors=dict(corridors),
                funding_path=dict(funding), peak_gap_minor=max(funding.values(), default=0),
                buffer_minor=buffers, collections=collections)


def solutions(profile, metrics):
    recommendations = []
    if metrics["peak_gap_minor"]:
        recommendations.append(dict(
            solution="Liquidity forecasting and cash concentration",
            evidence=f"Five-day receipt delay produces a peak gross buffer gap of USD {metrics['peak_gap_minor']/100:,.2f}.",
            benefit="Size a contingent funding discussion to the modeled gross gap.",
            assumptions="Local buffers are translated at static as-of FX.",
            dependencies="Confirm entity transfer permissions, balances and payment cutoffs.",
            risks="Liquidity may be trapped or arrive too late. The gap excludes inter-entity netting.",
        ))
    if metrics["fx_share"] >= .25:
        recommendations.append(dict(
            solution="Cross-border payments and FX risk management",
            evidence=f"{metrics['fx_share']:.1%} of instructed USD-equivalent value requires currency conversion.",
            benefit="Track USD funding needs and compare all-in FX costs by corridor.",
            assumptions="The prior 30 calendar days provide an exposure sample.",
            dependencies="Validate invoice currencies, corridor availability and treasury hedge policy.",
            risks="Quote changes and execution slippage can alter costs. No hedge pricing is modeled.",
        ))
    collections = metrics["collections"]
    if collections and collections["unique_receipts"] > collections["matched"]:
        recommendations.append(dict(
            solution="Collections and automated reconciliation",
            evidence=f"{collections['matched']} of {collections['unique_receipts']} unique receipts matched in the Singapore sample.",
            benefit="Test automatic payer attribution and route the remaining cases to review.",
            assumptions="Virtual references use a small synthetic receipt sample.",
            dependencies="Map payer identifiers and agree ownership of missing and duplicate references.",
            risks="An attributed payment may still need invoice-level validation.",
        ))
    if metrics["exceptions"] or not recommendations:
        recommendations.append(dict(
            solution="Payment controls and exception reporting",
            evidence=f"{metrics['exceptions']} failed or pending instructions across {metrics['count']} in the window.",
            benefit="Direct operations staff to aged or failed items before adding new routing.",
            assumptions="Payment status is measured at the selected ledger cutoff.",
            dependencies="Agree status mappings, ownership and escalation standards.",
            risks="Synthetic status codes provide no root-cause or live service evidence.",
        ))
    if profile == PROFILES[0] and metrics["fx_volume_minor"]:
        recommendations.append(dict(
            solution="Trade and supply-chain finance discovery",
            evidence="Importer/exporter profile with USD supplier exposure.",
            benefit="Assess whether eligible invoices and supplier terms justify a separate financing review.",
            assumptions="Invoice tenor and credit exposure are outside the input data.",
            dependencies="Obtain invoice, acceptance, tenor and counterparty evidence.",
            risks="This discovery step provides no financing amount or eligibility decision.",
        ))
    return recommendations
