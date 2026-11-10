# Privacy notice and data handling

This notice describes the current local VoxEthos prototype, not a production deployment or legal guarantee. Operators must review and adapt it before exposing a service to users.

## What the prototype processes

When a user submits a WAV file, the API receives its bytes and computes format/quality measurements, heuristic signal activity, and experimental RMS/F0 summaries. Activity is not speech detection. The response also contains a request identifier, timestamp, capability statuses, and stage timings. No transcript, speaker identity, embedding, emotion label, model prediction, or generated voice is produced.

The web client keeps a selected `File` in browser memory until it is removed, the page is reset, or the page is closed. It sends the file only when the user starts analysis, and sends a neutral upload filename rather than the local filename. There is no account, analytics, or durable consent-ledger feature in this application.

## Storage and retention

The application has no database or audio persistence layer and does not intentionally retain uploads after request processing. Multipart parsing may transiently spool request bytes to temporary storage before endpoint processing. Hosting platforms, reverse proxies, container runtimes, crash dumps, backups, and operator logs are outside the application's control and may have separate retention behavior. Operators must use access-controlled ephemeral temp storage, avoid recording request bodies, configure log/backup retention, and verify cleanup.

The API has no stored-record deletion endpoint because it has no application-level audio store. This does not guarantee deletion of temporary files or infrastructure logs; those are controlled by the deployment operator.

## Consent and user responsibility

A required checkbox is a single-request authorization acknowledgement. It is not identity verification, proof that every speaker consented, a legal basis determination, or a durable record of consent. Upload only recordings you have the right to submit, and avoid sensitive, confidential, or third-party audio unless the necessary permissions and safeguards are in place.

## Security and sharing

The prototype has no authentication, production rate limiting, formal privacy evaluation, or production security assessment. By default the API allows the configured frontend origin; CORS is not an access-control mechanism. Do not expose the development service to public or untrusted networks. Deployment providers and administrators may be able to access data while it is processed; review their terms and controls before use.

## Changes and questions

Update this notice when processing, storage, hosting, analytics, or third-party services change. For project-specific questions, use the repository's approved maintainer contact process; do not include recordings, tokens, or other personal data in an issue.
