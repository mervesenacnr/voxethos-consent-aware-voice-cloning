"""Request-scoped acknowledgement gate; not an identity or legal-consent system."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.errors import AppError


@dataclass(frozen=True, slots=True)
class ConsentAcknowledgement:
    acknowledged: bool
    version: str
    scope: str
    acknowledged_at: datetime
    identity_or_rights_verified: bool = False
    persistent_record_created: bool = False


class ConsentManager:
    """Require an explicit per-upload acknowledgement before reading audio bytes."""

    version = "voxethos-upload-v1"
    scope = "single audio upload for local research-prototype analysis"

    def require_acknowledgement(self, acknowledged: bool) -> ConsentAcknowledgement:
        if acknowledged is not True:
            raise AppError("CONSENT_REQUIRED", "Confirm that you are authorized to submit this audio for this analysis.", 403)
        return ConsentAcknowledgement(
            acknowledged=True,
            version=self.version,
            scope=self.scope,
            acknowledged_at=datetime.now(timezone.utc),
        )
