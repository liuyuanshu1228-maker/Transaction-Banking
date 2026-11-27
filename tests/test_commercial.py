from dataclasses import replace
from decimal import Decimal

import pytest

from src.commercial_opportunity import Opportunity, Terms, compare_economics


def test_pricing_conversion_and_accounting():
    inputs = Opportunity(10, 100_000, 5000, adoption_pct=50, prospects=4, labour_hour_minor=6000,
                         client_setup_minor=100, bank_implementation_minor=1800, bank_service_month_minor=100,
                         bank_unit_cost_minor=10, cost_of_funds_bps=0)
    baseline, proposed = Terms(200, 100, 3, 2, 500), Terms(100, 50, 1, 1, 400)
    row = compare_economics(inputs, baseline, proposed)
    assert row["baseline"]["fx"] == 60_000 and row["proposed"]["fx"] == 30_000
    assert row["client_savings_minor"] == 65_900
    assert row["provider_revenue_minor"] == 84_000 and row["provider_operating_minor"] == 4800
    assert row["year_one_contribution_minor"] == 77_400
    assert row["payback_months"] == Decimal(1800 * 12) / 79_200
    assert row["baseline"]["working_capital"] > row["proposed"]["working_capital"]
    assert row["proposed"]["buffer"] == 400


def test_zero_adoption_or_volume_and_negative_inputs():
    inputs, terms = Opportunity(1, 100, 0, adoption_pct=0), Terms(100, 50, 0, 0, 0)
    row = compare_economics(inputs, terms, terms)
    assert row["provider_revenue_minor"] == 0 and row["payback_months"] is None
    assert row["year_one_contribution_minor"] == -inputs.bank_implementation_minor
    zero_volume = compare_economics(replace(inputs, monthly_volume=0, adoption_pct=100), terms, terms)
    assert zero_volume["provider_revenue_minor"] == 0 and zero_volume["payback_months"] is None
    assert zero_volume["provider_operating_minor"] > 0
    for invalid in [replace(inputs, monthly_volume=-1), replace(inputs, adoption_pct=105)]:
        with pytest.raises(ValueError):
            compare_economics(invalid, terms, terms)
