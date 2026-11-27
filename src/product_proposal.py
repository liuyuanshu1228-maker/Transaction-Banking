"""Generate a fictional client proposal with the portfolio's existing deck layout."""

import argparse
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from src.product_strategy import OFFERS, PILOT_SEGMENT, evaluate, format_usd, recommend
from src.reporting import SLATE, TEAL, deck_slide, text


def export_proposal(path=Path("reports/client_product_proposal.pptx")):
    client = PILOT_SEGMENT
    options = [evaluate(client, offer) for offer in OFFERS]
    choice = recommend(options)
    deck = Presentation()
    deck.slide_width = Inches(13.333)
    deck.slide_height = Inches(7.5)
    deck.core_properties.title = "Pearl Commerce | Collections Pilot Proposal"
    deck.core_properties.comments = "Fictional client proposal with illustrative USD economics."
    deck.core_properties.last_modified_by = ""

    slide = deck_slide(deck, "A collections pilot for Pearl Commerce")
    text(slide, .72, 1.79, 11.8, .8, "Identify payer receipts before they reach the manual queue", 27, TEAL, True)
    text(slide, .72, 3.15, 5.7, 1.4, f"{client.monthly_receipts:,} incoming receipts per month\n"
         f"{client.manual_receipt_bps / 100:g}% assumed to need manual attribution", 23)
    text(slide, 7.0, 3.15, 5.4, 1.6, "Marketplace cash operations\nCNY, HKD and USD exposure", 23, SLATE)
    text(slide, .72, 5.56, 11.6, .72, "Fictional client profile · Scope a single master account and a limited payer cohort.", 16, SLATE)

    slide = deck_slide(deck, "Start with virtual account collections")
    text(slide, .72, 1.69, 11.6, 1.2, "Assign payer identifiers, preserve the master account, and review missing or duplicate references.", 22)
    for x, key, label in ((.72, "gross_client_value_minor", "Modeled effort value"),
                          (4.73, "per_client_fee_minor", "Illustrative service fee"),
                          (8.74, "net_client_value_minor", "Modeled net client value")):
        text(slide, x, 3.25, 3.7, .55, format_usd(choice[key]), 25, TEAL, True)
        text(slide, x, 4.00, 3.7, .72, label, 18)
    text(slide, .72, 5.53, 11.8, 1.04, "Annual estimate assumes 70% fewer manual cases, six minutes per case and USD 30 per hour. "
         "Effort value assumes released time can be redeployed.", 16, SLATE)

    slide = deck_slide(deck, "Measure performance before expanding")
    for index, (title, detail) in enumerate((
        ("Establish a baseline", "Measure receipt-match rate, exception age and manual minutes for the chosen payer cohort."),
        ("Test reference handling", "Review missing and duplicate references, daily reconciliation and operational ownership."),
        ("Decide whether to expand", "Compare realized effort and exception coverage with the indicative fee. Validate eligibility and integration needs."),
    )):
        y = 1.58 + 1.43 * index
        text(slide, .72, y, 11.7, .46, title, 21, TEAL, True)
        text(slide, .72, y + .54, 11.7, .72, detail, 18)
    text(slide, .72, 6.22, 11.8, .5, "Illustrative proposal. Confirm client inputs, technical design and commercial terms before adoption.", 14, SLATE)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    deck.save(path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/client_product_proposal.pptx"))
    args = parser.parse_args()
    print(export_proposal(args.output))
