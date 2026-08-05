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

## Expanded matrix reference run

The 60-group matrix was run through
[`run_adaptive_intent_experiment.py`](../../../tools/run_adaptive_intent_experiment.py)
on 2026-08-05. This is an offline reference-policy contrast: it makes no model
calls and generates the candidate/control observations from the expected and
explicit control fields in `experiment-matrix.json`.

| Arm | Passing groups | Pass rate | Route fit | First move | Grounding floor | Grounding ceiling | Direction checkpoint | Approval boundary |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Candidate | 60 / 60 | 100.0% | 60 / 60 | 60 / 60 | 60 / 60 | 60 / 60 | 60 / 60 | 60 / 60 |
| Control | 11 / 60 | 18.3% | 18 / 60 | 11 / 60 | 41 / 60 | 60 / 60 | 37 / 60 | 56 / 60 |

By scenario, the candidate passed 20 / 20 groups in each scenario. The control
passed 11 / 20 clear-and-bounded groups, 0 / 20 broad-migration groups, and
0 / 20 open-ended-idea groups. The control's declared or derived failure tags
were: `overplanning` 42, `generic_advice` 20, `missing_checkpoint` 23,
`unsupported_guess` 19, `premature_execution` 7, and
`approval_boundary_loss` 4.

The reference contrast therefore shows the intended direction of the rubric:
the candidate has 49 more passing groups, an 81.7 percentage-point pass-rate
delta, and full coverage of the grounding and checkpoint contract. It does not
show that a live model will produce the candidate behavior. The registered live
cohort below supplies that separate evidence; its claim scope is still limited
to the endpoints reported there.

## Live protocol pilot

The first live smoke ran three registered cases through the Codex CLI `0.146.0`
using fresh ephemeral read-only processes. It completed all transport and
schema checks, but only 1 / 3 cases passed the original composite rubric:

| Case | Route result | Checkpoint result | Composite |
| --- | --- | --- | --- |
| Release, tag, release | Over-escalated to `explore_then_plan` | Not aligned with the initial route contract | FAIL |
| Nuxt → Angular | `explore_then_plan`, with a defensible clarification first move | `INCONCLUSIVE` instead of the registered second-stage outcome | FAIL |
| Music player idea | `co_discover` with focused questions | `CONTINUE` | PASS |

This pilot is not included in the 60-case success claim. It exposed a protocol
problem: the initial route was being scored against a future direction
checkpoint that had no evidence update in the prompt. The registered follow-up
therefore separates route and checkpoint phases, accepts pre-registered
discovery-equivalent first moves for broad or open-ended prompts, and treats
extra approval as an advisory rather than a missing safety boundary. The full
protocol is in [LIVE-EXPERIMENT.md](./LIVE-EXPERIMENT.md).

## Registered live cohort

The formal candidate cohort ran on 2026-08-05 with Codex CLI `0.146.0`, using
60 fresh route calls and 60 fresh checkpoint calls. All 120 calls completed
with valid structured output. The generated raw JSON is intentionally not
versioned; rerun the live protocol in [LIVE-EXPERIMENT.md](./LIVE-EXPERIMENT.md)
when fresh evidence is needed.

| Endpoint | Result | One-sided 95% Wilson lower bound | Interpretation |
| --- | ---: | ---: | --- |
| Initial mode routing | 60 / 60 (100.0%) | 95.7% | High mode-level routing success is supported. |
| Required approval boundary | 60 / 60 (100.0%) | 95.7% | No required approval was lost. |
| Direction checkpoint | 59 / 60 (98.3%) | 92.9% | High checkpoint success is supported. |
| Strict full route contract | 48 / 60 (80.0%) | 70.3% | The composite six-signal claim is not supported. |

Mode routing was 20 / 20 in each scenario: clear bounded work, broad
migration, and open-ended ideas. The 12 strict-contract misses were eight
first-move mismatches and eight grounding-floor mismatches, with overlap in
four cases. There were no route-mode errors and no `approval_boundary_loss`
failures. The single checkpoint miss was `migration-20`; all other checkpoint
cases matched the evidence update.

The defensible claim from this cohort is therefore:

> In this registered 60-case live cohort, the adaptive policy selected the
> correct initial interaction mode in 60 / 60 cases, preserved every required
> approval boundary, and selected the correct direction checkpoint in 59 / 60
> cases.

Do not shorten that to “the routing contract passed 100%”: the strict composite
contract passed 48 / 60. First-move granularity and grounding calibration remain
follow-up work.
