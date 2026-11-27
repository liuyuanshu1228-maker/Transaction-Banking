from pathlib import Path

from streamlit.testing.v1 import AppTest

from app import PAGES


def test_all_pages_execute():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    for page in PAGES:
        app = app.radio[0].set_value(page).run()
        assert not app.exception, page
        assert app.header[0].value == page


def test_scenario_control_updates_output():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    app.radio[0].set_value("Scenario Lab").run()
    baseline = app.metric[1].value
    app.number_input[0].set_value(20_000).run()
    assert not app.exception
    assert app.metric[1].value != baseline
