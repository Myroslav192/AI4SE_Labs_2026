def price(self, items: Sequence[LineItem]) -> Money:
    total_qty = 0
    for it in items:
        # assume LineItem exposes a .quantity attribute
        total_qty += it.quantity
    base_total = self._base.price(items)
    if total_qty < self._threshold or self._percent_off == 0:
        return base_total
    discount_cents = base_total.cents * self._percent_off // 100
    return Money(base_total.cents - discount_cents)