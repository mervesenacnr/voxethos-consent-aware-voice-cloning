# Release checklist

Checked items record completed verification on a candidate tree; the final review must identify its exact commit SHA. An internal feature-branch push is not public release approval.

## Legal and provenance

- [x] The maintainer confirmed authority to license project-authored work and permission to include collaborator contributions under Apache-2.0 (see `NOTICE`).
- [x] Add the complete Apache-2.0 text copied byte-for-byte from the existing public GitHub repository; review `NOTICE` attribution.
- [x] Review the direct backend and locked frontend dependency licenses; document notices and confirm no restricted dataset/model terms or remote font assets are included (`docs/THIRD_PARTY_NOTICES.md`). Backend requirements are pinned directly but are not a full transitive lockfile.
- [x] Review privacy notice, consent wording, and intended-use limitations.

## Security and data

- [x] Gitleaks 8.30.1 scanned current tracked/untracked candidate files and reachable Git history: 0 findings.
- [x] No private/restricted recordings, datasets, model weights, build outputs, or credential artifacts found in indexed files or reachable history; `datasets/` and `models/` contain policy/readme files only.
- [x] Python `pip-audit -r requirements-dev.txt`: 52 packages, 0 vulnerabilities; `npm audit`: 0 vulnerabilities.
- [x] Review CORS, upload bounds, temp-file behavior, logging, and deployment exposure; local CORS preflight and bounded-upload path were verified.

## Quality and claims

- [x] Backend tests pass (46); frontend production build passes.
- [x] Synthetic-WAV API integration smoke passes with consent gate, response schema, and negative consent case verified.
- [x] Browser UI successfully communicates with the API from the configured local origin using a generated WAV fixture; measured result displayed, no browser JS errors.
- [x] Documentation and UI distinguish implemented deterministic DSP from unimplemented/planned VoxEdge ML capabilities.
- [x] No performance, language, emotion, identity, spoof-detection, or voice-generation claims exceed the evidence.

## Release authorization

- [ ] Review exact diff and commit SHA.
- [ ] Push only to the approved Gitea `mervesenacnr/VoxEthos` feature branch; preserve `main`.
- [ ] Publish the GitHub snapshot/PR only after the Gitea branch is verified, the exact public diff passes review, and user approval for that commit is recorded.
