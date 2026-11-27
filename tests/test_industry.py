import pytest

from src.data_generation import AS_OF
from src.database import load
from src.industry_research import FIELDS, corporate_snapshot, csv_observations, research_observations, statistics
from src.treasury import daily_balances


def test_publication_lag_and_usd_rollup():
    early = research_observations("2025-07-25", "Official snapshot")
    later = research_observations("2025-07-28", "Official snapshot")
    assert len(later) == len(early) + 3
    assert sum(r["closing_usd_minor"] for r in corporate_snapshot(load(), AS_OF)["balances"]) == 455044328
    assert len(daily_balances(load(), AS_OF)) == 630


def test_csv_provenance_cutoff_and_statistics():
    header = ",".join(FIELDS)
    record = "USD/CNY,2025-01-10,2025-01-13,2025-02-13,CNY per USD,7.25,Official source,https://example.org,Public"
    assert csv_observations([header, record], "2025-01-12") == []
    rows = csv_observations([header, record], "2025-01-13")
    assert statistics(rows)[0]["average"] == 7.25
    for invalid in (record.replace("CNY per USD", "USD per CNY"), record.replace("7.25", ""),
                    record.replace("2025-02-13", "2025-01-01")):
        with pytest.raises(ValueError):
            csv_observations([header, invalid], "2025-01-20")
    with pytest.raises(ValueError, match="duplicates"):
        csv_observations([header, record, record], "2025-02-20")


def test_synthetic_fallback_identifies_assumptions():
    rows = research_observations(AS_OF, "Synthetic fallback")
    assert all(r["provenance"] == "Synthetic assumptions" and not r["source_url"] for r in rows)
