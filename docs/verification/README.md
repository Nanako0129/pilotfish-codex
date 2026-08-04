# Release verification artifacts

Each JSON artifact records the release gate separately from routing benchmarks.
It contains redacted, reproducible outcomes only: no prompts, session IDs,
rollout JSONL, credentials, or raw model output.

`sample_size` is a count of live invocations, not a quality or intelligence
score. Offline-suite counts and documentation lint results establish regression
coverage; the live smoke proves one installed dispatch path at one point in
time. Neither substitutes for the versioned usage-routing cohort.
