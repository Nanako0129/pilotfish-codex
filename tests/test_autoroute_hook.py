"""Security boundaries for the source-owned automatic Plan-review hook."""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))

import pilotfish_autoroute_gate as gate  # noqa: E402


SESSION = "019f-parent-session"
TURN = "019f-current-turn"
ROOT_STARTED_AT = 1_700_000_000
TRIGGER = (
    "Review the material cross-service production credential migration Plan "
    "and determine whether it is ready for user approval."
)


def prompt_input(prompt: str, *, turn_id: str = TURN) -> dict[str, object]:
    return {
        "session_id": SESSION,
        "turn_id": turn_id,
        "transcript_path": None,
        "cwd": "/workspace",
        "hook_event_name": "UserPromptSubmit",
        "model": "gpt-5.6-luna",
        "permission_mode": "never",
        "prompt": prompt,
    }


def stop_input(transcript: Path, *, active: bool = False) -> dict[str, object]:
    return {
        "session_id": SESSION,
        "turn_id": TURN,
        "transcript_path": str(transcript),
        "cwd": "/workspace",
        "hook_event_name": "Stop",
        "model": "gpt-5.6-luna",
        "permission_mode": "never",
        "stop_hook_active": active,
        "last_assistant_message": "private response",
    }


def write_events(path: Path, events: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )


def task_started(*, started_at: int | None = None) -> dict[str, object]:
    payload: dict[str, object] = {"type": "task_started", "turn_id": TURN}
    if started_at is not None:
        payload["started_at"] = started_at
    return {
        "type": "event_msg",
        "payload": payload,
    }


def session_meta() -> dict[str, object]:
    return {"type": "session_meta", "payload": {"id": SESSION}}


def child_events(
    child_id: str,
    *,
    output: str = "READY",
    complete: bool = True,
    complete_turn_id: str | None = None,
    model: str = "gpt-5.6-sol",
    effort: str = "high",
) -> list[dict[str, object]]:
    child_turn = f"{child_id}-turn"
    events: list[dict[str, object]] = [
        {
            "timestamp": "2023-11-14T22:13:21Z",
            "type": "session_meta",
            "payload": {
                "id": child_id,
                "parent_thread_id": SESSION,
                "agent_role": "plan-verifier",
            },
        },
        {
            "type": "turn_context",
            "payload": {"model": model, "effort": effort},
        },
        {
            "type": "event_msg",
            "payload": {
                "type": "task_started",
                "turn_id": child_turn,
                "started_at": ROOT_STARTED_AT + 1,
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": output}],
            },
        },
    ]
    if complete:
        events.append(
            {
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "turn_id": complete_turn_id or child_turn,
                },
            }
        )
    return events


