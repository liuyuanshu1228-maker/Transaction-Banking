from openpyxl import load_workbook
from pptx import Presentation

from src.data_generation import AS_OF
from src.database import load
from src.forecasting import forecast
from src.reporting import DISCLOSURE, SHEETS, export_reports
from src.treasury import consolidate, daily_balances


def test_excel_export_reopens_and_matches_calculations(tmp_path):
    data = load()
    workbook, _ = export_reports(tmp_path, data)
    with workbook.open("rb") as file:
        book = load_workbook(file, read_only=True, data_only=True)
        assert tuple(book.sheetnames) == SHEETS
        assert book["Daily Balances"].max_row == 631
        summary = {key: value for key, value, _ in list(book["Executive Summary"].values)[1:]}
        assert summary["Group closing cash"] == consolidate(daily_balances(data, AS_OF))[-1]["closing_usd_minor"]/100
        assert summary["Expected day-30 cash"] == consolidate(forecast(data, AS_OF))[-1]["closing_usd_minor"]/100
        assert list(book["Scenario Comparison"].values)[0][-1] == "Delta USD"
        assert summary["Virtual receipts matched"] == .8
        assert book["Virtual Account Receipts"].max_row == 12
        methods = list(book["Settlement Options"].values)[1:]
        assert [row[1] for row in methods] == [1, 2880]
        assert [row[3] for row in methods] == [1, 6]
        book.close()


def test_powerpoint_export_contains_three_briefing_slides(tmp_path):
    _, slides = export_reports(tmp_path)
    deck = Presentation(slides)
    assert len(deck.slides) == 3
    text = [[shape.text for shape in slide.shapes if shape.has_text_frame] for slide in deck.slides]
    assert all(DISCLOSURE in slide for slide in text)
    assert "Cash and payment performance" in text[1]
    assert any("funding transfer" in item for item in text[2])
    assert any("80%" in item for item in text[1])
    assert any("Assign identifiers" in item for item in text[2])
