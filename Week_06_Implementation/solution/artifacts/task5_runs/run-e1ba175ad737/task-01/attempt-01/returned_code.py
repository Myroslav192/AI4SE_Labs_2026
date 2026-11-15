    @property
    def is_terminal(self) -> bool:
        return self in (OrderStatus.SHIPPED, OrderStatus.CANCELLED)