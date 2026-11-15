def __contains__(self, event_type: object) -> bool:
    if not isinstance(event_type, EventType):
        return False
    handlers = self._handlers.get(event_type, [])
    return bool(handlers)