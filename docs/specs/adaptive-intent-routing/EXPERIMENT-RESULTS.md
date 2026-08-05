# Adaptive intent routing — first smoke results

## Run

- Date: 2026-08-05
- Arms: approved adaptive candidate vs. pre-adaptive binary control
- Cases: the three user examples in `experiment-cases.json`
- Repetitions: one completed run per arm and case; the candidate release case
  was independently repeated while correcting the runner
- Model: same Codex model/profile for both arms
- Tools and writes: disabled; responses only

## Observations

| Case | Expected | Candidate | Control | Qualitative observation |
|---|---|---|---|---|
| Release, tag, release | `execute` plus approval gate | `execute`, minimum grounding, approval retained | `full_plan` | Candidate separates clear route from authority; control over-plans a clear request. |
| Nuxt → Angular | `explore_then_plan` | `explore_then_plan`, bounded discovery, migration questions | `full_plan` | Candidate proposes a reversible reconnaissance slice; control jumps to a complete migration plan. |
| Music player idea | `co_discover` | `co_discover`, focused MVP/platform/source questions | `generic_advice` | Candidate treats the prompt as product discovery; control gives useful questions but lacks an explicit discovery mode and bounded next experiment. |

## Manual result

The candidate matched the expected interaction shape in all three cases and
preserved the release approval boundary. The control did not demonstrate the
same progressive separation: it chose a full Plan for both the clear release
request and the framework migration, and generic advice for the product idea.

This is directional evidence that the adaptive policy changes the thinking
shape in the intended direction and reduces the tunnel of “execute vs. full
Plan”. It is not a statistically significant result and does not establish
live dispatch quality, model-wide rates, cost savings, or correctness for
other prompts.

One output-schema issue was observed: `premature_execution` was interpreted in
some candidate responses as “executing now would be premature”, not “the
response already began execution”. The textual first move and reason were
used for the manual judgment; future runs should use `execution_started`.
