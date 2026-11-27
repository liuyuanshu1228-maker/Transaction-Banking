import pandas as pd
import plotly.express as px
import streamlit as st

from src.client_solutions import PROFILES, assess_client, solutions
from src.client_treasury_proposal import proposal_bytes


def show_client_solutions(data, as_of):
    profile = st.selectbox("Fictional corporate client", PROFILES, format_func=lambda p: p.name)
    st.caption(f"{profile.industry} · Accounts {', '.join(profile.accounts)} · 30-day instruction window")
    st.write(profile.need)
    metrics = assess_client(data, profile, as_of)
    cols = st.columns(4)
    cols[0].metric("Instructions", metrics["count"])
    cols[1].metric("Instructed value", f"USD {metrics['volume_minor']/100:,.2f}")
    cols[2].metric("Failed or pending", metrics["exceptions"])
    cols[3].metric("Peak stress gap", f"USD {metrics['peak_gap_minor']/100:,.2f}")
    delay = metrics["median_delay"]
    st.caption(f"Median settled delay · {delay:g} calendar days" if delay is not None else "Median settled delay unavailable.")
    if metrics["corridors"]:
        st.plotly_chart(px.bar(pd.DataFrame([{"Corridor": k, "Instructed value (USD)": v/100}
                                            for k, v in metrics["corridors"].items()]),
                               x="Instructed value (USD)", y="Corridor"), width="stretch")
    st.plotly_chart(px.line(pd.DataFrame([{"Date": k, "Gross funding gap (USD)": v/100}
                                         for k, v in metrics["funding_path"].items()]),
                            x="Date", y="Gross funding gap (USD)"), width="stretch")
    recommendations = solutions(profile, metrics)
    for item in recommendations:
        with st.expander(item["solution"]):
            for key in ("evidence", "benefit", "assumptions", "dependencies", "risks"):
                st.markdown(f"**{key.title()}** — {item[key]}")
    st.download_button("Download editable client proposal", proposal_bytes(profile, as_of, metrics, recommendations),
                       "client_treasury_proposal.pptx",
                       mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