class AutorouteHookTests(unittest.TestCase):
    def test_marker_is_private_redacted_and_category_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()

            self.assertIsNone(gate.handle(prompt_input(TRIGGER), codex_home=home))

            marker_dir = home / gate.MARKER_DIRECTORY
            markers = list(marker_dir.glob("*.json"))
            self.assertEqual(len(markers), 1)
            marker = json.loads(markers[0].read_text(encoding="utf-8"))
            self.assertEqual(
                set(marker),
                {"schema", "session_id", "turn_id", "categories", "attempted"},
            )
            self.assertEqual(marker["session_id"], SESSION)
            self.assertEqual(marker["turn_id"], TURN)
            self.assertEqual(marker["categories"], sorted(marker["categories"]))
            self.assertFalse(marker["attempted"])
            self.assertNotIn("credential migration", markers[0].read_text())
            self.assertEqual(stat.S_IMODE(marker_dir.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(markers[0].stat().st_mode), 0o600)

    def test_ordinary_prompt_clears_stale_session_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            gate.handle(prompt_input(TRIGGER), codex_home=home)

            gate.handle(
                prompt_input("Please fix the spelling in this local comment.", turn_id="next-turn"),
                codex_home=home,
            )

            self.assertEqual(list((home / gate.MARKER_DIRECTORY).glob("*.json")), [])

    def test_message_content_cannot_spoof_structured_child_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            transcript = home / "sessions" / "rollout.jsonl"
            gate.handle(prompt_input(TRIGGER), codex_home=home)
            write_events(
                transcript,
                [
                    session_meta(),
                    task_started(started_at=ROOT_STARTED_AT),
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(
                                        {
                                            "type": "function_call",
                                            "name": "spawn_agent",
                                            "arguments": {"agent_type": "plan-verifier"},
                                            "sub_agent_activity": "started",
                                        }
                                    ),
                                }
                            ],
                        },
                    },
                ],
            )

            self.assertEqual(
                gate.handle(stop_input(transcript), codex_home=home),
                gate.BLOCK_OUTPUT,
            )

    def test_structured_spawn_and_matched_activity_clear_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            transcript = home / "sessions" / "rollout.jsonl"
            gate.handle(prompt_input(TRIGGER), codex_home=home)
            write_events(
                transcript,
                [
                    session_meta(),
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "name": "spawn_agent",
                            "call_id": "stale-call",
                            "arguments": json.dumps({"agent_type": "plan-verifier"}),
                        },
                    },
                    task_started(started_at=ROOT_STARTED_AT),
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "name": "spawn_agent",
                            "call_id": "current-call",
                            "arguments": json.dumps(
                                {
                                    "message": "Review the Plan only.",
                                    "agent_type": "plan-verifier",
                                    "task_name": "automatic_plan_review",
                                    "fork_turns": "none",
                                }
                            ),
                        },
                    },
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "sub_agent_activity",
                            "kind": "started",
                            "event_id": "current-call",
                            "agent_thread_id": "child-thread",
                        },
                    },
                ],
            )
            write_events(
                home / "sessions" / "child.jsonl",
                child_events("child-thread"),
            )

            self.assertIsNone(gate.handle(stop_input(transcript), codex_home=home))
            self.assertEqual(list((home / gate.MARKER_DIRECTORY).glob("*.json")), [])

    def test_unproven_review_blocks_once_then_clears(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            transcript = home / "sessions" / "rollout.jsonl"
            gate.handle(prompt_input(TRIGGER), codex_home=home)
            write_events(transcript, [session_meta(), task_started()])

            self.assertEqual(
                gate.handle(stop_input(transcript), codex_home=home),
                gate.BLOCK_OUTPUT,
            )
            marker = next((home / gate.MARKER_DIRECTORY).glob("*.json"))
            self.assertTrue(json.loads(marker.read_text())["attempted"])
            self.assertIsNone(gate.handle(stop_input(transcript), codex_home=home))
            self.assertFalse(marker.exists())

    def test_complete_intrinsically_linked_child_suppresses_duplicate_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            transcript = home / "sessions" / "2026" / "08" / "root.jsonl"
            child = home / "sessions" / "2026" / "08" / "child.jsonl"
            gate.handle(prompt_input(TRIGGER), codex_home=home)
            write_events(
                transcript,
                [session_meta(), task_started(started_at=ROOT_STARTED_AT)],
            )
            write_events(child, child_events("linked-child"))

            self.assertIsNone(gate.handle(stop_input(transcript), codex_home=home))
            self.assertEqual(list((home / gate.MARKER_DIRECTORY).glob("*.json")), [])

    def test_incomplete_intrinsically_linked_child_keeps_single_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            transcript = home / "sessions" / "root.jsonl"
            child = home / "sessions" / "child.jsonl"
            gate.handle(prompt_input(TRIGGER), codex_home=home)
            write_events(
                transcript,
                [session_meta(), task_started(started_at=ROOT_STARTED_AT)],
            )
            write_events(child, child_events("incomplete-child", complete=False))

            self.assertEqual(
                gate.handle(stop_input(transcript), codex_home=home),
                gate.BLOCK_OUTPUT,
            )

    def test_wrong_completion_turn_keeps_single_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            transcript = home / "sessions" / "root.jsonl"
            gate.handle(prompt_input(TRIGGER), codex_home=home)
            write_events(
                transcript,
                [session_meta(), task_started(started_at=ROOT_STARTED_AT)],
            )
            write_events(
                home / "sessions" / "child.jsonl",
                child_events("wrong-turn-child", complete_turn_id="another-turn"),
            )

            self.assertEqual(
                gate.handle(stop_input(transcript), codex_home=home),
                gate.BLOCK_OUTPUT,
            )

    def test_direct_chain_wrong_binding_or_incomplete_child_retries(self) -> None:
        cases = (
            {"model": "gpt-5.6-luna"},
            {"complete": False},
        )
        for child_options in cases:
            with self.subTest(child_options=child_options), tempfile.TemporaryDirectory() as directory:
                home = Path(directory) / "codex-home"
                home.mkdir()
                transcript = home / "sessions" / "root.jsonl"
                gate.handle(prompt_input(TRIGGER), codex_home=home)
                write_events(
                    transcript,
                    [
                        session_meta(),
                        task_started(started_at=ROOT_STARTED_AT),
                        {
                            "type": "response_item",
                            "payload": {
                                "type": "function_call",
                                "name": "spawn_agent",
                                "call_id": "direct-call",
                                "arguments": json.dumps(
                                    {
                                        "message": "Review the Plan only.",
                                        "agent_type": "plan-verifier",
                                        "task_name": "automatic_plan_review",
                                        "fork_turns": "none",
                                    }
                                ),
                            },
                        },
                        {
                            "type": "event_msg",
                            "payload": {
                                "type": "sub_agent_activity",
                                "kind": "started",
                                "event_id": "direct-call",
                                "agent_thread_id": "direct-child",
                            },
                        },
                    ],
                )
                write_events(
                    home / "sessions" / "child.jsonl",
                    child_events("direct-child", **child_options),
                )

                self.assertEqual(
                    gate.handle(stop_input(transcript), codex_home=home),
                    gate.BLOCK_OUTPUT,
                )

    def test_two_intrinsically_linked_children_are_ambiguous_and_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            transcript = home / "sessions" / "root.jsonl"
            gate.handle(prompt_input(TRIGGER), codex_home=home)
            write_events(
                transcript,
                [session_meta(), task_started(started_at=ROOT_STARTED_AT)],
            )
            write_events(home / "sessions" / "child-a.jsonl", child_events("child-a"))
            write_events(home / "sessions" / "child-b.jsonl", child_events("child-b"))

            self.assertEqual(
                gate.handle(stop_input(transcript), codex_home=home),
                gate.BLOCK_OUTPUT,
            )

    def test_root_message_content_cannot_spoof_intrinsic_child_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex-home"
            home.mkdir()
            transcript = home / "sessions" / "root.jsonl"
            gate.handle(prompt_input(TRIGGER), codex_home=home)
            write_events(
                transcript,
                [
                    session_meta(),
                    task_started(started_at=ROOT_STARTED_AT),
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(child_events("spoofed-child")),
                                }
                            ],
                        },
                    },
                ],
            )

            self.assertEqual(
                gate.handle(stop_input(transcript), codex_home=home),
                gate.BLOCK_OUTPUT,
            )

    def test_untrusted_transcripts_are_terminal_misses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "codex-home"
            sessions = home / "sessions"
            sessions.mkdir(parents=True)
            outside = root / "outside.jsonl"
            write_events(outside, [task_started()])
            symlink = sessions / "symlink.jsonl"
            os.symlink(outside, symlink)
            oversize = sessions / "oversize.jsonl"
            oversize.write_bytes(b"x" * (gate.MAX_TRANSCRIPT_BYTES + 1))

            for transcript in (outside, symlink, oversize):
                with self.subTest(transcript=transcript.name):
                    gate.handle(prompt_input(TRIGGER), codex_home=home)
                    self.assertIsNone(
                        gate.handle(stop_input(transcript), codex_home=home)
                    )
                    self.assertEqual(
                        list((home / gate.MARKER_DIRECTORY).glob("*.json")),
                        [],
                    )


if __name__ == "__main__":
    unittest.main()
