import argparse
from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from src.client_solutions import PROFILES, assess_client, solutions
from src.data_generation import AS_OF
from src.database import load
from src.reporting import SLATE, TEAL, deck_slide, text

DISCLOSURE = "Fictional client case study — educational simulation"


def proposal_bytes(profile, as_of, metrics, recommendations):
    deck = Presentation()
    deck.slide_width = Inches(13.333)
    deck.slide_height = Inches(7.5)
    deck.core_properties.title = f"{profile.name} | Treasury solutions proposal"
    deck.core_properties.comments = DISCLOSURE
    deck.core_properties.last_modified_by = ""
    lead = recommendations[0]
    delay = f"{metrics['median_delay']:g} calendar days" if metrics["median_delay"] is not None else "Unavailable"
    top = sorted(metrics["corridors"], key=metrics["corridors"].get, reverse=True)[:3]
    content = (
        (f"Treasury proposal for {profile.name}", profile.industry,
         [profile.need, f"Synthetic operating accounts {', '.join(profile.accounts)}", f"Ledger date {as_of}"]),
        ("Current state", "30-day payment instruction window",
         [f"{metrics['count']:,} instructions · USD {metrics['volume_minor']/100:,.2f} instructed value",
          f"Median settled delay · {delay}", "Leading corridors by instructed value · " + (", ".join(top) or "Unavailable")]),
        ("Treasury priorities", lead["solution"],
         [r["evidence"] for r in recommendations[:3]]),
        ("Proposed solutions", "Prioritise the evidence from the synthetic assessment",
         [f"{r['solution']} · {r['benefit']}" for r in recommendations[:3]]),
        ("Illustrative operating impact", "Measure results against the existing baseline",
         [f"Peak 30-day gross buffer gap under a five-day delay · USD {metrics['peak_gap_minor']/100:,.2f}",
          f"Cross-currency instruction value · USD {metrics['fx_volume_minor']/100:,.2f}",
          lead["benefit"]]),
        ("Implementation roadmap", "Validate, pilot, then review",
         [lead["dependencies"], "Pilot on a limited account or corridor scope and reconcile daily.",
          "Review cash gaps, payment exceptions and manual effort against the starting baseline."]),
        ("Assumptions, risks and next steps", "Confirm inputs before a commercial decision",
         [lead["assumptions"], lead["risks"], "Agree success measures, owners and a go/no-go review before expansion."]),
    )
    for title, heading, paragraphs in content:
        slide = deck_slide(deck, title)
        slide.shapes[-1].text_frame.paragraphs[0].text = DISCLOSURE
        text(slide, .72, 1.65, 11.78, .78, heading, 23, TEAL, True)
        for index, paragraph in enumerate(paragraphs):
            text(slide, .72, 2.63 + index * 1.07, 11.7, .96, paragraph, 19, SLATE)
    stream = BytesIO()
    deck.save(stream)
    return stream.getvalue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the fictional importer/exporter proposal.")
    parser.add_argument("--output", type=Path, default=Path("reports/client_treasury_proposal.pptx"))
    args = parser.parse_args()
    profile = PROFILES[0]
    metrics = assess_client(load(), profile, AS_OF)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(proposal_bytes(profile, AS_OF, metrics, solutions(profile, metrics)))
