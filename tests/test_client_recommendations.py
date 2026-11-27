from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.data_generation import AS_OF
from src.database import load
from src.forecasting import forecast
from src.payments import payment_rows
from src.recommendations import client_recommendations
from src.scenarios import CONSERVATIVE
from src.settlement import DEMO_PRINCIPAL_MINOR, compare_settlement
from src.virtual_accounts import demo_receipts, reconciliation_summary


def test_brief_tracks_calculated_evidence():
    data = load()
    stress = forecast(data, AS_OF, CONSERVATIVE)
    _, rows = demo_receipts(data, AS_OF)
    summary = reconciliation_summary(rows)
    options = compare_settlement(data, AS_OF, DEMO_PRINCIPAL_MINOR, "SGD")
    brief = client_recommendations(payment_rows(data, AS_OF), stress, summary, options)
    assert all(set(row) == {"solution", "problem", "evidence", "action", "impact", "assumptions", "limitations"}
               for row in brief)
    gap = max(row["shortfall_minor"] for row in stress) / 100
    assert f"{gap:,.2f} below buffer" in brief[0]["evidence"]
    assert f"{summary['matched']} of {summary['unique_receipts']}" in brief[1]["evidence"]
    assert f"{options[1]['delay_min'] - options[0]['delay_min']:,} minutes" in brief[2]["impact"]


def test_recommendations_page_displays_client_brief():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    app.radio[0].set_value("Business Recommendations").run()
    assert not app.exception
    assert app.subheader[0].value == "Executive summary"
    assert app.expander[0].label == "Liquidity buffer and contingent funding"
    assert any("Illustrative impact" in item.value for item in app.markdown)
