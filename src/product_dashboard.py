import pandas as pd
import plotly.express as px
import streamlit as st

from src.product_strategy import BASE_ADOPTION_PCT, OFFERS, SCENARIOS, SEGMENTS, evaluate, format_usd, recommend


def show_product_strategy():
    st.caption("Fictional corporate opportunities and illustrative first-year USD economics.")
    segment = st.selectbox("Client segment", SEGMENTS, format_func=lambda item: item.name)
    st.markdown(f"**{segment.industry} · {segment.currency_exposure}** — {segment.need}")
    st.caption(f"{segment.monthly_payments:,} monthly payments · {segment.monthly_receipts:,} monthly receipts · "
               f"{segment.foreign_share_bps / 100:g}% foreign-currency payment share · "
               f"{format_usd(segment.idle_cash_minor)} average potentially idle cash")
    left, middle, right = st.columns(3)
    adoption = left.slider("Eligible cohort adoption (%)", 0, 100, BASE_ADOPTION_PCT)
    volume = middle.slider("Volume (% of baseline)", 0, 200, 100)
    cost = right.slider("Service cost (% of baseline)", 0, 200, 100)
    rows = [evaluate(segment, offer, adoption_pct=adoption, volume_pct=volume, cost_pct=cost) for offer in OFFERS]
    st.dataframe([{"Solution": row["offer"], "Value proposition": offer.value_proposition,
                   "Fit threshold met": row["fit"], "Client gross value (USD)": row["gross_client_value_minor"]/100,
                   "Annual client fee (USD)": row["per_client_fee_minor"]/100,
                   "Client net value (USD)": row["net_client_value_minor"]/100,
                   "Expected clients": float(row["adopted_clients"]), "Fee income (USD)": row["cohort_revenue_minor"]/100,
                   "Cost to serve (USD)": row["cohort_cost_minor"]/100,
                   "Provider contribution (USD)": row["cohort_contribution_minor"]/100}
                  for offer, row in zip(OFFERS, rows)], hide_index=True)
    choice = recommend(rows)
    if choice:
        st.subheader(choice["offer"])
        st.markdown(f"**Fit rule** — {choice['fit_rule']} **Illustrative net client value** — "
                    f"{format_usd(choice['net_client_value_minor'])} per year.")
        offer = next(item for item in OFFERS if item.name == choice["offer"])
        comparisons = []
        for name, uptake, flow, service in SCENARIOS:
            outcome = evaluate(segment, offer, adoption_pct=uptake, volume_pct=flow, cost_pct=service)
            comparisons.append({"Case": name, "Adoption (%)": uptake, "Volume (%)": flow, "Service cost (%)": service,
                                "Provider contribution (USD)": outcome["cohort_contribution_minor"]/100})
        st.plotly_chart(px.bar(pd.DataFrame(comparisons), x="Case", y="Provider contribution (USD)",
                                hover_data=["Adoption (%)", "Volume (%)", "Service cost (%)"]), width="stretch")
    else:
        st.info("No offer meets the fit, client value and per-client contribution rules under these inputs.")
    with st.expander("Illustrative pricing and cost assumptions"):
        st.dataframe([{"Offer": offer.name, "Monthly fee (USD)": offer.monthly_fee_minor/100,
                       "Fee per item (USD)": offer.unit_fee_minor/100,
                       "Monthly provider service cost (USD)": offer.monthly_service_minor/100,
                       "Provider cost per item (USD)": offer.unit_cost_minor/100,
                       "Onboarding per client (USD)": offer.onboarding_minor/100,
                       "Fixed platform cost (USD)": offer.platform_minor/100}
                      for offer in OFFERS], hide_index=True)
        st.caption("Payment items are outgoing instructions. Virtual account items are incoming receipts. "
                   "The table shows baseline prices and costs before your scenario factors.")
    st.caption("Offers are standalone alternatives. Fee income uses expected adopters. Cost includes ongoing support, "
               "year-one onboarding and fixed platform cost. Values and adoption rates are assumptions.")
