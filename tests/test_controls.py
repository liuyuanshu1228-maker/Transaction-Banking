from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.controls import control_cases, record_review, review_queue
from src.data_generation import AS_OF
from src.database import load
from src.virtual_accounts import demo_receipts, reconciliation_summary


def test_rules_and_review_history_preserve_receipts():
    _, receipts = demo_receipts(load(), AS_OF)
    summary = reconciliation_summary(receipts)
    cases = control_cases(receipts)
    assert {row["trigger"] for row in cases} == {"Unmatched virtual reference", "Missing virtual reference",
                                                "Duplicate bank reference", "Synthetic customer verification incomplete"}
    case_id = cases[0]["case_id"]
    events = record_review(cases, [], case_id, "Escalated")
    assert events == [dict(event=1, case_id=case_id, from_status="Pending Review", to_status="Escalated")]
    assert review_queue(cases, events)[0]["review_status"] == "Escalated"
    assert reconciliation_summary(receipts) == summary
    for invalid_case, decision in [(case_id, "Cleared"), ("UNKNOWN", "Escalated"),
                                   (cases[1]["case_id"], "Pending Review")]:
        with pytest.raises(ValueError, match="pending cases"):
            record_review(cases, events, invalid_case, decision)


def test_reviewer_can_record_a_decision_in_streamlit():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    app.radio[0].set_value("Payment Analytics").run()
    app.selectbox(key="control_decision").set_value("Escalated")
    app.button(key="record_control_review").click().run()
    assert not app.exception
    event = next(frame.value for frame in app.dataframe if "to_status" in frame.value)
    assert event.iloc[0]["to_status"] == "Escalated"
