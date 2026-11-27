from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.product_strategy import OFFERS, PILOT_SEGMENT, SCENARIOS, evaluate, format_usd


ROOT = Path(__file__).resolve().parents[1]


def test_market_page_respects_cutoff_and_reprices():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    app.radio[0].set_value("Market Intelligence").run()
    assert not app.exception
    cutoff = next(widget for widget in app.date_input if widget.label == "Research publication cutoff")
    cutoff.set_value(date(2025, 7, 27))
    app.selectbox[0].set_value("USD/SGD").run()
    assert not app.exception
    assert list(app.dataframe[0].value["observed_on"]) == ["2025-01-24", "2025-04-25"]
    spread = next(widget for widget in app.slider if widget.label == "Additional supplier FX spread (bp)")
    spread.set_value(50).run()
    assert not app.exception
    summary = app.dataframe[1].value.set_index("Measure (USD)")
    assert summary.loc["30-day supplier FX spread cost", "Change"] > 0


def test_product_page_sensitivity_and_case_numbers():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    app.radio[0].set_value("Client & Product Strategy").run()
    assert not app.exception
    base = app.dataframe[0].value
    app.slider[0].set_value(0).run()
    assert not app.exception
    assert base["Fee income (USD)"].sum() > 0
    assert app.dataframe[0].value["Fee income (USD)"].sum() == 0
    case = (ROOT / "docs/product_commercialisation_case.md").read_text(encoding="utf-8")
    for _, uptake, flow, cost in SCENARIOS:
        row = evaluate(PILOT_SEGMENT, OFFERS[1], adoption_pct=uptake, volume_pct=flow, cost_pct=cost)
        assert format_usd(abs(row["cohort_contribution_minor"])).removesuffix(".00") in case
