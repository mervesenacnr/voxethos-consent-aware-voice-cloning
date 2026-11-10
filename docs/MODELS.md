# Model status and future model policy

## Current implementation

No machine-learning model is loaded or called by the API. No checkpoint, weight, model manifest, inference runtime, model prediction, confidence score, transcript, speaker embedding, spoof score, or generated audio is shipped. `VoxEdge` is a planned model family/name only; the capability endpoint reports `PLANNED_NOT_LOADED` and `inference_performed: false`.

The implemented features are deterministic audio validation, signal-quality metrics, an energy/zero-crossing activity heuristic, and experimental autocorrelation-derived F0/RMS. These DSP outputs are not learned predictions, validated Turkish-language results, emotion estimates, identity features, or forensic evidence.

## Future gate before selecting or loading a model

A future model proposal must first define the user-facing task and misuse boundaries, confirm authority to use training/evaluation data, review each model's license/terms and export/redistribution conditions, and complete a privacy/security/ethics assessment. Any approved model must have a versioned manifest containing its source, version, digest, license, input/output contract, preprocessing, supported languages, intended use, known limitations, evaluation protocol, and rollback path.

Do not commit weights to Git. Do not train or download models as part of the current phase. Keep any later artifacts in approved access-controlled storage and expose a capability as implemented only after real inference and reproducible evaluation are verified.
