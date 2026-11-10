"""Execution status values for the framework-independent pipeline engine."""

from enum import StrEnum


class PipelineStatus(StrEnum):
    """Lifecycle states owned by pipeline execution, not HTTP transport."""

    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
