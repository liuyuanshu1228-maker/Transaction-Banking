from src.payments import payment_metrics


def recommendations(payments, projections):
    result = []
    worst = max(projections, key=lambda r: r["shortfall_minor"] / r["buffer_minor"] if r["buffer_minor"] else 0)
    if worst["shortfall_minor"]:
        result.append(dict(solution="Liquidity buffer and contingent funding",
                           problem="Projected operating cash below buffer",
                           evidence=f"{worst['account']} on {worst['day']}: {worst['currency']} {worst['shortfall_minor']/100:,.2f} below buffer.",
                           action="Confirm incoming receipts and arrange a contingent intercompany funding transfer.",
                           impact="A same-currency top-up equal to the gap would restore that day's modeled buffer.",
                           assumptions="Scheduled flows and as-of FX rates drive the projection.",
                           limitations="Funding availability, tax, cutoffs and approvals are outside the model."))
    metrics = payment_metrics(payments)
    if metrics["failed_rate"] or metrics["pending_rate"]:
        result.append(dict(solution="Payment exception triage",
                           problem="Payment exceptions require triage",
                           evidence=f"{metrics['failed_rate']:.1%} failed and {metrics['pending_rate']:.1%} pending across {metrics['count']} instructions.",
                           action="Review failed instructions for data quality and age pending items by corridor.",
                           impact="Prioritizes exception queues by case count and age.",
                           assumptions="Status reflects the selected reporting date.",
                           limitations="Synthetic records do not establish root cause or completion time."))
    if metrics["spread_usd_minor"]:
        result.append(dict(solution="All-in FX price review",
                           problem="FX spread adds to cross-currency execution cost",
                           evidence=f"Modeled settled FX spread totals USD {metrics['spread_usd_minor']/100:,.2f}.",
                           action="Compare all-in prices by corridor and evaluate batching eligible supplier payments.",
                           impact="Illustrative upper bound on spread exposure addressed by this review.",
                           assumptions="Spread is calculated on settlement-date local principal.",
                           limitations="Actual pricing, batching eligibility and settlement service levels may differ."))
    return result


def client_recommendations(payments, projections, collections, settlement):
    existing = recommendations(payments, projections)
    funding = [row for row in existing if row["solution"] == "Liquidity buffer and contingent funding"]
    payment_actions = [row for row in existing if row not in funding]
    receipts = collections["unique_receipts"]
    collections_actions = []
    if receipts:
        exceptions = receipts - collections["matched"]
        collections_actions.append(dict(
            solution="Virtual account collections",
            problem="Identify the customer behind each master-account receipt.",
            evidence=f"{collections['matched']} of {receipts} unique Singapore receipts matched. "
                     f"SGD {collections['unattributed_minor']/100:,.2f} remains unattributed.",
            action="Assign identifiers by customer and route missing or unknown identifiers to a review queue.",
            impact=f"The sample supports automated attribution for {collections['matched']} receipts "
                   f"and leaves {exceptions} unique receipts for manual review.",
            assumptions="The window contains up to ten already-posted synthetic receipts. Rates exclude duplicate feed records.",
            limitations="Attribution does not validate open invoices or estimate actual processing-time savings.",
        ))
    fast, conventional = sorted(settlement, key=lambda row: row["delay_min"])
    earlier = conventional["delay_min"] - fast["delay_min"]
    rail_action = dict(
        solution="Settlement method selection",
        problem="Balance urgent beneficiary funding against earlier depletion of operating cash.",
        evidence=f"The SGD {fast['principal_minor']/100:,.2f} test payment settles after {fast['delay_min']:,} "
                 f"versus {conventional['delay_min']:,} minutes under the two assumptions. Post-settlement "
                 f"buffer shortfalls are SGD {fast['shortfall_minor']/100:,.2f} and "
                 f"SGD {conventional['shortfall_minor']/100:,.2f}, respectively.",
        action="Reserve fast settlement for eligible time-critical payments and confirm cash headroom first.",
        impact=f"The assumed earlier method advances the modeled cash debit by {earlier:,} minutes.",
        assumptions="Both cases start from the same account close and exclude other flows.",
        limitations="Timing, fees, routing and eligibility are illustrative and require provider confirmation.",
    )
    return [*funding, *collections_actions, rail_action, *payment_actions]
