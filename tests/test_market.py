from copy import deepcopy

import pytest

from src.data_generation import AS_OF
from src.database import load
from src.market_intelligence import PAYMENTS, published_observations, sensitivity


def test_publication_cutoff_respects_release_lag_and_annual_reports():
    before = published_observations("2025-07-25")
    assert not any(row["observed_on"] == "2025-07-25" for row in before)
    after = published_observations("2025-07-28")
    assert sum(row["observed_on"] == "2025-07-25" for row in after) == 3
    assert [r["observed_on"] for r in after if r["series"] == PAYMENTS] == ["2024"]
    assert len([r for r in published_observations("2026-11-16") if r["series"] == PAYMENTS]) == 3


def test_zero_is_neutral_and_interest_uses_act_365():
    data = load()
    original = deepcopy(data)
    baseline, neutral, interest = sensitivity(data, AS_OF, {"CNY": 0}, 0)
    assert baseline == neutral and interest == 0
    _, shocked, interest = sensitivity(data, AS_OF, {}, 100)
    assert interest == -41096
    assert shocked["day30_cash_minor"] - baseline["day30_cash_minor"] == interest
    assert data == original


def test_stronger_usd_stresses_open_positions_and_funding():
    baseline, shocked, _ = sensitivity(load(), AS_OF, {"CNY": 1000, "HKD": 1000, "SGD": 1000}, 0, receipt_delay=5)
    assert shocked["day30_cash_minor"] < baseline["day30_cash_minor"]
    assert shocked["peak_funding_minor"] > baseline["peak_funding_minor"]


def test_quote_direction_and_spread_cost_use_local_principal():
    data = dict(accounts=[dict(id="SG", region="Singapore", currency="SGD", opening_minor=100000, buffer_minor=90000)],
                fx=[dict(day="2025-01-01", currency="SGD", usd_ppm=500000),
                    dict(day="2025-01-01", currency="USD", usd_ppm=1000000)],
                payments=[], transfers=[], cashflows=[], scheduled=[
                    dict(account="SG", known_on="2025-01-01", due_on="2025-01-02",
                         kind="supplier", currency="USD", amount_minor=10000)])
    base, stress, _ = sensitivity(data, "2025-01-01", {"SGD": 1000}, 0)
    assert base == dict(day30_cash_minor=39057, peak_funding_minor=5943, fx_cost_minor=35)
    assert stress == dict(day30_cash_minor=34593, peak_funding_minor=6316, fx_cost_minor=35)


@pytest.mark.parametrize("shift", [{"GBP": 50}, {"SGD": -10000}, {"CNY": 1.5}])
def test_invalid_quote_shock(shift):
    with pytest.raises(ValueError):
        sensitivity(load(), AS_OF, shift, 0)
