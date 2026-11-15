def transition(self, source: OrderStatus, target: OrderStatus) -> OrderStatus:
    if not isinstance(source, OrderStatus):
        raise TypeError("source must be OrderStatus")
    if not isinstance(target, OrderStatus):
        raise TypeError("target must be OrderStatus")
    if self.can_transition(source, target):
        return target
    raise InvalidTransitionError(source, target)