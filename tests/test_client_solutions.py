from io import BytesIO

from pptx import Presentation

from src.client_solutions import PROFILES, assess_client, client_source, solutions
from src.client_treasury_proposal import DISCLOSURE, proposal_bytes
from src.data_generation import AS_OF
from src.database import load


def test_profiles_and_payment_scope():
    data = load()
    exporter, domestic, regional = [assess_client(data, profile, AS_OF) for profile in PROFILES]
    assert domestic["count"] > exporter["count"] and domestic["fx_share"] == 0
    assert domestic["collections"] is None and regional["collections"]["match_rate"] == .8
    assert len(domestic["corridors"]) == 1
    original = [r for r in load(seed=43)["payments"] if r["account"] == "HK" and r["currency"] == "HKD"]
    assert sum(r["principal_minor"] for r in client_source(data, PROFILES[1])["payments"]) == sum(
        r["principal_minor"] for r in original)
    assert "Trade and supply-chain finance discovery" in [r["solution"] for r in solutions(PROFILES[0], exporter)]
    assert all("FX risk" not in r["solution"] for r in solutions(PROFILES[1], domestic))


def test_proposal_uses_same_profile_and_kpis():
    client = PROFILES[2]
    metrics = assess_client(load(), client, AS_OF)
    deck = Presentation(BytesIO(proposal_bytes(client, AS_OF, metrics, solutions(client, metrics))))
    assert len(deck.slides) == 7
    pages = [" ".join(shape.text for shape in slide.shapes if shape.has_text_frame) for slide in deck.slides]
    assert client.name in pages[0]
    assert f"USD {metrics['volume_minor']/100:,.2f}" in pages[1]
    assert all(DISCLOSURE in page for page in pages)
