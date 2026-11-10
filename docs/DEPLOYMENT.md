# Local deployment notes

This repository is a development/research prototype and is not production-hardened. Use only on a trusted local machine or an access-controlled test environment. The API currently has no authentication, identity verification, production rate limiting, formal privacy assessment, or durable consent workflow.

## Local services

- Backend: `cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Frontend: `cd frontend && npm run dev -- --host 127.0.0.1`
- Compose: `docker compose -f docker/docker-compose.yml up --build`

Set `VITE_API_BASE_URL` to an address reachable from the browser. Set `VOXETHOS_FRONTEND_ORIGIN` to the exact UI origin. CORS does not authenticate clients. The default backend binds to `0.0.0.0` in application settings; for local-only use, explicitly bind Uvicorn to `127.0.0.1` as above.

## Before any shared or production deployment

This is a separate release decision and requires, at minimum:

- verified source licensing and attribution, dataset/model rights, and privacy notice review;
- authentication/authorization, network isolation, abuse controls/rate limits, TLS, and an explicit origin policy;
- file-size/time/resource limits at reverse proxy and application layers, request timeouts, and safe temporary-upload handling;
- no request-body/audio logging, access-controlled ephemeral temp storage, cleanup verification, backup/log retention, and incident response;
- dependency and container/image scanning, pinned/reproducible build artifacts, vulnerability remediation, and a tested rollback procedure;
- access, privacy, ethics, and security review for intended user groups and use cases.

There is no model runtime or model-artifact pipeline to deploy in this phase. Do not enable public uploads or claim production readiness based solely on the local tests/build.
