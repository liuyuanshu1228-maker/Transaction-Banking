from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.data_generation import AS_OF
from src.database import load
from src.treasury import daily_balances
from src.virtual_accounts import MAPPINGS, demo_receipts, reconcile, reconciliation_summary


def test_virtual_accounts_attribute_existing_cash_once():
    data = load()
    master_rows = [r for r in daily_balances(data, AS_OF) if r["account"] == "SG"][-10:]
    mappings, rows = demo_receipts(data, AS_OF)
    summary = reconciliation_summary(rows)
    assert {mapping["master_account"] for mapping in mappings} == {"SG"}
    assert summary["posted_minor"] == sum(r["inflow_minor"] for r in master_rows)
    assert summary["matched_minor"] + summary["unattributed_minor"] == summary["posted_minor"]
    assert summary["unique_receipts"] == 10 and summary["match_rate"] == .8
    assert summary["duplicates"] == 1
    assert {row["status"] for row in rows} == {"Matched", "Duplicate bank reference",
                                              "Missing virtual reference", "Unmatched virtual reference"}


def test_wrong_master_is_unmatched_and_duplicate_ids_are_rejected():
    feed = [dict(bank_reference="test", virtual_account="SYN-VA-101", posted_account="HK", amount_minor=100)]
    assert reconcile(feed, MAPPINGS)[0]["status"] == "Unmatched virtual reference"
    with pytest.raises(ValueError, match="unique"):
        reconcile(feed, (*MAPPINGS, MAPPINGS[0]))


def test_virtual_account_dashboard_renders_metrics():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    app.radio[0].set_value("Payment Analytics").run()
    assert not app.exception
    assert any(metric.label == "Matched receipt records" and metric.value == "80.0%" for metric in app.metric)
