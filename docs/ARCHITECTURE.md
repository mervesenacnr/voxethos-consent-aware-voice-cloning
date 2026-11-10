# VoxEthos architecture

## Scope

VoxEthos is a research prototype for consent-aware Turkish speech analysis. The current runtime is deterministic DSP and audio validation only. VoxEdge is a planned model boundary; there is no model binary, checkpoint, model inference, transcript, identity embedding, emotion label, spoof score, or voice generation in the request path.

## Request flow

1. FastAPI receives a multipart upload and the per-request consent acknowledgement.
2. `UploadService` checks the declared content type and enforces the configured byte ceiling before passing bytes onward. Original filenames are not used in the analysis response.
3. `Pcm16WavInspector` validates the WAV container, PCM encoding, channels, sample rate, duration, signal quality, and resource limits while decoding bounded samples.
4. `DeterministicSpeechAnalyzer` computes an explicitly heuristic signal-activity estimate from energy and zero crossings; activity is not proof of speech.
5. `ProsodyAnalyzer` computes bounded frame-level RMS and autocorrelation-based F0 estimates. This is experimental signal processing, not a learned prosody or emotion model.
6. The shared `PipelineEngine` records stage lifecycle events. The response includes completed stage names and durations, not raw audio or internal arrays.
7. Samples and payload references are cleared from request context before response serialization. The application has no audio persistence layer.

## Modules

- `app/audio/`: WAV inspection, resource limits, quality metrics, and deterministic activity analysis.
- `app/research/prosody.py`: bounded signal-level pitch/energy feature extraction.
- `app/research/consent.py`: request-level authorization acknowledgement; not identity verification or a durable consent ledger.
- `app/research/capabilities.py`: explicit implementation-status registry used by the API and dashboard.
- `app/core/`: reusable ordered pipeline engine, immutable stage events, and per-request context.
- `app/api/`: health, capability, and analysis routes.
- `frontend/src/features/research/`: upload form and dashboard driven only by API measurements.

## Data handling

The server does not intentionally persist recordings, identifiers, transcripts, embeddings, or generated audio. The upload framework can transiently spool request bodies to temporary storage before endpoint processing; operators must configure ephemeral storage, permissions, cleanup, and log retention accordingly. The response deliberately omits file names, hashes, waveform samples, and model predictions.

## Extension boundaries

Future Turkish ASR, emotion, speaker-representation, privacy-evaluation, consent-record, VoxEdge, and expressive-generation implementations must be separately versioned, consent-gated, auditable, and reflected in the capability registry. A planned module must remain `NOT_IMPLEMENTED`/`PLANNED` until an actual implementation and evaluation are present. Dataset and model provenance/licensing review is a prerequisite; no such assets are bundled.
