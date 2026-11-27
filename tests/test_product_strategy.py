import pytest
from pptx import Presentation

from src.product_proposal import export_proposal
from src.product_strategy import OFFERS, PILOT_SEGMENT, SEGMENTS, evaluate, recommend


@pytest.mark.parametrize("segment,offer", tuple(zip(SEGMENTS, OFFERS)))
def test_recommendation_routes_each_segment_to_evidenced_fit(segment, offer):
    options = [evaluate(segment, candidate) for candidate in OFFERS]
    selection = recommend(options)
    assert selection["offer"] == offer.name
    assert selection["net_client_value_minor"] > 0


def test_marketplace_economics_hand_calculated():
    row = evaluate(PILOT_SEGMENT, OFFERS[1])
    assert row["adopted_clients"] == 14
    assert row["gross_client_value_minor"] == 9676800
    assert row["per_client_fee_minor"] == 1404000
    assert row["net_client_value_minor"] == 8272800
    assert row["cohort_revenue_minor"] == 19656000
    assert row["cohort_cost_minor"] == 10896000
    assert row["cohort_contribution_minor"] == 8760000


def test_adoption_service_cost_and_volume_behave_independently():
    base = evaluate(PILOT_SEGMENT, OFFERS[1])
    zero = evaluate(PILOT_SEGMENT, OFFERS[1], adoption_pct=0)
    expensive = evaluate(PILOT_SEGMENT, OFFERS[1], cost_pct=200)
    thin = evaluate(PILOT_SEGMENT, OFFERS[1], volume_pct=0)
    assert zero["cohort_revenue_minor"] == 0
    assert zero["cohort_contribution_minor"] == -OFFERS[1].platform_minor
    assert expensive["cohort_revenue_minor"] == base["cohort_revenue_minor"]
    assert expensive["cohort_cost_minor"] > base["cohort_cost_minor"]
    assert thin["net_client_value_minor"] < 0
    assert recommend([thin, expensive]) == expensive
    no_provider_margin = dict(base, per_client_cost_minor=base["per_client_fee_minor"])
    assert recommend([thin, no_provider_margin]) is None
    with pytest.raises(ValueError, match="Adoption"):
        evaluate(PILOT_SEGMENT, OFFERS[1], adoption_pct=101)


def test_proposal_is_editable_and_contains_model_outputs(tmp_path):
    deck = Presentation(export_proposal(tmp_path / "proposal.pptx"))
    assert len(deck.slides) == 3
    content = "\n".join(shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame)
    assert "Pearl Commerce" in content
    assert "USD 82,728.00" in content
    assert "Synthetic Data" in content
