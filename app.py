from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.controls import DECISIONS, control_cases, record_review, review_queue
from src.data_generation import AS_OF, START
from src.database import DEFAULT_DB, load
from src.forecasting import compare, forecast
from src.market_dashboard import show_market
from src.industry_dashboard import show_industry
from src.payments import payment_metrics, payment_rows
from src.product_dashboard import show_product_strategy
from src.recommendations import client_recommendations
from src.scenarios import CONSERVATIVE, Scenario
from src.settlement import DEMO_PRINCIPAL_MINOR, compare_settlement
from src.treasury import consolidate, daily_balances
from src.virtual_accounts import demo_receipts, reconciliation_summary

PAGES = ("Executive Overview", "Payment Analytics", "Liquidity Forecast", "Scenario Lab",
         "Business Recommendations", "Market Intelligence", "Client & Product Strategy", "Market & Industry Intelligence")
COLORS = ["#087f8c", "#304a80", "#d06735", "#7458a5"]


def usd(minor):
    return f"USD {minor / 100:,.2f}"


@st.cache_data
def portfolio(database_revision):
    return load(DEFAULT_DB if database_revision else None)


def line(rows, column, label, color=None):
    frame = pd.DataFrame(rows)
    frame[column] = frame[column] / 100
    figure = px.line(frame, x="day", y=column, color=color,
                     labels={"day": "Date", column: label}, color_discrete_sequence=COLORS)
    st.plotly_chart(figure, width="stretch")


def metrics(items):
    for col, (label, value) in zip(st.columns(len(items)), items):
        col.metric(label, value)


def show_forecast(base, alternate, label):
    combined = [dict(row, Case=case) for case, rows in (("Expected", base), (label, alternate))
                for row in consolidate(rows)]
    line(combined, "closing_usd_minor", "Group closing cash (USD)", "Case")
    metrics([("Expected day 30", usd(combined[29]["closing_usd_minor"])),
             (f"{label} day 30", usd(combined[-1]["closing_usd_minor"])),
             (f"{label} breach days (account × day)", sum(row["breach"] for row in alternate))])
    breaches = [dict(Date=r["day"], Account=r["account"], Currency=r["currency"],
                     Closing=r["closing_minor"]/100, Buffer=r["buffer_minor"]/100,
                     Shortfall=r["shortfall_minor"]/100) for r in alternate if r["breach"]]
    if breaches:
        st.warning("One or more accounts fall below their operating cash buffer.")
        st.dataframe(breaches, hide_index=True)
    else:
        st.success("All modeled account-day positions meet the operating buffers.")


def show_control_review(receipts, as_of):
    with st.expander("Educational KYC and payment exception review"):
        st.caption("Fictional customer profiles and deterministic alerts. A flag prompts review; it establishes neither wrongdoing nor compliance.")
        journal = st.session_state.setdefault("control_journal", {})
        key = str(as_of)
        events = journal.get(key, [])
        queue = review_queue(control_cases(receipts), events)
        if not queue:
            st.info("No exceptions for this sample.")
            return
        pending = [case["case_id"] for case in queue if case["review_status"] == "Pending Review"]
        if pending:
            case_id = st.selectbox("Pending case", pending, key="control_case")
            decision = st.selectbox("Review decision", DECISIONS, key="control_decision")
            if st.button("Record review", key="record_control_review"):
                journal[key] = record_review(queue, events, case_id, decision)
                st.rerun()
        st.dataframe(queue, hide_index=True)
        if events:
            st.dataframe(events, hide_index=True)
        st.caption("The event journal lasts for the current Streamlit session. Review decisions leave posted cash unchanged.")


