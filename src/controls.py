"""Educational receipt review using fictional customer verification states."""

PENDING = "Pending Review"
DECISIONS = ("Cleared", "Escalated")
KYC = {"Synthetic Customer A": "Verified in demo", "Synthetic Customer B": "Verification pending",
       "Synthetic Customer C": "Verified in demo"}


def control_cases(receipts):
    cases = []
    for index, row in enumerate(receipts, start=1):
        kyc = KYC.get(row["customer"], "Identity unavailable")
        if row["status"] != "Matched":
            trigger = row["status"]
        elif kyc != "Verified in demo":
            trigger = "Synthetic customer verification incomplete"
        else:
            continue
        cases.append(dict(case_id=f"CASE-{index:02}", bank_reference=row["bank_reference"],
                          trigger=trigger, synthetic_kyc=kyc))
    return cases


def review_queue(cases, events):
    decisions = {event["case_id"]: event["to_status"] for event in events}
    return [dict(case, review_status=decisions.get(case["case_id"], PENDING)) for case in cases]


def record_review(cases, events, case_id, decision):
    status = {row["case_id"]: row["review_status"] for row in review_queue(cases, events)}
    if case_id not in status or decision not in DECISIONS or status[case_id] != PENDING:
        raise ValueError("Only pending cases can be cleared or escalated.")
    return [*events, dict(event=len(events) + 1, case_id=case_id, from_status=PENDING, to_status=decision)]
