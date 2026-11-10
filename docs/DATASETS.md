# Dataset policy

## Current state

No speech corpus, private recording, restricted dataset, pre-trained model, or model weight is included or required by this repository. Phase 2 does not download datasets or train models. Tests use generated synthetic signals; they are not real speaker recordings and are not a substitute for corpus validation. The tracked `datasets/` directory contains policy text only.

## Approval required before any future use

Before acquiring or processing a dataset, the research owner must document:

- source, version, license/terms, access restrictions, and permission for the specific research and redistribution use;
- informed consent or another documented legal/ethical basis for every recording, including rights to use voice data and any applicable withdrawal process;
- purpose limitation, language/population coverage, known representation gaps, and an ethics/privacy review where applicable;
- provenance, preprocessing and split protocol, deduplication/leakage controls, and a reproducibility identifier that does not expose personal data;
- retention/deletion schedule, access controls, encryption, secure temporary storage, incident handling, and approved processors.

Dataset access permission is not automatically permission to redistribute recordings, derived samples, embeddings, or model weights. Do not commit any audio, corpus archive, restricted protocol file, credentials, or model artifact. Keep approved local data outside the repository and use documented, access-controlled storage. Do not place private data in notebooks, test fixtures, logs, issue trackers, or screenshots.

## Consent and synthetic fixtures

The API checkbox only records a per-request acknowledgement that the uploader is authorized to submit the file. It does not verify a person's identity, establish consent from every speaker, or create a persistent consent record. Synthetic test WAVs should be generated at test time, remain small and ephemeral, and never be replaced with real speech recordings without the required approvals.
