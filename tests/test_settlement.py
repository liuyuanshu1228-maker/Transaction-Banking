from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.data_generation import AS_OF
from src.database import load
from src.settlement import compare_settlement
from src.treasury import daily_balances


def test_cash_timing_fees_and_shortfall_hand_calculation():
    balances = [dict(day="2025-01-01", account="SG", closing_minor=20_000, buffer_minor=10_000)]
    real_time, conventional = compare_settlement({"fx": []}, "2025-01-01", 10_000, "SGD", balances=balances)
    assert [r["balance_minor"] for r in real_time["timeline"]] == [20_000, 9_900, 9_900]
    assert [r["balance_minor"] for r in conventional["timeline"]] == [20_000, 20_000, 9_400]
    assert (real_time["shortfall_minor"], conventional["shortfall_minor"]) == (100, 600)
    assert real_time["spread_bps"] == conventional["spread_bps"] == 0


def test_fx_spread_uses_same_as_of_principal_and_no_ledger_mutation():
    data = load()
    before = daily_balances(data, AS_OF)
    real_time, conventional = compare_settlement(data, AS_OF, 100_000, "USD")
    assert real_time["principal_minor"] == conventional["principal_minor"] > 100_000
    for row in (real_time, conventional):
        assert row["ending_minor"] + row["principal_minor"] + row["fee_minor"] + row["spread_minor"] == row["opening_minor"]
    assert conventional["spread_minor"] > real_time["spread_minor"] > 0
    assert daily_balances(data, AS_OF) == before


@pytest.mark.parametrize("amount,currency", [(0, "SGD"), (100, "GBP"), (1.5, "USD")])
def test_invalid_instructions(amount, currency):
    with pytest.raises(ValueError, match="positive integer-cent"):
        compare_settlement(load(), AS_OF, amount, currency)


def test_settlement_comparison_app_control():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    app.radio[0].set_value("Payment Analytics").run()
    assert not app.exception
    assert app.dataframe[2].value.iloc[0]["FX cost (SGD)"] == 0
    app.selectbox[0].set_value("USD").run()
    assert not app.exception
    assert app.dataframe[2].value.iloc[0]["FX cost (SGD)"] > 0
