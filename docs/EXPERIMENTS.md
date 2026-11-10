# Experiment protocol

There are no reported model benchmarks or corpus results in this branch. The notebooks in `notebooks/` are planning scaffolds that only resolve/print the project path; they do not load datasets, train models, perform inference, or calculate metrics.

Before a future experiment, obtain the dataset and ethics approvals described in [Dataset policy](DATASETS.md) and record a reproducible protocol: source/version and terms, split definition, consent/rights status, language and population coverage, preprocessing steps and code revision, feature/model version, environment, random seeds where relevant, and excluded-data rules. Do not include private examples or credentials in logs or notebooks.

For deterministic DSP validation, define ground truth and measurement tolerances before evaluating, report per-group coverage and uncertainty, and label results as engineering measurements rather than ASR, emotion, identity, spoof, clinical, or forensic performance. For any future model, select task-appropriate metrics before evaluation; publish limitations and failure cases and prevent speaker or recording leakage across splits.

Synthetic WAV smoke fixtures verify the API boundary only. They are not scientific evidence or a substitute for consented, representative Turkish speech evaluation.
