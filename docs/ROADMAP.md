# Research roadmap

This roadmap separates work present in the Phase 2 prototype from future research. A roadmap entry is not an implemented or validated feature. No model training or large dataset download is included in this phase.

## Present in this branch

- PCM16 WAV parsing and bounded format/resource validation.
- Deterministic signal-quality measurements and energy/zero-crossing signal-activity heuristic (not a speech detector).
- Experimental autocorrelation F0/RMS summaries.
- Consent-acknowledged, request-scoped API and UI, capability reporting, and explicit non-inference state for VoxEdge.
- Synthetic audio fixtures and API/backend tests (no speech corpus included).

## Planned, not implemented

1. **Rights and governance:** retain source/contributor rights and attribution records (project-authored code is licensed under Apache-2.0); define the consent process, threat model, retention/deletion practices, and any research ethics review before collecting real recordings.
2. **Measurement validation:** evaluate the deterministic DSP on appropriately authorized, representative Turkish speech; document measurement error, demographic coverage, limitations, and reproducible test protocols. Do not claim language recognition or emotion understanding.
3. **VoxEdge research:** define the intended task and safety boundaries before selecting any model; review training-data rights and model terms; create a model card and independently reproducible evaluation plan. Do not add inference or weights until these gates pass.
4. **Privacy and security evaluation:** threat-model audio and derived features; review re-identification/inference risks; add abuse controls and privacy testing before any deployment decision.
5. **Production readiness (separate decision):** authentication/authorization, rate limiting, secure temporary storage, observability without audio/PII, retention controls, deployment hardening, and incident response.

Speaker representation, Turkish ASR, emotion recognition, privacy evaluation, durable consent records, spoof detection, and voice generation remain unimplemented. Reconsider each independently; no feature is implied by the VoxEdge name.
