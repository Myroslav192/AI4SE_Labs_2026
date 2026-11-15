def __contains__(self, sku: object) -> bool:
    if not isinstance(sku, str):
        return False
    try:
        normalized = normalize_sku(sku)
    except ValueError:
        return False
    # If SKU is not known to the product repository, it's not contained.
    if normalized not in self._product_repo:
        return False
    # Presence in the ledger is defined by existence of the key in _on_hand,
    # even if the quantity is zero (e.g. after a full commit).
    return normalized in self._on_hand