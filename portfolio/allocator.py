class Allocator:
    def allocate(self, signals: list[str] | None = None) -> dict[str, float]:
        """Return equal-weight allocation across the provided signals.

        Parameters
        ----------
        signals:
            List of signal identifiers (e.g. asset symbols or strategy names).
            When *None* or empty a default single-unit weight is returned.

        Returns
        -------
        dict[str, float]
            Mapping of signal → weight, all weights summing to 1.0.
        """
        if not signals:
            return {"default": 1.0}

        weight = 1.0 / len(signals)
        return {s: weight for s in signals}
