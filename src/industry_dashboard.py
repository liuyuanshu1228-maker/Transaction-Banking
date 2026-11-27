from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from src.industry_research import FIELDS, FRAMEWORK, corporate_snapshot, csv_observations, market_brief
from src.industry_research import research_observations, statistics
from src.market_dashboard import show_macro_sensitivity
from src.market_intelligence import SNAPSHOT


def show_industry(data, as_of):
    st.subheader("Harbor Components · fictional industrial group")
    st.write("Shanghai, Hong Kong and Singapore operations. Manufacturing vendors and freight suppliers serve regional industrial distributors.")
    snapshot = corporate_snapshot(data, as_of)
    st.dataframe([{"Region": r["region"], "Currency": r["currency"], "Local cash": r["closing_minor"]/100,
                   "USD equivalent": r["closing_usd_minor"]/100} for r in snapshot["balances"]], hide_index=True)
    st.caption("Observed synthetic corridors · " + "; ".join(snapshot["corridors"]))
    st.caption(f"Settled USD-denominated payment principal · USD {snapshot['usd_settled_minor']/100:,.2f}")
    for topic, question, url in FRAMEWORK:
        st.markdown(f"**{topic}** — {question} [Reference]({url})")
    mode = st.radio("Research dataset", ["Official snapshot", "Upload CSV", "Synthetic fallback"], horizontal=True)
    cutoff = st.date_input("Industry research publication cutoff", SNAPSHOT, min_value=date(2024, 9, 1))
    if mode == "Upload CSV":
        st.code(",".join(FIELDS), language="text")
        upload = st.file_uploader("Research CSV", type="csv", max_upload_size=1)
        try:
            rows = csv_observations(upload.getvalue().decode("utf-8-sig").splitlines(), cutoff) if upload else []
        except ValueError as error:
            st.error(str(error))
            rows = []
    else:
        rows = research_observations(cutoff, mode)
    if rows:
        frame = pd.DataFrame([dict(row, value=float(row["value"])) for row in rows])
        series = st.selectbox("Industry series", sorted(frame["series"].unique()))
        subset = frame[frame["series"] == series]
        st.plotly_chart(px.line(subset, x="observed_on", y="value", markers=True,
                                labels={"value": subset["unit"].iloc[0]}), width="stretch")
        st.dataframe(frame, hide_index=True, column_config={"source_url": st.column_config.LinkColumn("Source")})
        st.dataframe(statistics(rows), hide_index=True)
    else:
        st.info("No usable research observations at the selected cutoff.")
    st.download_button("Download English market brief", market_brief(rows, snapshot, cutoff, as_of, mode),
                       "industry_research_brief.md", mime="text/markdown")
    show_macro_sensitivity(data, as_of)
