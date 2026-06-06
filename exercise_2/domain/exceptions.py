class ConflictError(Exception):
    """Raised when an optimistic locking version mismatch occurs."""

    pass


class NotFoundError(Exception):
    """Raised when an entity is not found."""

    pass
