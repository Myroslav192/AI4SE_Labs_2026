def __bool__(self) -> bool:
    """Return True when the amount is non-zero."""
    return self._cents != 0