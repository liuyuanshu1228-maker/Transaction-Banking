from src.payments import payment_metrics


def recommendations(payments, projections):
    result = []
    worst = max(projections, key=lambda r: r["shortfall_minor"] / r["buffer_minor"] if r["buffer_minor"] else 0)
    if worst["shortfall_minor"]:
        result.append(dict(problem="Projected operating cash below buffer",
                           evidence=f"{worst['account']} on {worst['day']}: {worst['currency']} {worst['shortfall_minor']/100:,.2f} below buffer.",
                           action="Confirm incoming receipts and arrange a contingent intercompany funding transfer.",
                           impact="A same-currency top-up equal to the gap would restore that day's modeled buffer.",
                           assumptions="Scheduled flows and as-of FX rates drive the projection.",
                           limitations="Funding availability, tax, cutoffs and approvals are outside the model."))
    metrics = payment_metrics(payments)
    if metrics["failed_rate"] or metrics["pending_rate"]:
        result.append(dict(problem="Payment exceptions require triage",
                           evidence=f"{metrics['failed_rate']:.1%} failed and {metrics['pending_rate']:.1%} pending across {metrics['count']} instructions.",
                           action="Review failed instructions for data quality and age pending items by corridor.",
                           impact="Prioritizes exception queues by case count and age.",
                           assumptions="Status reflects the selected reporting date.",
                           limitations="Synthetic records do not establish root cause or completion time."))
    if metrics["spread_usd_minor"]:
        result.append(dict(problem="FX spread adds to cross-currency execution cost",
                           evidence=f"Modeled settled FX spread totals USD {metrics['spread_usd_minor']/100:,.2f}.",
                           action="Compare all-in prices by corridor and evaluate batching eligible supplier payments.",
                           impact="Illustrative upper bound on spread exposure addressed by this review.",
                           assumptions="Spread is calculated on settlement-date local principal.",
                           limitations="Actual pricing, batching eligibility and settlement service levels may differ."))
    return result
