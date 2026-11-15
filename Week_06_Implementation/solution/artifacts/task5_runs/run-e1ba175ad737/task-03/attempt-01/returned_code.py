def stock_report(self) -> Dict[str, int]:
    return {sku: self._ledger.available(sku) for sku in self._ledger}