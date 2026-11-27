from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from src.market_intelligence import FX_CURRENCIES, PAYMENTS, POLICY, SNAPSHOT, observations_summary
from src.market_intelligence import published_observations, sensitivity


def show_market(data, as_of):
    st.subheader("Published market research")
    st.caption("Fixed research snapshot. Its publication cutoff is separate from the synthetic ledger date.")
    cutoff = st.date_input("Research publication cutoff", SNAPSHOT, min_value=date(2024, 9, 1), max_value=SNAPSHOT)
    records = published_observations(cutoff)
    series = st.selectbox("Market series", [POLICY, *(f"USD/{c}" for c in FX_CURRENCIES), PAYMENTS])
    selected = [dict(row, value=float(row["value"])) for row in records if row["series"] == series]
    if selected:
        st.plotly_chart(px.line(pd.DataFrame(selected), x="observed_on", y="value", markers=True,
                                labels={"observed_on": "Observation date or report year",
                                        "value": selected[0]["unit"]}), width="stretch")
        st.dataframe(selected, hide_index=True, column_config={"source_url": st.column_config.LinkColumn("Source")})
    else:
        st.info("No selected observations had been published by this cutoff.")
    for name, statement, first, last in observations_summary(records):
        st.markdown(f"**{name}** · {statement} [Start]({first}) · [End]({last})")

    show_macro_sensitivity(data, as_of)


def show_macro_sensitivity(data, as_of):
    st.subheader("Synthetic 30-day macro sensitivity")
    st.caption("Positive FX shocks mean more local currency per USD. The charts above are research context.")
    columns = st.columns(4)
    shifts = {c: col.slider(f"USD/{c} quote shock (bp)", -2000, 2000, 0) for c, col in zip(FX_CURRENCIES, columns)}
    rates = columns[-1].slider("USD interest-rate shock (bp)", -300, 300, 0)
    left, right = st.columns(2)
    delay = left.slider("Working-capital stress: receipt delay (calendar days)", 0, 15, 0)
    spread = right.slider("Additional supplier FX spread (bp)", 0, 150, 0)
    base, stressed, interest = sensitivity(data, as_of, shifts, rates, receipt_delay=delay, spread_shock_bps=spread)
    labels = {"day30_cash_minor": "Day-30 group cash", "peak_funding_minor": "Peak same-day gross funding gap",
              "fx_cost_minor": "30-day supplier FX spread cost"}
    st.dataframe([{"Measure (USD)": label, "Baseline": base[key]/100, "Scenario": stressed[key]/100,
                   "Change": (stressed[key]-base[key])/100} for key, label in labels.items()], hide_index=True)
    st.caption(f"Incremental 30-day net interest: USD {interest/100:,.2f}. Assumed USD 500,000 rate-sensitive cash "
               "and USD 1,000,000 floating debt, full pass-through and ACT/365. Interest posts at day 30. "
               "Gross funding gap sums same-day account shortfalls without netting or interest.")
