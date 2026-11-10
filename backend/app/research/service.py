"""Request-scoped WAV analysis orchestrated by the shared pipeline engine."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

import numpy as np

from app.audio.config import AudioInspectionConfig
from app.core.config import settings
from app.audio.errors import AudioInspectionError, SpeechAnalysisError
from app.audio.speech import DeterministicSpeechAnalyzer, SpeechAnalysisConfig
from app.audio.wav import Pcm16WavInspector
from app.core.context import PipelineContext
from app.core.engine import PipelineEngine
from app.core.errors import AppError
from app.core.stages import PipelineStage, RESEARCH_PIPELINE_EXECUTION_ORDER
from app.core.status import PipelineStatus
from app.research.capabilities import capability_snapshot
from app.research.consent import ConsentAcknowledgement, ConsentManager
from app.research.prosody import ProsodyAnalyzer
from app.schemas.audio import AudioMetadata
from app.schemas.research import (
    AudioValidationResponse,
    ConsentResponse,
    PipelineStepResponse,
    PrivacyResponse,
    ProsodyPointResponse,
    ProsodyResponse,
    ResearchAnalysisResponse,
    SpeechActivityResponse,
    SpeechSegmentResponse,
)


class ResearchAnalysisService:
    """Validate and measure PCM16 audio without persistence or model predictions."""

    def __init__(
        self,
        engine: PipelineEngine | None = None,
        inspector: Pcm16WavInspector | None = None,
        speech_analyzer: DeterministicSpeechAnalyzer | None = None,
        prosody_analyzer: ProsodyAnalyzer | None = None,
        consent_manager: ConsentManager | None = None,
    ) -> None:
        self.engine = engine or PipelineEngine()
        self.inspector = inspector or Pcm16WavInspector(
            AudioInspectionConfig(maximum_input_bytes=settings.max_audio_bytes)
        )
        self.speech_analyzer = speech_analyzer or DeterministicSpeechAnalyzer(SpeechAnalysisConfig())
        self.prosody_analyzer = prosody_analyzer or ProsodyAnalyzer()
        self.consent_manager = consent_manager or ConsentManager()

    async def analyze(
        self,
        payload: bytes,
        content_type: str,
        consent: ConsentAcknowledgement,
    ) -> ResearchAnalysisResponse:
        """Run only validated, deterministic signal analysis for one upload."""
        if not payload:
            raise AppError("EMPTY_AUDIO", "Audio payload is empty.", 400)
        started = perf_counter()
        created_at = datetime.now(timezone.utc)
        context = PipelineContext(
            session_id=f"ve_{uuid4().hex[:16]}",
            created_at=created_at,
            raw_payload=payload,
            audio_content_type=content_type,
        )
        # Release the function's second reference; the pipeline owns the bounded request bytes.
        payload = b""
        failure: list[Exception] = []

        async def receive_audio(current: PipelineContext) -> None:
            raw = current.raw_payload
            if raw is None or not raw:
                raise AppError("EMPTY_AUDIO", "Audio payload is empty.", 400)
            current.uploaded_audio = AudioMetadata(
                filename="upload.wav",
                content_type=current.audio_content_type,
                size_bytes=len(raw),
            )

        async def validate_audio(current: PipelineContext) -> None:
            raw = current.raw_payload
            if raw is None:
                raise AppError("EMPTY_AUDIO", "Audio payload is empty.", 400)
            try:
                inspection, samples = self.inspector.inspect_with_samples(raw, lambda decoded, _rate: decoded)
                speech = self.speech_analyzer.analyze(samples, inspection.format.sample_rate_hz)
            except (AudioInspectionError, SpeechAnalysisError) as exc:
                failure.append(exc)
                raise
            current.audio_inspection = inspection
            current.speech_inspection = speech
            current.decoded_samples = samples
            current.raw_payload = None
            current.uploaded_audio = AudioMetadata(
                filename="upload.wav",
                content_type=current.audio_content_type,
                size_bytes=current.uploaded_audio.size_bytes if current.uploaded_audio else 0,
                duration_ms=int(inspection.format.duration_seconds * 1000),
                sample_rate_hz=inspection.format.sample_rate_hz,
                channels=inspection.format.channels,
            )

        async def extract_features(current: PipelineContext) -> None:
            if current.decoded_samples is None or current.audio_inspection is None:
                raise AppError("FEATURE_INPUT_UNAVAILABLE", "Validated audio samples are unavailable.", 500)
            try:
                features = await asyncio.to_thread(
                    self.prosody_analyzer.analyze,
                    np.asarray(current.decoded_samples, dtype=np.float32),
                    current.audio_inspection.format.sample_rate_hz,
                )
            except (TypeError, ValueError, FloatingPointError) as exc:
                failure.append(exc)
                raise
            current.research_features = features
            current.decoded_samples = None

        async def publish_capabilities(_current: PipelineContext) -> None:
            # This pipeline stage publishes the explicit capability boundary, not a model result.
            return None

        result = await self.engine.execute(
            context,
            {
                PipelineStage.VOICE_INPUT: receive_audio,
                PipelineStage.VALIDATION: validate_audio,
                PipelineStage.AUDIO_FEATURE_EXTRACTION: extract_features,
                PipelineStage.RESEARCH_CAPABILITIES: publish_capabilities,
            },
            execution_order=RESEARCH_PIPELINE_EXECUTION_ORDER,
        )
        context.raw_payload = None
        context.decoded_samples = None
        if result.context.status is not PipelineStatus.COMPLETED:
            error = failure[0] if failure else None
            if isinstance(error, (AudioInspectionError, SpeechAnalysisError)):
                raise AppError(error.code, str(error), error.status_code) from error
            if error is not None:
                raise AppError("FEATURE_EXTRACTION_FAILED", str(error), 422) from error
            raise AppError("ANALYSIS_PIPELINE_FAILED", "Audio analysis could not be completed.", 500)

        inspection = context.audio_inspection
        speech = context.speech_inspection
        features = context.research_features
        if inspection is None or speech is None or features is None:
            raise AppError("ANALYSIS_RESULT_INCOMPLETE", "Audio analysis did not produce a complete result.", 500)
        elapsed_ms = max(0, int((perf_counter() - started) * 1000))
        audio_format = inspection.format
        metrics = inspection.metrics
        completed_steps = [
            PipelineStepResponse(stage=event.stage.value, status=event.status.value, duration_ms=event.duration_ms)
            for event in result.events
            if event.status is PipelineStatus.COMPLETED and event.stage is not PipelineStage.COMPLETED
        ]
        return ResearchAnalysisResponse(
            analysis_id=context.session_id,
            created_at=created_at,
            processing_ms=elapsed_ms,
            audio_validation=AudioValidationResponse(
                container=audio_format.container,
                encoding=audio_format.encoding,
                sample_rate_hz=audio_format.sample_rate_hz,
                channels=audio_format.channels,
                frame_count=audio_format.frame_count,
                duration_seconds=audio_format.duration_seconds,
                technical_quality_status=inspection.technical_quality_status.value,
                signal_present=inspection.signal_present,
                peak_amplitude=metrics.peak_amplitude,
                rms_amplitude=metrics.rms_amplitude,
                active_window_ratio=metrics.active_window_ratio,
                silence_window_ratio=metrics.silence_window_ratio,
                clipping_ratio=metrics.clipping_ratio,
                dc_offset=metrics.dc_offset,
                zero_crossing_rate=metrics.zero_crossing_rate,
                reason_codes=list(inspection.reason_codes),
            ),
            speech_activity=SpeechActivityResponse(
                status=speech.status.value,
                estimator="energy_and_zero_crossing_heuristic",
                total_frame_count=speech.total_frame_count,
                active_frame_count=speech.active_frame_count,
                active_ratio=speech.speech_active_ratio,
                estimated_duration_seconds=speech.estimated_speech_duration_seconds,
                segments=[SpeechSegmentResponse(**asdict(segment)) for segment in speech.segments],
                limitation="Signal heuristic only; it does not identify words or verify that the sound is human speech.",
            ),
            prosody=ProsodyResponse(
                status=features.status,
                estimator=features.estimator,
                median_f0_hz=features.median_f0_hz,
                p10_f0_hz=features.p10_f0_hz,
                p90_f0_hz=features.p90_f0_hz,
                voiced_frame_count=features.voiced_frame_count,
                total_frame_count=features.total_frame_count,
                voiced_frame_ratio=features.voiced_frame_ratio,
                pause_count_estimate=features.pause_count_estimate,
                energy_track=[ProsodyPointResponse(**asdict(point)) for point in features.energy_track],
                limitation=features.limitation,
            ),
            capabilities=capability_snapshot(),
            consent=ConsentResponse(
                version=consent.version,
                scope=consent.scope,
                acknowledged_at=consent.acknowledged_at,
                identity_or_rights_verified=False,
                persistent_record_created=False,
                limitation="This is a request-level user attestation, not verified consent from every speaker or legal authorization.",
            ),
            privacy=PrivacyResponse(
                raw_audio_persisted_by_application=False,
                processing_scope="REQUEST_SCOPED",
                formal_privacy_evaluation="NOT_IMPLEMENTED",
                limitation="The application does not persist uploads; the web framework may temporarily spool an incoming upload while parsing the request.",
            ),
            pipeline=completed_steps,
        )
