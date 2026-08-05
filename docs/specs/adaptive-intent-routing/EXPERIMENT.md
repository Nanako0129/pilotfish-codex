# Adaptive intent routing experiment

## Purpose

This is a small qualitative A/B experiment for the initial Q1-Q5 routing
change. It tests whether the adaptive policy reduces perspective tunnel vision:
the assistant should choose an interaction shape that fits the request instead
of treating every prompt as immediate execution or a full Plan.

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
- **Tunnel avoidance:** no premature direct execution, false certainty, or
  exhaustive Plan when the case needs progressive discovery.
- **Boundary preservation:** release/authority approval is retained when
  relevant.
- **Consistency:** repeated runs in the same arm use materially similar modes.

Do not score eloquence, token count, or whether the reviewer prefers the exact
wording. Record representative evidence and disagreements.

The output field `premature_execution` must be interpreted carefully: the
model may use `true` to mean “executing now would be premature” rather than
“this response already started execution”. For this smoke pass, actual behavior
is judged from `first_move`, questions, approval boundary, and whether the
response contains an implementation action. Future runs should rename the
field to `execution_started` to remove this ambiguity.

## Limits

Two repetitions per case are only a smoke experiment. They cannot establish
model-wide rates, statistical significance, cost savings, or live dispatch
quality. Live model calls are deliberately separate from the offline route and
checkpoint evaluator.
