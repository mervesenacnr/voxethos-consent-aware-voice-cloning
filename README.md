# VoxEthos

**A consent-aware Turkish-speech research prototype.** The current runtime performs bounded PCM16 WAV validation and transparent, deterministic signal-level measurements. It does not understand or verify language, transcribe speech, identify speakers, classify emotion, detect spoofing, or generate voice.

> **Model status:** VoxEdge is planned only. No VoxEdge weights are shipped or loaded; the API does not emit an ML prediction, confidence score, transcript, embedding, or generated audio.

## Implemented in this branch

- Bounded PCM16 little-endian WAV upload validation (container, encoding, sample rate, channels, duration, and configured byte limit).
- Signal-quality measurements: RMS/energy, peak, clipping, DC offset, zero-crossing, silence/activity.
- A deterministic energy/zero-crossing signal-activity estimate; it is not speech detection, ASR, or a trained VAD.
- Experimental autocorrelation-based F0 and RMS summaries; these are not validated Turkish-language, emotion, identity, clinical, or forensic measures.
- FastAPI health, capability-catalog, and consent-acknowledged analysis endpoints.
- React/TypeScript UI that calls the API and displays returned measurements and explicit capability statuses.
- Request-scoped analysis with no application persistence layer. Multipart handling may transiently spool request bodies; see the [privacy policy](docs/PRIVACY.md).

The consent checkbox is a per-request user attestation only. It does not verify identity, the consent of every speaker, or legal rights, and it does not create a durable consent record.

## Not implemented

Turkish ASR, emotion recognition, speaker representation/verification/diarization, formal privacy evaluation, consent-record management, VoxEdge inference, spoof detection, and expressive voice generation are not available. No model training or dataset download is part of this phase. The former legacy inference, storage/repository, report/session, and product-specific UI modules were removed; this prototype must not be represented as providing those functions.

## Run locally

### Backend

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API docs: <http://localhost:8000/docs> · health: <http://localhost:8000/health>

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Open <http://localhost:5173>. `VITE_API_BASE_URL` must point to a backend address reachable from the browser, and the backend's `VOXETHOS_FRONTEND_ORIGIN` must match the UI origin. Backend defaults support this local setup; to use overrides in a backend `.env`, pass `--env-file .env` to Uvicorn or export the variables. The upload form accepts PCM16 WAV and requires a per-request acknowledgement.

### Docker Compose

```bash
docker compose -f docker/docker-compose.yml up --build
```

## API overview

- `GET /health`
- `GET /api/v1/capabilities`
- `POST /api/v1/analyze` — multipart fields `audio` and `consent_acknowledged=true`.

See [API documentation](docs/API.md) for formats, limits, responses, and errors.

## Research, privacy, and operations

This is a local research prototype, not a validated scientific instrument or a production service. It has no authentication, identity verification, durable consent ledger, production rate limiting, or formal privacy/security assessment. Do not upload sensitive recordings or recordings of others unless you have the necessary authorization. Review the [privacy policy](docs/PRIVACY.md), [dataset policy](docs/DATASETS.md), [model plan](docs/MODELS.md), [experiment protocol](docs/EXPERIMENTS.md), [deployment notes](docs/DEPLOYMENT.md), and [release checklist](docs/RELEASE_CHECKLIST.md).

- [Architecture](docs/ARCHITECTURE.md)
- [Research roadmap](docs/ROADMAP.md)

## Development checks

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/pip-audit
cd ../frontend
npm run build
npm audit
```

## License and source attribution

This project is licensed under Apache-2.0; see [`LICENSE`](LICENSE). The maintainer has confirmed authority to license the project-authored contributions and permission to include collaborator contributions in this repository. [`NOTICE`](NOTICE) records historical source lineage and attribution; it does not replace or modify the license.

Third-party dependencies remain under their own licenses. See [`docs/THIRD_PARTY_NOTICES.md`](docs/THIRD_PARTY_NOTICES.md). This repository includes no external speech corpus, model weights, or real voice recordings; the project license grants no rights to future data or model artifacts.
