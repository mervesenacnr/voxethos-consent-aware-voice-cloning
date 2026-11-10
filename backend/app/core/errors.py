"""Structured application errors for predictable API failures."""

from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    """An expected client-facing error with a stable machine-readable code."""

    code: str
    message: str
    status_code: int = 400

    def __post_init__(self) -> None:
        # Exception middleware may clear/reassign __traceback__; keep the error mutable.
        Exception.__init__(self, self.message)
