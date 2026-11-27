from datetime import date, timedelta
from random import Random

START = date(2025, 1, 1)
HISTORY_DAYS = 210
AS_OF = START + timedelta(days=HISTORY_DAYS - 1)
DEFAULT_SEED = 42


def generate(seed=DEFAULT_SEED):
    rng = Random(seed)
    accounts = [
        ("HK", "Hong Kong", "HKD", 210_000_000, 120_000_000),
        ("CN", "Shanghai", "CNY", 150_000_000, 90_000_000),
        ("SG", "Singapore", "SGD", 33_000_000, 90_000_000),
    ]
    fx, payments, cashflows, scheduled, transfers = [], [], [], [], []
    for offset in range(HISTORY_DAYS):
        day = START + timedelta(days=offset)
        for currency, rate in (("USD", 1000000), ("HKD", 128000), ("CNY", 139000), ("SGD", 745000)):
            fx.append((day.isoformat(), currency, rate if currency == "USD" else rate + rng.randint(-1800, 1800)))
        for account, region, currency, _, _ in accounts:
            foreign = rng.random() < 0.58
            status = rng.choices(["settled", "failed", "pending"], [94, 3, 3])[0]
            outcome = day + timedelta(days=rng.randint(0, 4) if foreign else rng.randint(0, 1))
            if outcome > AS_OF or status == "pending":
                status, outcome = "pending", None
            destination = rng.choice(["United States", "Germany", "Australia"]) if foreign else region
            instruction_currency = "USD" if foreign else currency
            amount = rng.randint(500_000, 1_650_000) if foreign else rng.randint(5_000_000, 10_000_000)
            payments.append((len(payments) + 1, account, day.isoformat(), instruction_currency,
                             amount, destination, status, outcome.isoformat() if outcome else None))
            cashflows.append((len(cashflows) + 1, account, day.isoformat(), rng.randint(8_300_000, 18_000_000)
                              if currency != "SGD" else rng.randint(4_800_000, 10_000_000) * 53 // 100))
        if offset % 21 == 5:
            transfers.append((len(transfers) + 1, day.isoformat(), "HK", "SG", 3_000_000))

    for offset in range(1, 36):
        day = AS_OF + timedelta(days=offset)
        for account, _, currency, _, _ in accounts:
            known = AS_OF - timedelta(days=rng.randint(0, 20))
            receipt = rng.randint(7_000_000, 17_000_000) if currency != "SGD" else rng.randint(4_000_000, 12_000_000)
            scheduled.append((len(scheduled) + 1, account, known.isoformat(), day.isoformat(),
                              "receipt", currency, receipt))
            supplier_currency = "USD" if offset % 3 == 0 else currency
            supplier = rng.randint(900_000, 2_800_000) if supplier_currency == "USD" else rng.randint(6_000_000, 15_000_000)
            scheduled.append((len(scheduled) + 1, account, known.isoformat(), day.isoformat(),
                              "supplier", supplier_currency, supplier))
    return dict(accounts=accounts, fx=fx, payments=payments, cashflows=cashflows,
                scheduled=scheduled, transfers=transfers)
