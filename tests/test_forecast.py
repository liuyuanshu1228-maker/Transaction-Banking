from datetime import timedelta

from src.data_generation import AS_OF
from src.database import load
from src.forecasting import compare, forecast
from src.scenarios import BASELINE, Scenario


def test_forecast_baseline_equivalence_and_horizon():
    data = load()
    base = forecast(data, AS_OF)
    assert base == forecast(data, AS_OF, Scenario()) == forecast(data, AS_OF, BASELINE)
    assert len(base) == 30 * len(data["accounts"])
    assert base[-1]["day"] == str(AS_OF + timedelta(days=30))


def test_future_information_excluded():
    data = load()
    base = forecast(data, AS_OF)
    data["scheduled"].append(dict(account="SG", known_on=str(AS_OF + timedelta(days=1)),
                                  due_on=str(AS_OF + timedelta(days=2)), kind="receipt",
                                  currency="SGD", amount_minor=999_999))
    assert forecast(data, AS_OF) == base


def test_expense_delta_and_breach():
    data = load()
    base = forecast(data, AS_OF)
    expense = [r for r in base if r['account'] == 'SG'][1]['closing_minor'] + 100
    shocked = forecast(data, AS_OF, Scenario(expense_minor=expense, expense_day=2))
    rows = [r for r in compare(base, shocked) if r["account"] == "SG"]
    assert rows[0]["delta_minor"] == 0
    assert all(r["delta_minor"] == -expense for r in rows[1:])
    assert rows[1]["breach"] and rows[1]["shortfall_minor"] > 0
