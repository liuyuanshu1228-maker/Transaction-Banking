import sqlite3

import pytest

from src.data_generation import AS_OF
from src.database import create_database, load
from src.forecasting import forecast
from src.payments import convert, payment_metrics, payment_rows
from src.recommendations import recommendations
from src.scenarios import CONSERVATIVE, Scenario
from src.treasury import consolidate, daily_balances


@pytest.fixture
def toy():
    return dict(
        accounts=[dict(id="HK", region="Hong Kong", currency="HKD", opening_minor=80_000, buffer_minor=40_000),
                  dict(id="US", region="United States", currency="USD", opening_minor=10_000, buffer_minor=0)],
        fx=[dict(day=day, currency=currency, usd_ppm=rate)
            for day in ("2025-01-01", "2025-01-02")
            for currency, rate in (("USD", 1_000_000), ("HKD", 125_000))],
        cashflows=[], transfers=[], payments=[], scheduled=[],
    )


def test_internal_transfer_conserves_group_cash(toy):
    toy["transfers"].append(dict(day="2025-01-02", source="HK", target="US", amount_minor=8_000))
    rows = daily_balances(toy, "2025-01-02")
    assert [r["closing_minor"] for r in rows[-2:]] == [72_000, 11_000]
    assert [r["closing_usd_minor"] for r in consolidate(rows)] == [20_000, 20_000]
    assert sum(r["inflow_minor"] + r["outflow_minor"] for r in rows) == 0


def test_payment_outcome_visible_only_after_settlement(toy):
    toy["payments"].append(dict(id=1, instructed="2025-01-01", outcome_day="2025-01-02", account="HK",
                                destination="United States", currency="USD", principal_minor=5_000,
                                status="settled"))
    early = payment_rows(toy, "2025-01-01")[0]
    assert (early["status"], early["outcome_day"], early["settled_minor"]) == ("pending", None, 0)
    rows = daily_balances(toy, "2025-01-02")
    assert rows[0]["closing_minor"] == 80_000
    assert rows[2]["closing_minor"] == 38_028


def test_delays_and_fee_shocks_are_traceable(toy):
    toy["scheduled"] = [
        dict(account="HK", known_on="2025-01-01", due_on="2025-01-03", kind="receipt",
             currency="HKD", amount_minor=10_000),
        dict(account="HK", known_on="2025-01-02", due_on="2025-01-03", kind="supplier",
             currency="USD", amount_minor=5_000),
    ]
    base = forecast(toy, "2025-01-02")
    assert base[0]["closing_minor"] == 48_028
    rows = forecast(toy, "2025-01-02", Scenario(receipt_delay=2, supplier_delay=1, fee_bps=10, spread_bps=25))
    hk = [row for row in rows if row["account"] == "HK"]
    assert [r["receipts_minor"] for r in hk[:3]] == [0, 0, 10_000]
    assert [r["suppliers_minor"] for r in hk[:3]] == [0, 40_000, 0]
    assert [r["fees_minor"] for r in hk[:3]] == [0, 2_112, 0]
    assert hk[1]["shortfall_minor"] == 2_112
    assert hk[2]["closing_minor"] == 47_888


def test_horizon_truncates_shifted_supplier(toy):
    toy["scheduled"] = [dict(account="HK", known_on="2025-01-02", due_on="2025-02-01",
                             kind="supplier", currency="HKD", amount_minor=1000)]
    assert forecast(toy, "2025-01-02")[-2]["suppliers_minor"] == 1000
    assert forecast(toy, "2025-01-02", Scenario(supplier_delay=1))[-2]["suppliers_minor"] == 0


def test_missing_fx_raises():
    with pytest.raises(KeyError):
        convert(100, "HKD", "USD", "2025-01-01", {})


def test_empty_instruction_selection():
    metrics = payment_metrics([])
    assert metrics["count"] == metrics["volume_usd_minor"] == metrics["fees_usd_minor"] == 0
    assert metrics["median_delay"] is None


def test_negative_shock_rejected():
    with pytest.raises(ValueError):
        Scenario(receipt_delay=-1)


def test_default_stress_triggers_evidence_based_action():
    data = load()
    base = forecast(data, AS_OF)
    stress = forecast(data, AS_OF, CONSERVATIVE)
    assert not any(row["breach"] for row in base)
    assert any(row["breach"] for row in stress)
    assert stress == forecast(data, AS_OF, CONSERVATIVE)
    rec = recommendations(payment_rows(data, AS_OF), stress)[0]
    assert "SG" in rec["evidence"] and "funding" in rec["action"]


def test_materialized_sqlite_daily_balances(tmp_path):
    path = create_database(tmp_path / "portfolio.sqlite")
    expected = daily_balances(load(path), AS_OF)
    with sqlite3.connect(path) as connection:
        actual = connection.execute("SELECT day, account, closing_minor FROM daily_balances ORDER BY day, account")
        assert actual.fetchall() == [(r["day"], r["account"], r["closing_minor"]) for r in expected]
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