def main():
    st.set_page_config(page_title="Corporate Treasury Analytics", layout="wide")
    st.title("Corporate Cash & Cross-Border Payments Analytics")
    page = st.sidebar.radio("Analysis", PAGES)
    disclosure = ("Public market research and synthetic sensitivity"
                  if page in ("Market Intelligence", "Market & Industry Intelligence") else "Synthetic Data — Educational Portfolio Demonstration")
    st.caption(disclosure)
    st.header(page)
    if page == "Client & Product Strategy":
        show_product_strategy()
        return

    revision = DEFAULT_DB.stat().st_mtime_ns if DEFAULT_DB.exists() else None
    data = portfolio(revision)
    as_of = st.sidebar.date_input("Synthetic ledger as-of date", AS_OF, min_value=START, max_value=AS_OF)
    st.caption(f"Synthetic ledger as of {as_of:%d %b %Y} · Group reporting currency USD")
    if page == "Market Intelligence":
        show_market(data, as_of)
        return
    if page == "Market & Industry Intelligence":
        show_industry(data, as_of)
        return
    balances = daily_balances(data, as_of)
    payments = payment_rows(data, as_of)

    if page == PAGES[0]:
        closing = [row for row in balances if row["day"] == str(as_of)]
        period = [row for row in balances if row["day"] > str(as_of - timedelta(days=30))]
        metrics([("Group closing cash", usd(sum(row["closing_usd_minor"] for row in closing))),
                 ("30-day external receipts", usd(sum(row["inflow_usd_minor"] for row in period))),
                 ("30-day settled principal", usd(sum(row["outflow_usd_minor"] for row in period))),
                 ("30-day fees and spread", usd(sum(row["fees_usd_minor"] for row in period)))])
        breached = [row["region"] for row in closing if row["breach"]]
        if breached:
            st.warning("Below buffer: " + ", ".join(breached))
        st.dataframe([{"Region": row["region"], "Currency": row["currency"],
                       "Local balance": row["closing_minor"] / 100, "Local buffer": row["buffer_minor"] / 100,
                       "USD equivalent": row["closing_usd_minor"] / 100} for row in closing], hide_index=True)
        line(consolidate(balances), "closing_usd_minor", "Group closing cash (USD)")
        st.caption("External flow totals exclude intercompany transfers. Historical FX uses each day’s midpoint.")

    elif page == PAGES[1]:
        with st.expander("Virtual account collections"):
            st.caption("Synthetic attribution of the latest Singapore receipts. Cash was already posted to master account SG.")
            mappings, receipts = demo_receipts(data, as_of)
            summary = reconciliation_summary(receipts)
            metrics([("Matched receipt records", f"{summary['match_rate']:.1%}"),
                     ("Reconciled SGD value", f"{summary['value_rate']:.1%}"),
                     ("Duplicate feed records", summary["duplicates"])])
            st.dataframe(mappings, hide_index=True)
            st.dataframe(receipts, hide_index=True, column_config={
                "amount_minor": None,
                "receipt_sgd": st.column_config.NumberColumn("Receipt (SGD)", format="%.2f"),
            })
            st.caption("Record and value rates exclude repeat feed records. Unique unmatched and missing references remain posted but unattributed.")

        show_control_review(receipts, as_of)

        with st.expander("Hypothetical settlement comparison"):
            st.caption("Illustrative input assumptions only. These methods do not represent bank rails or service levels.")
            currency = st.selectbox("Instruction currency", ["SGD", "USD"])
            amount = st.number_input(f"Outgoing principal ({currency})", min_value=1, max_value=10_000_000,
                                     value=DEMO_PRINCIPAL_MINOR // 100, step=1000)
            comparison = compare_settlement(data, as_of, amount * 100, currency, balances=balances)
            st.dataframe([{"Method": row["method"], "Settlement (minutes)": row["delay_min"],
                           "Principal (SGD)": row["principal_minor"] / 100,
                           "Flat fee (SGD)": row["fee_minor"] / 100, "FX spread (bp)": row["spread_bps"],
                           "FX cost (SGD)": row["spread_minor"] / 100,
                           "Opening cash (SGD)": row["opening_minor"] / 100,
                           "Cash after settlement (SGD)": row["ending_minor"] / 100,
                           "Buffer shortfall (SGD)": row["shortfall_minor"] / 100}
                          for row in comparison], hide_index=True)
            events = pd.DataFrame([{"Minute after instruction": event["minute"],
                                    "Available cash (SGD)": event["balance_minor"] / 100, "Method": row["method"]}
                                   for row in comparison for event in row["timeline"]])
            st.plotly_chart(px.line(events, x="Minute after instruction", y="Available cash (SGD)", color="Method",
                                    line_shape="hv", color_discrete_sequence=COLORS), width="stretch")
            st.caption("Both cases use the same SGD opening cash and reporting-date FX midpoint. Cash is debited at settlement. "
                       "The comparison excludes other flows, holds and payment-routing eligibility.")

        begin = finish = as_of
        if as_of != START:
            selection = st.date_input("Instruction date range", (max(START, as_of - timedelta(days=29)), as_of),
                                      min_value=START, max_value=as_of)
            if len(selection) != 2:
                st.info("Select the end of the instruction window.")
                return
            begin, finish = selection
        corridors = sorted({row["corridor"] for row in payments})
        chosen = st.multiselect("Payment corridors", corridors, default=corridors)
        rows = [row for row in payments if str(begin) <= row["instructed"] <= str(finish)
                and row["corridor"] in chosen]
        if not rows:
            st.info("No payment instructions match these filters.")
            return
        m = payment_metrics(rows)
        metrics([("Instructions", m["count"]), ("Instructed volume", usd(m["volume_usd_minor"])),
                 ("Settled volume", usd(m["settled_usd_minor"])), ("All-in cost", usd(m["fees_usd_minor"]))])
        metrics([("Settled", f"{m['settled_rate']:.1%}"), ("Failed", f"{m['failed_rate']:.1%}"),
                 ("Pending", f"{m['pending_rate']:.1%}"),
                 ("Median settlement", f"{m['median_delay']:g} days" if m["median_delay"] is not None else "N/A")])
        frame = pd.DataFrame(rows)
        frame["Instructed USD"] = frame["instructed_usd_minor"] / 100
        grouped = frame.groupby(["corridor", "status"], as_index=False)["Instructed USD"].sum()
        left, right = st.columns(2)
        left.plotly_chart(px.bar(grouped, x="Instructed USD", y="corridor", color="status",
                                 color_discrete_sequence=COLORS), width="stretch")
        currency = frame.groupby("currency", as_index=False)["Instructed USD"].sum()
        right.plotly_chart(px.bar(currency, x="currency", y="Instructed USD",
                                  color_discrete_sequence=COLORS), width="stretch")
        st.dataframe([{"Fee component": label, "USD": m[f"{key}_usd_minor"] / 100}
                      for key, label in (("fixed", "Fixed bank fee"), ("variable", "Variable bank fee"),
                                         ("spread", "FX spread"))], hide_index=True)
        st.dataframe(frame[["id", "corridor", "instructed", "outcome_day", "status",
                            "currency", "Instructed USD", "delay_days"]], hide_index=True)

    else:
        if not any(row['known_on'] <= str(as_of) < row['due_on'] for row in data['scheduled']):
            st.info('No scheduled cash flows were known at this date. The expected projection holds opening cash flat.')
        base = forecast(data, as_of)
        st.caption("30 calendar days · Known scheduled flows only · Matching as-of FX held flat · Unscheduled payments excluded")
        if page == PAGES[2]:
            stress = forecast(data, as_of, CONSERVATIVE)
            st.caption("Conservative case delays receipts by 5 days and adds SGD 15,000 on day 7, 10 bp in fees and 25 bp in FX spread.")
            show_forecast(base, stress, "Conservative")
            account = st.selectbox("Account detail", [row["id"] for row in data["accounts"]])
            detail = [r for r in compare(base, stress) if r["account"] == account]
            st.dataframe(detail, hide_index=True)
            st.caption("Detail fields ending in minor use integer cents in the row currency, except USD fields.")
        elif page == PAGES[3]:
            left, middle, right = st.columns(3)
            receipt = left.slider("Receipt delay (days)", 0, 15, 0)
            supplier = middle.slider("Supplier delay (days)", 0, 15, 0)
            fee = right.slider("Additional fee (bp)", 0, 100, 0)
            spread = right.slider("Additional FX spread (bp)", 0, 150, 0)
            accounts = {row["id"]: row["currency"] for row in data["accounts"]}
            account = left.selectbox("Expense account", list(accounts), format_func=lambda k: f"{k} · {accounts[k]}")
            expense = middle.number_input(f"Unexpected expense ({accounts[account]})", 0, 100_000_000, 0, 1000)
            day = middle.slider("Expense day", 1, 30, 7)
            scenario = Scenario(receipt, supplier, expense * 100, account, day, fee, spread)
            shocked = forecast(data, as_of, scenario)
            show_forecast(base, shocked, "Scenario")
            st.dataframe(compare(base, shocked), hide_index=True)
            st.caption("Compare opening cash, receipts, supplier principal, fees, expense and closing deltas in integer cents.")
        else:
            st.subheader("Executive summary")
            st.caption("Fictional APAC corporate treasury · Decision brief for collections, payments and liquidity")
            _, receipts = demo_receipts(data, as_of)
            rail = compare_settlement(data, as_of, DEMO_PRINCIPAL_MINOR, "SGD", balances=balances)
            result = client_recommendations(payments, forecast(data, as_of, CONSERVATIVE),
                                            reconciliation_summary(receipts), rail)
            for index, row in enumerate(result):
                with st.expander(row["solution"], expanded=index < 2):
                    st.markdown(f"**Client problem** — {row['problem']}")
                    st.markdown(f"**Supporting evidence** — {row['evidence']}")
                    st.markdown(f"**Proposed action** — {row['action']}")
                    st.markdown(f"**Illustrative impact** — {row['impact']}")
                    st.caption(f"Assumptions · {row['assumptions']} Limitations · {row['limitations']}")


if __name__ == "__main__":
    main()
