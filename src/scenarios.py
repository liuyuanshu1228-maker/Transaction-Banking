from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    receipt_delay: int = 0
    supplier_delay: int = 0
    expense_minor: int = 0
    expense_account: str = "SG"
    expense_day: int = 7
    fee_bps: int = 0
    spread_bps: int = 0

    def __post_init__(self):
        if min(self.receipt_delay, self.supplier_delay, self.expense_minor, self.fee_bps, self.spread_bps) < 0:
            raise ValueError("Scenario shocks must be nonnegative.")
        if not 1 <= self.expense_day <= 30:
            raise ValueError("Expense day must be within the forecast horizon.")


BASELINE = Scenario()
CONSERVATIVE = Scenario(receipt_delay=5, expense_minor=1_500_000, fee_bps=10, spread_bps=25)
