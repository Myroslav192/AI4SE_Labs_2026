def by_status(self, status: OrderStatus) -> Iterator[Order]:
    if not isinstance(status, OrderStatus):
        raise TypeError("status must be OrderStatus")
    for order in list(self._orders):
        if order.status == status:
            yield order