"""Public market provenance and synthetic corporate research brief."""

import argparse
from csv import DictReader
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import mean
from urllib.parse import urlsplit

from src.data_generation import AS_OF
from src.database import load
from src.market_intelligence import FX_UNITS, POLICY, SNAPSHOT, published_observations
from src.payments import payment_rows
from src.treasury import daily_balances

UNITS = {POLICY: "Percent per year", **FX_UNITS}
FIELDS = ("series", "observed_on", "published_on", "retrieved_on", "unit", "value",
          "source_name", "source_url", "licensing_notes")
RETRIEVED_ON = "2026-11-27"
FRAMEWORK = (
    ("Cross-border payments", "Compare corridor and beneficiary credit time; check exception handling.",
     "https://www.fsb.org/2026/11/g20-roadmap-for-enhancing-cross-border-payments-consolidated-progress-report-for-2026/"),
    ("Corporate liquidity", "Compare local cash with local buffers, then translate to USD for reporting.",
     "https://careers.bankofamerica.com/en-us/company/organization/global-payments-solutions"),
    ("Working capital", "Compare due dates and actual cash timing; test the impact of collection delays.",
     "https://www.wto.org/english/res_e/booksp_e/gvcreport2025-06_e.pdf"),
    ("FX exposure", "Separate USD payables from USD translation of existing operating cash.",
     "https://www.federalreserve.gov/releases/h10/20250728/"),
    ("Trade and supply-chain finance", "Ask for invoice terms, acceptance, tenor and counterparty evidence before sizing a facility.",
     "https://www.wto.org/english/res_e/booksp_e/gvcreport2025-06_e.pdf"),
)


def csv_observations(lines, cutoff):
    cutoff = date.fromisoformat(str(cutoff))
    reader = DictReader(lines)
    if not set(FIELDS).issubset(reader.fieldnames or ()):
        raise ValueError("Provide all required provenance and measurement columns.")
    rows, seen = [], set()
    for line, raw in enumerate(reader, 2):
        if any(raw[key] is None or not raw[key].strip() for key in FIELDS):
            raise ValueError(f"Missing value or provenance on line {line}.")
        row = {key: raw[key].strip() for key in FIELDS}
        try:
            observed, published, retrieved = [date.fromisoformat(row[key]) for key in
                                               ("observed_on", "published_on", "retrieved_on")]
            if observed > published or published > retrieved:
                raise ValueError("Expected observation ≤ publication ≤ retrieval.")
            value = Decimal(row["value"])
            source = urlsplit(row["source_url"])
            key = row["series"], observed
            if (row["unit"] != UNITS.get(row["series"]) or not value.is_finite()
                or (row["series"] in FX_UNITS and value <= 0) or source.scheme != "https"
                or not source.hostname or key in seen):
                raise ValueError("Check units, quote direction, HTTPS source and duplicates.")
        except (ValueError, InvalidOperation) as error:
            raise ValueError(f"Invalid observation on line {line}: {error}") from error
        seen.add(key)
        if published <= cutoff:
            rows.append(dict(row, value=value, provenance="User-supplied · independently verify source"))
    return sorted(rows, key=lambda row: (row["series"], row["observed_on"]))


def research_observations(cutoff, mode):
    if mode == "Official snapshot":
        return [dict(row, source_name="Federal Reserve Board", retrieved_on=RETRIEVED_ON,
                     licensing_notes="Board material generally public domain; see disclaimer",
                     provenance="Published observation")
                for row in published_observations(cutoff) if row["series"] in UNITS]
    cutoff = str(date.fromisoformat(str(cutoff)))
    return [dict(series=series, observed_on=day, published_on=day, retrieved_on="—",
                 unit=UNITS[series], value=Decimal(value), source_name="Educational scenario inputs",
                 source_url="", licensing_notes="Repository terms", provenance="Synthetic assumptions")
            for series, start, end in ((POLICY, "4.50", "4.25"), ("USD/CNY", "7.20", "7.25"),
                                       ("USD/HKD", "7.80", "7.81"), ("USD/SGD", "1.35", "1.32"))
            for day, value in (("2025-01-24", start), ("2025-07-25", end)) if day <= cutoff]


def statistics(rows):
    return [dict(series=series, unit=UNITS[series], count=len(values),
                 minimum=min(values), maximum=max(values), average=mean(values))
            for series in UNITS if (values := [row["value"] for row in rows if row["series"] == series])]


def corporate_snapshot(data, as_of):
    balances = [row for row in daily_balances(data, as_of) if row["day"] == str(as_of)]
    payments = payment_rows(data, as_of)
    usd_settled = sum(row["settled_usd_minor"] for row in payments if row["currency"] == "USD")
    return dict(balances=balances, corridors=sorted({r["corridor"] for r in payments}),
                usd_settled_minor=usd_settled)


def market_brief(rows, snapshot, cutoff, as_of, mode):
    lines = ["# Industry and treasury research brief", "",
             f"Research dataset: {mode}; publication cutoff {cutoff}.",
             f"Fictional company: Harbor Components · synthetic ledger as of {as_of}.", "",
             "Operating exposure covers Shanghai, Hong Kong and Singapore. Suppliers include manufacturing "
             "vendors and freight providers; customers include regional industrial distributors.", "",
             "## Research framework", ""]
    lines += [f"- **{topic}.** {question} [Reference]({url})" for topic, question, url in FRAMEWORK]
    lines += ["", "## Synthetic exposure", "",
              f"Settled USD-denominated principal through the ledger date: USD {snapshot['usd_settled_minor']/100:,.2f}."]
    lines += [f"- {row['region']}: {row['currency']} {row['closing_minor']/100:,.2f} cash "
              f"(USD {row['closing_usd_minor']/100:,.2f})." for row in snapshot["balances"]]
    lines += ["", "## Descriptive statistics", ""]
    lines += [f"- {row['series']}: {row['count']} observations; mean {row['average']:.4f} {row['unit']}."
              for row in statistics(rows)]
    lines += ["", "The published series provide context. Cash, corridors and exposures come from the synthetic ledger."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export a reproducible market and industry brief.")
    parser.add_argument("--output", type=Path, default=Path("reports/industry_research_brief.md"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(market_brief(research_observations(SNAPSHOT, "Official snapshot"),
                                        corporate_snapshot(load(), AS_OF), SNAPSHOT, AS_OF,
                                        "Official snapshot"), encoding="utf-8")
