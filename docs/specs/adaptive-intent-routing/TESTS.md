# TESTS — adaptive-intent-routing

> Acceptance cases for the approved routing policy. Offline route and
> checkpoint fixtures are implemented under this spec directory; they measure
> behavioral policy evidence separately from native dispatch evidence.

## Route selection

- **AC-IR-001:** When a request has a clear bounded outcome, Pilotfish shall
  select `execute`, including when an existing authority gate is required for
  a release or external action; it shall stop at that gate and shall not add
  an unconditional discovery round.
- **AC-IR-002:** When a request has a clear direction but broad migration,
  cross-component, high-impact, or costly-to-reverse scope, Pilotfish shall
  select `explore_then_plan` and shall not admit bulk implementation before the
  required discovery and approval conditions are satisfied.
- **AC-IR-003:** When a request lacks a stable product outcome, target user,
  MVP, or acceptance boundary, Pilotfish shall select `co_discover` and shall
  not treat the initial sentence as a complete implementation contract.
- **AC-IR-004:** When two route interpretations remain materially plausible,
  Pilotfish shall expose the decision and a recommended default rather than
  silently selecting one based only on keywords.
- **AC-IR-005:** When technical uncertainty exists but a safe, reversible probe
  can resolve it without changing product intent, Pilotfish shall keep the
  decision in the agent workflow rather than unnecessarily asking the user.

## Planning and user interaction

- **AC-IR-006:** When a route enters discovery, the internal plan shall retain
  assumptions, evidence, open decisions, budget, and next gate, while the user
  response shall expose a concise decision card containing the current
  interpretation, default, scope, exclusions, and material decisions.
- **AC-IR-007:** When later implementation details cannot affect the next safe
  slice, Pilotfish shall allow them to remain provisional and shall not require
  a complete future Plan before starting that slice.
- **AC-IR-008:** When a discovery budget is exhausted without sufficient
  evidence, Pilotfish shall narrow, pause, or ask for a decision; it shall not
  silently convert uncertainty into write authorization.
- **AC-IR-009:** When the user supplies a short exploratory idea, Pilotfish
  shall be able to propose divide-and-conquer questions and a smallest useful
  experiment without requiring the user to author a complete specification.

## Direction and recovery

- **AC-IR-010:** When a completed slice satisfies its observable outcome,
  non-negotiable constraints, and acceptance evidence, the direction checkpoint
  shall return `CONTINUE`.
- **AC-IR-011:** When the outcome remains valid but the current path or
  assumption is contradicted by evidence, the direction checkpoint shall return
  `PIVOT` and require a bounded re-plan before further expansion.
- **AC-IR-012:** When a required invariant or acceptance condition is broken,
  the direction checkpoint shall return `ROLLBACK`, stop new writes, and
  identify the latest verified good checkpoint.
- **AC-IR-013:** When repeated repairs do not improve the acceptance signal,
  Pilotfish shall treat the condition as direction risk rather than continue
  indefinitely in the current path.
- **AC-IR-014:** When a rollback target is unavailable or an external action is
  irreversible, Pilotfish shall report the recovery limitation and require the
  appropriate containment or user decision; it shall not claim successful
  rollback.

## Dispatch and evidence boundaries

- **AC-IR-015:** When `execute`, `explore_then_plan`, or `co_discover` is
  selected, role choice shall remain within the existing installed role manifest
  and
  native typed dispatch contract.
- **AC-IR-016:** When route evaluation produces a positive result, it shall not
  be described as proof that a live model always makes the same semantic choice.
- **AC-IR-017:** When native dispatch evidence is missing or malformed, the
  dispatch verifier shall fail closed independently of the semantic route
  decision.
- **AC-IR-018:** When a request performs an external, destructive, release, or
  irreversible action, route clarity shall not bypass the existing approval,
  security, or containment gate.

## Cost and calibration

- **AC-IR-019:** When a clear bounded task is evaluated against a vague or broad
  task, the route evaluator shall verify that unnecessary discovery is not
  imposed on the clear task and that premature execution is not selected for
  the vague or broad task.
- **AC-IR-020:** The evaluator shall report latency, token/cost proxy,
  abstention, false-direct-execution, and false-overexploration separately; it
  shall not collapse them into a single uncalibrated quality score.
