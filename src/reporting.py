import argparse
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from src.data_generation import AS_OF
from src.database import load
from src.forecasting import compare, forecast
from src.payments import DOMESTIC_FIXED_MINOR, FX_SPREAD_BPS, WIRE_FEE_BPS, WIRE_FIXED_MINOR
from src.payments import payment_metrics, payment_rows
from src.recommendations import client_recommendations
from src.scenarios import CONSERVATIVE
from src.settlement import DEMO_PRINCIPAL_MINOR, compare_settlement
from src.treasury import consolidate, daily_balances
from src.virtual_accounts import demo_receipts, reconciliation_summary

DISCLOSURE = "Synthetic Data — Educational Portfolio Demonstration"
SHEETS = ("Executive Summary", "Accounts", "Payments", "Daily Balances", "Liquidity Forecast",
          "Scenario Comparison", "Virtual Account Receipts", "Settlement Options", "Assumptions")
NAVY = "152741"
TEAL = "087F8C"
SLATE = "466079"
PAPER = "F2F6F8"


def write_table(ws, headers, rows, money=(), percents=()):
    ws.append(headers)
    for row in rows:
        ws.append(row)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = TEAL
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 32
    for row in ws.iter_rows(min_row=2):
        if row[0].row % 2 == 0:
            for cell in row:
                cell.fill = PatternFill("solid", fgColor=PAPER)
        for cell in row:
            if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                if cell.column - 1 in money:
                    cell.number_format = '#,##0.00;[Red](#,##0.00);0.00'
                elif cell.row in percents and cell.column == 2:
                    cell.number_format = "0.0%"
    for index, column in enumerate(ws.columns, 1):
        width = max(len(str(cell.value or "")) for cell in column)
        ws.column_dimensions[get_column_letter(index)].width = min(max(14, width + 3), 104)


def write_records(ws, rows):
    keys = list(rows[0])
    money = {i for i, key in enumerate(keys) if key.endswith("_minor")}
    headers = [key.removesuffix("_minor").replace("_", " ").title().replace("Usd", "USD") for key in keys]
    values = ([row[key] / 100 if i in money else row[key] for i, key in enumerate(keys)] for row in rows)
    write_table(ws, headers, values, money=money)


