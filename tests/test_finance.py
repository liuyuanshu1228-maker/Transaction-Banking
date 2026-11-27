from src.data_generation import AS_OF
from src.database import load
from src.payments import charges, convert, payment_rows
from src.treasury import consolidate, daily_balances


def test_fx_direction_and_half_up():
    rates = {("2025-01-01", "USD"): 1_000_000, ("2025-01-01", "HKD"): 125_000}
    assert convert(100, "USD", "HKD", "2025-01-01", rates) == 800
    assert convert(12, "HKD", "USD", "2025-01-01", rates) == 2


def test_fee_components():
    assert charges(100_000, True, True) == (1800, 80, 350)
    assert charges(100_000, False, False) == (300, 0, 0)


def test_nonsettled_has_zero_debits():
    rows = payment_rows(load(), AS_OF)
    assert {r["status"] for r in rows} == {"settled", "failed", "pending"}
    assert all(r["settled_minor"] == r["fee_minor"] == 0 for r in rows if r["status"] != "settled")


def test_all_days_reconcile():
    last = {}
    for r in daily_balances(load(), AS_OF):
        account = r["account"]
        assert r["opening_minor"] == last.get(account, r["opening_minor"])
        assert r["closing_minor"] == (r["opening_minor"] + r["inflow_minor"] - r["outflow_minor"]
                                      - r["fees_minor"] + r["transfer_in_minor"] - r["transfer_out_minor"])
        last[account] = r["closing_minor"]


def test_consolidation_uses_usd():
    assert consolidate([dict(day="d", closing_minor=800, closing_usd_minor=100),
                        dict(day="d", closing_minor=200, closing_usd_minor=150)]) == [
                            dict(day="d", closing_usd_minor=250)]
