# HTTP API

The FastAPI service exposes a local prototype API. OpenAPI/Swagger is available at `/docs`; the schema is at `/openapi.json`. There is no authentication or production rate limiting, so do not expose this service to an untrusted network.

## `GET /health`

Readiness response, for example:

```json
{"status":"ok","service":"VoxEthos"}
```

## `GET /api/v1/capabilities`

Returns the project name and a keyed capability catalog. Statuses distinguish implemented validation, heuristic activity estimates, experimental DSP, acknowledgement-only consent, and capabilities that are not implemented or only planned. Treat this response as the source of truth for current functionality; `VoxEdge` is always `PLANNED_NOT_LOADED` in this prototype.

## `POST /api/v1/analyze`

`multipart/form-data` fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `audio` | file | yes | WAV upload; permitted MIME types are `audio/wav`, `audio/x-wav`, `audio/wave`, or `application/octet-stream`. The payload must still pass WAV validation. |
| `consent_acknowledged` | boolean string | yes | Send `true` after confirming you are authorized to submit the recording for this single request. Omission/default `false` is rejected before the endpoint reads the upload. |

Default engineering limits: PCM16 little-endian WAV, 8–96 kHz, one or two channels, at most 30 seconds, and at most 10 MiB upload bytes. The byte limit can be configured with `VOXETHOS_MAX_AUDIO_BYTES` (1 byte–100 MiB); code-level WAV inspection limits remain in effect. These are resource/format limits, not speech-quality or language validation.

Example:

```bash
curl -sS http://localhost:8000/api/v1/analyze \
  -F 'audio=@sample.wav;type=audio/wav' \
  -F 'consent_acknowledged=true'
```

### Successful response

The response contains:

- `project`, request-scoped `analysis_id`, `created_at`, and `processing_ms`;
- `audio_validation`: WAV format, duration, measured quality values, and reason codes;
- `speech_activity`: threshold-based signal-activity status/intervals and its limitation. `ACTIVITY_PRESENT` means only that measured frames passed configured energy/zero-crossing thresholds; it does not establish that speech is present. The other statuses are `INSUFFICIENT_ACTIVITY`, `NO_ACTIVITY`, and `NOT_EVALUATED`;
- `prosody`: experimental F0/RMS estimates and limitation;
- `capabilities`, `model_plan`, `privacy`, and `consent` status objects;
- `pipeline`: stage names, status, and elapsed milliseconds.

No transcript, model prediction, confidence score, speaker embedding, spoof score, or generated-audio field exists. The response omits the original local filename, raw samples, and audio bytes. `consent.identity_or_rights_verified` and `consent.persistent_record_created` are explicitly false; the acknowledgement is not legal consent management.

### Errors

Expected application errors use this envelope:

```json
{"error":{"code":"CONSENT_REQUIRED","message":"..."}}
```

Common statuses include `403` for missing acknowledgement, `415` for an unsupported upload MIME type, `413` for an oversized upload, `400` for an empty/invalid audio payload, and `422` for malformed request fields. Validation details may be included for a `422`. Clients should use the stable `error.code` where present and must not assume all upstream/proxy errors use this envelope.

## Browser integration

Set `VITE_API_BASE_URL` to an API URL reachable by the user's browser and set `VOXETHOS_FRONTEND_ORIGIN` to the exact frontend origin allowed by CORS (default `http://localhost:5173`). CORS is not authentication. The frontend uses a neutral upload filename; it does not intentionally send the user's local filename.
