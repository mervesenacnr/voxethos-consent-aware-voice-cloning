"""Common constrained primitives used by versioned API contracts."""

from datetime import datetime
from typing import Annotated

from pydantic import Field

Probability = Annotated[float, Field(ge=0.0, le=1.0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
NonEmptyString = Annotated[str, Field(min_length=1)]
UtcTimestamp = datetime
