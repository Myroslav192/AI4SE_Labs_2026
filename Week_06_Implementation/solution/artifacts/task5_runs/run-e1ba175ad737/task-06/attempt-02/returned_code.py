def can_afford(self, total: Money) -> bool:
    """Return True if ``balance + total`` does not exceed the credit limit."""
    if not isinstance(total, Money):
        raise TypeError("total must be Money")
    return (self._balance + total) <= self._credit_limit