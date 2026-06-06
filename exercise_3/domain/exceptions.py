class ConflictError(Exception):
    """Raised when an optimistic locking version mismatch occurs."""

    pass


class NotFoundError(Exception):
    """Raised when an entity is not found."""

    pass


class EnrichmentError(Exception):
    """Raised when the external threat enrichment service fails."""

    pass
