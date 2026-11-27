from dataclasses import replace

import pandas as pd
import plotly.express as px
import streamlit as st

from src.client_solutions import PROFILES, assess_client
from src.commercial_opportunity import adoption_cases, business_case, compare_economics, default_case


def show_commercial(data, as_of):
    st.caption("Fictional volume and illustrative USD pricing. Client cost and provider economics use separate calculations.")
    profile = st.selectbox("Commercial client segment", PROFILES, format_func=lambda p: p.name)
    configs = {client: default_case(assess_client(data, client, as_of)) for client in PROFILES}
    inputs, baseline, proposed = configs[profile]
    with st.expander("Transaction, price and operating assumptions", expanded=True):
        left, middle, right = st.columns(3)
        volume = left.number_input("Monthly payments", min_value=0, value=inputs.monthly_volume)
        ticket = left.number_input("Average payment size (USD)", min_value=0.0, value=inputs.ticket_minor/100)
        fx = left.slider("FX share (bp)", 0, 10_000, inputs.fx_share_bps)
        base_fee = middle.number_input("Baseline fee per payment (USD)", min_value=0.0, value=baseline.fee_minor/100)
        new_fee = middle.number_input("Proposed fee per payment (USD)", min_value=0.0, value=proposed.fee_minor/100)
        base_spread = middle.slider("Baseline FX spread (bp)", 0, 250, baseline.spread_bps)
        new_spread = middle.slider("Proposed FX spread (bp)", 0, 250, proposed.spread_bps)
        adoption = right.slider("Expected adoption (%)", 0, 100, inputs.adoption_pct)
        implementation = right.number_input("Provider rollout cost (USD)", min_value=0, value=inputs.bank_implementation_minor//100)
        service = right.number_input("Provider monthly service per adopter (USD)", min_value=0,
                                     value=inputs.bank_service_month_minor//100)
        new_buffer = right.number_input("Proposed liquidity buffer (USD)", min_value=0.0,
                                        value=proposed.buffer_minor/100)
        st.caption("Baseline → proposed manual effort is 4 → 2 minutes per payment. Working-capital funding days are "
                   "5 → 3. Both use 4% funding cost and USD 30 hourly labour. The proposed client incurs USD 500 setup.")
    inputs = replace(inputs, monthly_volume=volume, ticket_minor=round(ticket*100), fx_share_bps=fx,
                     adoption_pct=adoption, bank_implementation_minor=implementation*100,
                     bank_service_month_minor=service*100)
    baseline = replace(baseline, fee_minor=round(base_fee*100), spread_bps=base_spread)
    proposed = replace(proposed, fee_minor=round(new_fee*100), spread_bps=new_spread, buffer_minor=round(new_buffer*100))
    result = compare_economics(inputs, baseline, proposed)
    slots = st.columns(4)
    for col, label, key in zip(slots, ("First-year client savings", "Provider fee and FX revenue", "Provider year-one contribution"),
                               ("client_savings_minor", "provider_revenue_minor", "year_one_contribution_minor")):
        col.metric(label, f"USD {result[key]/100:,.2f}")
    payback = result["payback_months"]
    slots[3].metric("Simple provider payback", f"{payback:.2f} months" if payback is not None else "Unavailable")
    components = [dict(Scenario=name.title(), Component=key.title(), USD=values[key]/100)
                  for name, values in (("baseline", result["baseline"]), ("proposed", result["proposed"]))
                  for key in ("processing", "fx", "reconciliation", "carrying", "setup")]
    st.plotly_chart(px.bar(pd.DataFrame(components), x="Component", y="USD", color="Scenario", barmode="group"),
                    width="stretch")
    st.dataframe([{"Measure": label, "Baseline (USD)": result["baseline"][key]/100,
                   "Proposed (USD)": result["proposed"][key]/100}
                  for key, label in (("working_capital", "Capital tied up"), ("buffer", "Required liquidity buffer"))],
                 hide_index=True)
    scenarios = [{"Adoption (%)": pct, "Provider revenue (USD)": row["provider_revenue_minor"]/100,
                  "Year-one contribution (USD)": row["year_one_contribution_minor"]/100}
                 for pct, row in adoption_cases(inputs, baseline, proposed)]
    st.dataframe(scenarios, hide_index=True)
    st.plotly_chart(px.line(pd.DataFrame(scenarios), x="Adoption (%)", y="Year-one contribution (USD)", markers=True),
                    width="stretch")
    st.subheader("Segment comparison at default assumptions")
    st.dataframe([{"Segment": client.name, "Client savings (USD)": row["client_savings_minor"]/100,
                   "Provider contribution (USD)": row["year_one_contribution_minor"]/100}
                  for client, config in configs.items() for row in (compare_economics(*config),)], hide_index=True)
    st.download_button("Download English business case", business_case(profile, as_of, inputs, baseline, proposed, result),
                       "commercial_opportunity.md", mime="text/markdown")
