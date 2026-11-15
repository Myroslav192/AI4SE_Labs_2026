def can_afford(self, total: Money) -> bool:
    if not isinstance(total, Money):
        raise TypeError("total must be Money")
    return (self._balance + total) <= self._credit_limit