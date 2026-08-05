# Adaptive intent routing experiment

## Purpose

This is a qualitative A/B experiment for the Q1-Q5 routing change. It tests
whether the adaptive policy reduces perspective tunnel vision: the assistant
should choose an interaction shape that fits the request instead of treating
every prompt as immediate execution or a full Plan.

The result is behavioral evidence, not a statistical significance claim. The
reviewer checks whether the response invokes the appropriate thinking mode and
preserves existing approval boundaries.

## Arms

- **Candidate:** the approved adaptive policy with `execute`,
  `explore_then_plan`, `co_discover`, impact bands, bounded discovery, and
  AskUserQuestion-style decision cards.
- **Control:** the pre-adaptive binary policy: execute a clear request or write
  a complete Plan before acting, without the three route modes or bounded
  progressive discovery contract.

Both arms use the same model, temperature/session defaults, repository, cases,
and output schema. The first smoke pass uses one completed run per arm and
case; a second repetition is only needed when a case disagrees with the
expected mode or when the first response is not interpretable.

## Expanded matrix

The full design is in
[experiment-matrix.json](./experiment-matrix.json). It contains 60 matched
candidate/control groups, 20 per scenario, or 120 arm observations when both
arms are run:

| Scenario | Groups | Candidate mode | Main tunnel risk |
| --- | ---: | --- | --- |
| Clear and bounded work | 20 | `execute` | Premature execution or unnecessary planning around an approval boundary |
| Broad framework or system migration | 20 | `explore_then_plan` | Treating a high-impact change as a complete Plan before grounding the first slice |
| Open-ended product idea | 20 | `co_discover` | Guessing a product contract, giving generic advice, or expanding without a stopping point |

Each group varies more than the noun in the prompt. The matrix crosses impact,
reversibility, approval boundary, grounding floor, grounding ceiling, and the
expected `direction_checkpoint`. The checkpoint is the second-stage probe after
the first reversible move, so the experiment tests both initial routing and the
ability to change direction when evidence changes.

The four grounding levels are ordered as `none`, `minimum`, `bounded`, and
`deep`. A candidate observation passes only when it stays above the floor and
below the ceiling. This gives the experiment a way to detect both unsupported
guessing and runaway discovery.

The control arm is deliberately explicit rather than a hidden historical
transcript: it represents the pre-adaptive binary policy as either `execute`,
`full_plan`, or `generic_advice`. This makes the first run reproducible and
keeps its conclusion narrow: it validates matrix coverage and the intended
contrast, not live model behavior.

Run the offline reference contrast with:

```bash
python3 tools/run_adaptive_intent_experiment.py
```

The runner emits JSON only, makes no model calls, and performs no repository
writes. The registered candidate live run was audited locally; its generated
raw JSON is intentionally not versioned. Re-run the live protocol in
[LIVE-EXPERIMENT.md](./LIVE-EXPERIMENT.md) when fresh evidence is needed. A
future comparison arm must keep model/session settings constant and record its
reviewer rubric separately from the raw response.

## Cases and expected behavior

1. `release-tag-and-release`
   Prompt: `幫我把專案上版並加 tag 和 release`
   Expected: clear intent and bounded route (`execute`), but preserve the
   release/external-action approval gate. It should not silently publish.
2. `nuxt-to-angular`
   Prompt: `想把 Nuxt 的專案改成 Angular`
   Expected: `explore_then_plan`; identify migration scope, compatibility,
   risks, and first reconnaissance/decision card before bulk implementation.
3. `music-player-start`
   Prompt: `我想做一個音樂播放器，怎麼開始`
   Expected: `co_discover`; ask focused product questions, narrow MVP/target
   user, and propose a smallest useful experiment instead of inventing a full
   implementation contract.

## Human review rubric

Mark each run `PASS`, `PARTIAL`, or `FAIL` for these independent checks:

- **Mode fit:** selected interaction shape matches the case.
- **First move:** response starts with the expected next step, not unrelated
  implementation detail.
- **Grounding floor:** the response checks enough context before making a
  claim; `none` is valid only when the prompt supplies all required facts or
  asks for a context-free answer.
- **Grounding ceiling:** the response stops at the smallest useful boundary
  instead of continuing into unrelated research.
- **Direction checkpoint:** the response chooses `CONTINUE`, `PIVOT`,
  `ROLLBACK`, or `INCONCLUSIVE` consistently with the evidence.
- **Tunnel avoidance:** no premature direct execution, false certainty, or
  exhaustive Plan when the case needs progressive discovery.
- **Boundary preservation:** release/authority approval is retained when
  relevant.
- **Consistency:** repeated runs in the same arm use materially similar modes.

For the matrix runner, score six binary checks: route fit, first move fit,
grounding floor, grounding ceiling, direction checkpoint, and approval
boundary. A group passes only when all six checks pass and no tunnel failure is
observed. For live review, use `PASS`, `PARTIAL`, or `FAIL` for each check and
record representative evidence and disagreements. Do not score eloquence,
token count, or whether the reviewer prefers the exact wording.

The output field `premature_execution` must be interpreted carefully: the
model may use `true` to mean “executing now would be premature” rather than
“this response already started execution”. For this smoke pass, actual behavior
is judged from `first_move`, questions, approval boundary, and whether the
response contains an implementation action. Future runs should rename the
field to `execution_started` to remove this ambiguity.

## Limits

The reference run is not a model run: its candidate arm is generated from the
expected policy fields and its control arm is generated from the explicit
control fields in the matrix. It cannot establish model-wide rates, statistical
significance, cost savings, or live dispatch quality. Live model calls are
deliberately separate from the offline route and checkpoint evaluator and need
their own quota and approval boundary.

The completed 60-case live run remains a directional experiment. It is evidence
about this prompt set and rubric, not a universal claim about every task or
model. Its supported mode-level and checkpoint claims, and its unsupported
strict-composite claim, are recorded in `EXPERIMENT-RESULTS.md`.