def text(slide, x, y, w, h, value, size, color=NAVY, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_top = frame.margin_left = frame.margin_bottom = frame.margin_right = 0
    for index, line in enumerate(value.splitlines()):
        paragraph = frame.add_paragraph() if index else frame.paragraphs[0]
        paragraph.text = line
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(size)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = RGBColor.from_string(color)
        paragraph.space_after = Pt(6)


def deck_slide(deck, title):
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(PAPER)
    text(slide, .72, .57, 11.9, 1.25, title, 34, bold=True)
    text(slide, .72, 7.05, 11.9, .28, DISCLOSURE, 11, SLATE)
    return slide


def write_deck(path, as_of, balances, metrics, baseline, stress, collections, actions):
    deck = Presentation()
    deck.core_properties.title = "Corporate Treasury Briefing"
    deck.core_properties.comments = DISCLOSURE
    deck.core_properties.last_modified_by = ""
    deck.slide_width = Inches(13.333)
    deck.slide_height = Inches(7.5)
    slide = deck_slide(deck, "Corporate cash & cross-border payment analytics")
    text(slide, .72, 1.78, 11.4, 1.1,
         "Can treasury fund the next 30 days while controlling payment costs?", 27, TEAL, True)
    for x, title, body in (
        (.72, "Cash visibility", "Reconcile daily cash across Hong Kong, Shanghai and Singapore. Translate balances and external flows into USD."),
        (4.78, "Payment operations", "Track instructed and settled principal, exceptions, settlement delays, bank fees and FX spreads."),
        (8.84, "Liquidity planning", "Stress receipt timing, supplier schedules, expenses and pricing against account-level buffers."),
    ):
        text(slide, x, 3.42, 3.65, .45, title, 21, bold=True)
        text(slide, x, 4.06, 3.65, 1.92, body, 19, SLATE)
    text(slide, .72, 6.5, 11.9, .35, f"Portfolio snapshot through {as_of:%d %B %Y}", 14, SLATE)

    slide = deck_slide(deck, "Cash and payment performance")
    latest = consolidate(balances)[-1]["closing_usd_minor"]
    end = consolidate(baseline)[-1]["closing_usd_minor"]
    stressed_end = consolidate(stress)[-1]["closing_usd_minor"]
    breaches = sum(row["breach"] for row in stress)
    for y, label, value, detail in (
        (1.63, "Group cash", f"USD {latest/100:,.0f}", "Historical closing balance at dated FX midpoint"),
        (2.61, "Settled rate", f"{metrics['settled_rate']:.1%}", f"Of {metrics['count']:,} payment instructions"),
        (3.59, "Settled payment cost", f"USD {metrics['fees_usd_minor']/100:,.0f}", "Fixed fees, variable fees and FX spread"),
        (4.57, "Day-30 stress impact", f"USD {(stressed_end-end)/100:+,.0f}", f"Versus expected closing cash · {breaches} breached account-days under stress"),
        (5.65, "Receipt attribution", f"{collections['match_rate']:.0%}",
         f"{collections['matched']} of {collections['unique_receipts']} unique Singapore receipts matched"),
    ):
        text(slide, .72, y, 3.02, .65, label, 19, bold=True)
        text(slide, 3.85, y - .03, 3.1, .65, value, 25, TEAL, True)
        text(slide, 7.18, y, 5.37, .82, detail, 17, SLATE)

    slide = deck_slide(deck, "Treasury actions and decision limits")
    for index, action in enumerate(actions[:3]):
        y = 1.55 + 1.36 * index
        text(slide, .72, y, 11.8, .39, action["action"], 19, bold=True)
        text(slide, .72, y + .45, 11.8, .77, action["evidence"], 16, SLATE)
    if not actions:
        text(slide, .72, 1.55, 11.8, .8, "The available data triggered no modeled interventions.", 19)
    text(slide, .72, 5.84, 11.8, .92,
         "Forecast uses known schedules and fixed as-of FX. Confirm funding availability, market pricing and payment cutoffs before acting.",
         16, SLATE)
    deck.save(path)


def export_reports(output=Path("reports"), data=None, as_of=AS_OF):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    data = load() if data is None else data
    payments = payment_rows(data, as_of)
    balances = daily_balances(data, as_of)
    baseline = forecast(data, as_of)
    stress = forecast(data, as_of, CONSERVATIVE)
    metrics = payment_metrics(payments)
    mappings, receipts = demo_receipts(data, as_of)
    collections = reconciliation_summary(receipts)
    settlement = compare_settlement(data, as_of, DEMO_PRINCIPAL_MINOR, "SGD", balances=balances)
    actions = client_recommendations(payments, stress, collections, settlement)
    latest = consolidate(balances)[-1]["closing_usd_minor"]
    book = Workbook()
    book.properties.creator = ""
    book.properties.title = "Corporate Treasury Analysis"
    book.active.title = SHEETS[0]
    for name in SHEETS[1:]:
        book.create_sheet(name)
    summary = [
        ("Reporting date", str(as_of), "ISO calendar date"),
        ("Group closing cash", latest/100, "USD at historical closing FX"),
        ("Payment instructions", metrics["count"], "Count through the reporting date"),
        ("Settled rate", metrics["settled_rate"], "Share of instructions"),
        ("Failed rate", metrics["failed_rate"], "Share of instructions"),
        ("Pending rate", metrics["pending_rate"], "Share of instructions"),
        ("Instructed principal", metrics["volume_usd_minor"]/100, "USD at instruction-date rates"),
        ("Settled principal", metrics["settled_usd_minor"]/100, "USD at settlement-date rates"),
        ("Settled cost", metrics["fees_usd_minor"]/100, "USD, fixed + variable fees + spread"),
        ("Expected day-30 cash", consolidate(baseline)[-1]["closing_usd_minor"]/100, "USD, frozen reporting-date FX"),
        ("Conservative day-30 cash", consolidate(stress)[-1]["closing_usd_minor"]/100, "USD, frozen reporting-date FX"),
        ("Conservative breaches", sum(r["breach"] for r in stress), "Account-days"),
        ("Virtual receipts matched", collections["match_rate"], "Share of unique records in synthetic SG sample"),
        ("Virtual receipt value matched", collections["value_rate"], "Share of unique posted SGD value"),
        ("Duplicate receipt records", collections["duplicates"], "Excluded from attribution denominators"),
    ]
    write_table(book[SHEETS[0]], ["Metric", "Value", "Unit or definition"], summary, percents={5, 6, 7, 14, 15})
    for name, rows in zip(SHEETS[1:6], (data["accounts"], payments, balances, baseline, compare(baseline, stress))):
        if rows:
            write_records(book[name], rows)
        else:
            write_table(book[name], ["Status"], [("No rows in this reporting window.",)])
    customer_by_id = {row["virtual_account"]: row["customer"] for row in mappings}
    receipt_rows = [{key: value for key, value in row.items() if key != "receipt_sgd"} for row in receipts]
    for row in receipt_rows:
        row["configured_customer"] = customer_by_id.get(row["virtual_account"])
    if receipt_rows:
        write_records(book["Virtual Account Receipts"], receipt_rows)
    write_records(book["Settlement Options"],
                  [{key: value for key, value in row.items() if key != "timeline"} for row in settlement])
    assumptions = [
        ("Disclosure", DISCLOSURE),
        ("Amount units", "Major currency units. USD fields are explicitly marked."),
        ("Payment currencies", "Principal uses instruction currency. Settled amount and charges use account currency."),
        ("FX quotation", "USD per 1 unit of local currency. Historical measures use the relevant dated midpoint."),
        ("Opening cash", "Forecast begins from end-of-day cash on the reporting date."),
        ("Forecast inputs", "Known scheduled flows only. As-of FX held flat. Pending without a schedule is excluded."),
        ("Bank fee", f"{DOMESTIC_FIXED_MINOR/100:g} domestic or {WIRE_FIXED_MINOR/100:g} + {WIRE_FEE_BPS} bp cross-border."),
        ("FX spread", f"{FX_SPREAD_BPS} bp on account-currency equivalent when currencies differ."),
        ("Conservative case", "Receipts +5 days, SGD 15,000 expense on day 7, fees +10 bp, FX spread +25 bp."),
        ("Virtual account receipts", "Latest ten posted Singapore receipts with synthetic attribution; duplicate feed rows add no cash."),
        ("Settlement comparison", "SGD 200,000 outgoing example; illustrative timing, fee and buffer results in SGD."),
        ("Local account money", "Round half up to cents. Translated amounts can differ by a cent from aggregate conversions."),
    ]
    write_table(book[SHEETS[-1]], ["Assumption", "Treatment"], assumptions)
    workbook = output / "treasury_analysis.xlsx"
    slides = output / "treasury_briefing.pptx"
    book.save(workbook)
    write_deck(slides, as_of, balances, metrics, baseline, stress, collections, actions)
    return workbook, slides


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export treasury workbook and executive briefing.")
    parser.add_argument("--output", type=Path, default=Path("reports"))
    parser.add_argument("--database", type=Path)
    args = parser.parse_args()
    for path in export_reports(args.output, load(args.database)):
        print(path)
