from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "templates" / "agents"


class PolicyTests(unittest.TestCase):
    def test_stamp_and_roles_remain_consistent(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertIn(f"<!-- pilotfish-codex v{version} -->", policy)
        for path in AGENTS.glob("*.toml"):
            self.assertEqual(tomllib.loads(path.read_text(encoding="utf-8"))["name"], path.stem)
            self.assertIn(f"`{path.stem}`", policy)

    def test_native_spawn_policy_is_typed_bounded_and_no_override(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        for phrase in (
            "non-empty `message`", "known `agent_type`", "`task_name` matching `[a-z0-9_]+`",
            '`fork_turns = "none"`', '`"1"` through `"3"`', "full-history named-role fork",
            "child `model`, `reasoning_effort`, `service_tier`, or", "never retry with an untyped child",
            "namespace-neutral", "Current receipt validation is post-hoc",
        ):
            self.assertIn(phrase, policy)
        self.assertNotIn("agents.spawn_agent", policy)

    def test_policy_proactively_routes_suitable_work_and_parallel_surfaces(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        policy = " ".join(policy.split())
        for phrase in (
            "active delegation signal",
            "proactively delegate",
            "parallel independent discovery",
            "start them in parallel",
            "material Plan to `plan-verifier` before approval",
            "pre-approval security evidence to `security-reviewer`",
            "fully specified mechanical repetition to `mech-executor`",
            "approved, bounded implementation requiring judgment to `executor`",
            "risk-triggered implementation",
            "fresh `verifier` for one independent refutation pass",
        ):
            self.assertIn(phrase, policy)

    def test_policy_keeps_parent_accountability_and_local_escape_hatches(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        policy = " ".join(policy.split())
        for phrase in (
            "The parent session remains responsible and accountable throughout",
            "reconciles findings",
            "integrates writes",
            "makes final judgment",
            "small, local, already-stable edit",
            "tightly coupled unknown bug",
            "all-or-nothing child-creation boundary",
            "No untyped fallback is permitted",
            "must not silently substitute an untyped child",
            "takes the bounded work locally",
        ):
            self.assertIn(phrase, policy)

    def test_policy_uses_rebuttable_mechanical_default(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        policy = " ".join(policy.split())
        for phrase in (
            "Stable multi-file mechanical repetition",
            "complete one-shot brief",
            "exclusive ownership",
            "per-item acceptance",
            "dispatch exactly one `mech-executor` before the main session edits by default",
            "main session owns per-item triage, exceptions, integration, and acceptance",
            "must not edit the worker-owned scope",
            "specific named blocker before editing",
            "evolving or coupled evidence",
            "ownership or integration conflict",
            "typed worker unavailability",
            "non-positive net benefit",
            "slightly faster is insufficient",
            "default is rebuttable, not unconditional",
        ):
            self.assertIn(phrase, policy)

    def test_policy_uses_net_benefit_and_stable_recurrence_contracts(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        policy = " ".join(policy.split())
        for phrase in (
            "Outside that qualifying mechanical shape, choose delegation by net benefit",
            "lower cost or quota use",
            "preservation of scarce main-session context",
            "true parallelism",
            "isolated ownership",
            "fresh-context independence",
            "context reconstruction, coordination, integration, and verification cost",
            "Recurring or homogeneous work",
            "stable, complete one-shot brief, not a numeric trigger",
            "remaining items must be independent and the same shape",
            "main session retains triage, exceptions, integration, and acceptance",
        ):
            self.assertIn(phrase, policy)

    def test_policy_verifies_at_smallest_coherent_boundary(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        policy = " ".join(policy.split())
        for phrase in (
            "smallest coherent integration boundary",
            "complete claim can be independently refuted",
            "Independent review is risk-triggered",
            "primary user-visible flow",
            "Verify earlier for security changes",
            "serialization or other data boundaries",
            "irreversible operations",
            "work that could block later integration",
            "substantially unchanged Plan",
            "material revision or new evidence",
        ):
            self.assertIn(phrase, policy)

    def test_policy_preserves_unfinished_objective_across_user_input(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        policy = " ".join(policy.split())
        for phrase in (
            "unfinished root objective remains active across turns",
            "user decision replies",
            "steering or corrections",
            "status or explanation requests",
            "pause or resume",
            "new input does not clearly supersede it",
            "Contextually clear replacement intent may replace the objective",
            "no explicit cancellation phrase is required",
            "replacement intent is materially ambiguous",
            "ask one concise clarification instead of silently abandoning it",
            "Before pausing for user input",
            "current phase or slice",
            "pending decision or blocker",
            "exact resume point",
            "Treat a reply that unambiguously resolves that pending decision",
            "continue from the resume point in the same turn",
            "within existing authorization and scope",
            "If the reply is ambiguous, preserve the pause",
            "ask one concise clarification",
            "without treating them as decision resolution",
            "resume only work not gated by the unresolved decision",
            "otherwise remain paused at the recorded resume point",
            "resume the remaining work",
            "unless a pending decision or user-requested pause still gates it",
            "Do not issue a normal final response",
            "active objective remains incomplete",
            "explicitly emit `PAUSED_NEEDS_USER`",
            "If the user explicitly requests a pause",
            "honor it without inventing a blocker or question",
            "active objective, current phase or slice, and exact resume point",
            "pause remains in force through status or explanation requests",
            "until the user explicitly asks to resume",
            "new input clearly supersedes the objective",
            "does not expand approval, security, destructive-action",
            "external-action, or scope boundaries",
        ):
            self.assertIn(phrase, policy)
        self.assertNotIn("only when explicitly cancelled or replaced", policy)
        self.assertNotIn("Treat a plausible reply", policy)
        self.assertNotIn("resume useful in-scope work in the same turn", policy)

    def test_policy_schedules_native_parallel_calls_back_to_back(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        policy = " ".join(policy.split())
        for phrase in (
            "Schedule eligible calls by data dependency",
            "independent typed calls are ready",
            "`spawn_agent` calls back-to-back",
            "exclusive file ownership",
            "continue only on disjoint scope",
            "collect every result before dependent work",
        ):
            self.assertIn(phrase, policy)
        self.assertNotIn("run_in_background", policy)
        self.assertNotIn("worktree", policy)

    def test_verifier_contracts_converge_without_crossing_boundaries(self) -> None:
        policy = (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8")
        plan = (AGENTS / "plan-verifier.toml").read_text(encoding="utf-8")
        outcome = (AGENTS / "verifier.toml").read_text(encoding="utf-8")
        security = (AGENTS / "security-reviewer.toml").read_text(encoding="utf-8")
        normalized_policy = " ".join(policy.split())
        normalized_plan = " ".join(plan.split())

        for phrase in (
            "program envelope",
            "next executable slice",
            "scope, non-goals",
            "acceptance that proves the slice outcome",
            "slice-local budget",
            "stop conditions",
            "Blocker:",
            "Evidence:",
            "Minimum revision:",
            "Acceptance check:",
            "use a fresh `plan-verifier`",
            "two automatic `REVISE` verdicts for the same unit",
            "disposition every blocker as `FIX`, `DEFER`, or `REJECT`",
            "Ask the user only for unresolved P0/P1",
            "not merely to authorize another review round",
            "substantially unchanged Plan",
            "findings and dispositions into the Plan",
        ):
            self.assertIn(phrase, normalized_policy)
        self.assertNotIn("Plan epoch", policy)
        self.assertNotIn("format-recovery", policy)

        self.assertIn("Return exactly one form", normalized_plan)
        self.assertIn("explicit outcome, scope and non-goals", normalized_plan)
        self.assertIn("acceptance that proves the slice outcome", normalized_plan)
        self.assertIn("a slice-local budget", normalized_plan)
        self.assertIn("slice-local stop conditions", normalized_plan)
        self.assertIn("completed security-reviewer findings", normalized_plan)
        self.assertIn("every currently known blocker in the same pass", normalized_plan)
        self.assertIn("Do not use REVISE for P3/P4 advice", normalized_plan)
        self.assertIn("P2 = material bounded or recoverable", normalized_plan)
        self.assertNotIn("CONFIRMED", normalized_plan)
        self.assertNotIn("REFUTED", normalized_plan)
        self.assertNotIn("READY", outcome)
        self.assertNotIn("REVISE", outcome)
        self.assertIn("first plan-verifier review", security)

    def test_policy_owns_outcome_disposition(self) -> None:
        policy = " ".join((ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8").split())
        self.assertIn(
            "Role verdicts are evidence, not implementation or scope authority",
            policy,
        )
        self.assertIn("label it `FIX`, `DEFER`, or `REJECT`", policy)
        self.assertIn(
            "documented deferral or evidence-backed rejection is an addressed finding",
            policy,
        )
        self.assertIn("P0 freezes the affected slice", policy)
        self.assertIn("Fix P1 within approved scope or pause and ask", policy)
        self.assertIn("sharing a repository or path with the change does not make it claim-relevant", policy)
        self.assertIn(
            "A documented regrade may use the verifier's cited evidence",
            policy,
        )
        self.assertIn(
            "stated missing evidence, contract, prerequisite, or environment",
            policy,
        )
        self.assertIn("explicit acceptance and approved scope", policy)

    def test_policy_bounds_verification_recovery_and_user_pause(self) -> None:
        policy = " ".join((ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8").split())
        self.assertRegex(
            policy,
            r"use Codex `request_user_input` only when that tool is exposed in the current mode",
        )
        self.assertRegex(
            policy,
            r"Otherwise end the turn with `PAUSED_NEEDS_USER`, one concise question, "
            r"choices, and a recommendation",
        )
        self.assertRegex(
            policy,
            r"Headless or noninteractive execution emits `PAUSED_NEEDS_USER` and exits",
        )
        self.assertRegex(
            policy,
            r"five-pass budget below is an emergency ceiling for high-risk recovery, "
            r"not a quota.*"
            r"Default recovery is one targeted recheck.*"
            r"High-risk, claim-critical P1/P2 recovery may use at most five meaningful "
            r"fix-reverify passes.*"
            r"rounds 3-5 are emergency recovery",
        )
        self.assertRegex(
            policy,
            r"external evidence or prerequisites.*immediately preceding verifier's "
            r"verdict or output alone is not new evidence.*"
            r"tracked and staged diff.*untracked input paths plus content.*"
            r"input submodule's HEAD plus recursive working-tree content.*"
            r"artifact is explicitly the sole deliverable.*"
            r"Never reverify the same complete identity",
        )
        self.assertIn(
            "headless likely-long run without an explicit mode",
            policy,
        )
        self.assertIn("not a new adjacent-hardening audit", policy)
        self.assertIn("next pass would only search adjacent risk", policy)
        self.assertIn("batch-disposition every current-head finding", policy)
        self.assertRegex(
            policy,
            r"After five unsuccessful or still-blocking passes, mark the slice "
            r"`PAUSED_VERIFICATION`, block its dependents, "
            r"and continue unrelated approved safe slices",
        )

    def test_risk_triggered_plan_review_is_a_mandatory_tool_use_gate(self) -> None:
        policy = " ".join(
            (ROOT / "templates" / "agents-md.orchestration.md").read_text(encoding="utf-8").split()
        )
        for phrase in (
            "mandatory tool-use gate",
            "must call `plan-verifier` before sending any readiness recommendation",
            "Do not return `READY` or `REVISE` from the main session first",
            "typed delegation is unavailable",
            "Review-service circuit breaker",
            "one bounded retry for the same stable unit and typed role",
            "Do not loop",
            "`WAITING_FOR_REVIEW` for plan or security readiness",
            "emit `PAUSED_NEEDS_USER` solely because the service is unavailable",
        ):
            self.assertIn(phrase, policy)


if __name__ == "__main__":
    unittest.main()
