"""Attribute already-posted synthetic receipts to virtual account identifiers."""

MAPPINGS = (
    {"virtual_account": "SYN-VA-101", "master_account": "SG", "customer": "Synthetic Customer A"},
    {"virtual_account": "SYN-VA-102", "master_account": "SG", "customer": "Synthetic Customer B"},
    {"virtual_account": "SYN-VA-103", "master_account": "SG", "customer": "Synthetic Customer C"},
)


def reconcile(receipts, mappings):
    by_id = {row["virtual_account"]: row for row in mappings}
    if len(by_id) != len(mappings):
        raise ValueError("Virtual account identifiers must be unique.")
    seen = set()
    results = []
    for receipt in receipts:
        reference = receipt["bank_reference"]
        virtual = receipt["virtual_account"]
        match = by_id.get(virtual)
        if reference in seen:
            status = "Duplicate bank reference"
        elif not virtual:
            status = "Missing virtual reference"
        elif not match or match["master_account"] != receipt["posted_account"]:
            status = "Unmatched virtual reference"
        else:
            status = "Matched"
        seen.add(reference)
        customer = match["customer"] if status == "Matched" else None
        results.append(dict(receipt, status=status, customer=customer,
                            receipt_sgd=receipt["amount_minor"] / 100))
    return results


def reconciliation_summary(rows):
    unique = [row for row in rows if row["status"] != "Duplicate bank reference"]
    matched = [row for row in unique if row["status"] == "Matched"]
    total = sum(row["amount_minor"] for row in unique)
    value = sum(row["amount_minor"] for row in matched)
    return dict(unique_receipts=len(unique), matched=len(matched), duplicates=len(rows) - len(unique),
                posted_minor=total, matched_minor=value, unattributed_minor=total - value,
                match_rate=len(matched) / len(unique) if unique else 0,
                value_rate=value / total if total else 0)


def demo_receipts(data, as_of):
    history = sorted((row for row in data["cashflows"] if row["account"] == "SG" and row["day"] <= str(as_of)),
                     key=lambda row: (row["day"], row["id"]))[-10:]
    feed = []
    for index, row in enumerate(history):
        virtual = MAPPINGS[index % len(MAPPINGS)]["virtual_account"]
        if index == 3:
            virtual = "SYN-VA-UNKNOWN"
        elif index == 7:
            virtual = None
        feed.append(dict(day=row["day"], bank_reference=f"SYN-R-{row['id']}", posted_account=row["account"],
                         virtual_account=virtual, amount_minor=row["amount_minor"]))
    if len(feed) >= 2:
        feed.append(dict(feed[1]))
    return MAPPINGS, reconcile(feed, MAPPINGS)
