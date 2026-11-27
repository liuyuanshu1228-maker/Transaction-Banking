"""First-year economics for separately evaluated fictional service offers."""

from dataclasses import dataclass
from decimal import Decimal

from src.payments import bps, rounded


@dataclass(frozen=True)
class Segment:
    name: str
    industry: str
    currency_exposure: str
    need: str
    addressable_clients: int
    monthly_payments: int
    monthly_receipts: int
    foreign_share_bps: int
    average_ticket_minor: int
    manual_receipt_bps: int
    idle_cash_minor: int


SEGMENTS = (
    Segment("Harbor Components", "Industrial exporter", "CNY / USD", "USD supplier costs and settlement predictability",
            25, 3200, 350, 6500, 260000, 900, 30_000_000),
    Segment("Pearl Commerce", "Marketplace", "CNY / HKD / USD", "High-volume receipts and manual payer identification",
            40, 2400, 12000, 1900, 6000, 3200, 22_000_000),
    Segment("Strait Logistics", "Regional logistics", "SGD / CNY / USD", "Idle cash across operating accounts",
            30, 760, 650, 3700, 110000, 1100, 250_000_000),
)


@dataclass(frozen=True)
class Offer:
    name: str
    value_proposition: str
    monthly_fee_minor: int
    unit_fee_minor: int
    monthly_service_minor: int
    unit_cost_minor: int
    onboarding_minor: int
    platform_minor: int


OFFERS = (
    Offer("Cross-border payments", "Consolidate payment instructions and compare all-in FX execution costs.",
          35_000, 25, 12_000, 10, 45_000, 2_400_000),
    Offer("Virtual account collections", "Give payers identifiable references and route exceptions to review.",
          45_000, 6, 18_000, 2, 60_000, 3_000_000),
    Offer("Liquidity visibility", "Surface idle cash and review operating buffers before reallocating cash.",
          70_000, 0, 27_000, 0, 90_000, 2_000_000),
)
PILOT_SEGMENT = SEGMENTS[1]
BASE_ADOPTION_PCT = 35
SCENARIOS = (("Downside", 10, 80, 120), ("Base", BASE_ADOPTION_PCT, 100, 100), ("Upside", 55, 120, 90))
FX_SAVINGS_BPS = 25
MANUAL_CASE_REDUCTION_BPS = 7000
MANUAL_CASE_COST_MINOR = 300
CASH_RELEASE_BPS = 2000
ANNUAL_OPPORTUNITY_BPS = 300


def evaluate(segment, offer, *, adoption_pct=BASE_ADOPTION_PCT, volume_pct=100, cost_pct=100):
    if any(type(v) is not int or not 0 <= v <= limit
           for v, limit in ((adoption_pct, 100), (volume_pct, 200), (cost_pct, 200))):
        raise ValueError("Adoption must be 0–100%; volume and service-cost factors must be 0–200%.")
    inputs = (segment.addressable_clients, segment.monthly_payments, segment.monthly_receipts,
              segment.average_ticket_minor, segment.idle_cash_minor)
    if any(type(v) is not int or v < 0 for v in inputs) or any(
        type(v) is not int or not 0 <= v <= 10_000
        for v in (segment.foreign_share_bps, segment.manual_receipt_bps)
    ):
        raise ValueError("Segment inputs require nonnegative counts and USD cents, and shares in 0–10,000 bp.")
    payments = rounded(Decimal(segment.monthly_payments) * volume_pct / 100)
    receipts = rounded(Decimal(segment.monthly_receipts) * volume_pct / 100)
    if offer == OFFERS[0]:
        units = payments
        gross = bps(bps(payments * 12 * segment.average_ticket_minor, segment.foreign_share_bps), FX_SAVINGS_BPS)
        fit = segment.foreign_share_bps >= 4000 and payments >= 500
        rule = "At least 500 monthly payments and 40% foreign-currency payment share."
    elif offer == OFFERS[1]:
        units = receipts
        manual_cases = Decimal(receipts) * 12 * segment.manual_receipt_bps / 10_000
        gross = bps(manual_cases * MANUAL_CASE_COST_MINOR, MANUAL_CASE_REDUCTION_BPS)
        fit = receipts >= 1000 and segment.manual_receipt_bps >= 2000
        rule = "At least 1,000 monthly receipts and 20% manual attribution."
    elif offer == OFFERS[2]:
        units = 0
        gross = bps(bps(segment.idle_cash_minor, CASH_RELEASE_BPS), ANNUAL_OPPORTUNITY_BPS)
        fit = segment.idle_cash_minor >= 50_000_000
        rule = "At least USD 500,000 in average potentially idle cash."
    else:
        raise ValueError("Unknown catalogue offer.")

    annual_fee = 12 * (offer.monthly_fee_minor + units * offer.unit_fee_minor)
    annual_cost = rounded(Decimal(12 * (offer.monthly_service_minor + units * offer.unit_cost_minor)
                                  + offer.onboarding_minor) * cost_pct / 100)
    adopted = Decimal(segment.addressable_clients) * adoption_pct / 100
    revenue = rounded(annual_fee * adopted)
    cost = rounded(annual_cost * adopted) + offer.platform_minor
    return dict(offer=offer.name, fit=fit, fit_rule=rule, gross_client_value_minor=gross,
                net_client_value_minor=gross - annual_fee, per_client_fee_minor=annual_fee,
                per_client_cost_minor=annual_cost, adopted_clients=adopted,
                cohort_revenue_minor=revenue, cohort_cost_minor=cost, cohort_contribution_minor=revenue - cost)


def recommend(rows):
    viable = [row for row in rows if row["fit"] and row["net_client_value_minor"] > 0
              and row["per_client_fee_minor"] > row["per_client_cost_minor"]]
    return max(viable, key=lambda row: row["net_client_value_minor"], default=None)


def format_usd(minor):
    return f"USD {minor / 100:,.2f}"
