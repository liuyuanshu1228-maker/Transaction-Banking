from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.client_solutions import PROFILES

ROOT = Path(__file__).resolve().parents[1]


def open_page(name):
    app = AppTest.from_file(ROOT / "app.py", default_timeout=40).run()
    app.sidebar.radio[0].set_value(name).run()
    assert not app.exception
    return app


def test_research_source_can_switch_to_synthetic():
    app = open_page("Market & Industry Intelligence")
    assert set(app.dataframe[1].value["provenance"]) == {"Published observation"}
    next(widget for widget in app.radio if widget.label == "Research dataset").set_value("Synthetic fallback").run()
    assert not app.exception
    assert set(app.dataframe[1].value["provenance"]) == {"Synthetic assumptions"}


def test_client_selection_recalculates_metrics():
    app = open_page("Client Solutions")
    initial = app.metric[0].value
    app.selectbox[0].set_value(PROFILES[1]).run()
    assert not app.exception
    assert int(app.metric[0].value) > int(initial)


def test_zero_adoption_keeps_client_impact_and_removes_revenue():
    app = open_page("Commercial Opportunity")
    savings = app.metric[0].value
    next(widget for widget in app.slider if widget.label == "Expected adoption (%)").set_value(0).run()
    assert not app.exception
    assert app.metric[0].value == savings
    assert app.metric[1].value == "USD 0.00"
    assert app.metric[3].value == "Unavailable"
