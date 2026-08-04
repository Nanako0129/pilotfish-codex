#!/usr/bin/env python3
"""Enforce one redacted retry for risk-triggered pre-approval Plan review."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA = 1
MARKER_DIRECTORY = ".pilotfish-autoroute-gate"
MAX_HOOK_INPUT_BYTES = 1_048_576
MAX_PROMPT_CHARS = 65_536
MAX_MARKER_BYTES = 4_096
MAX_TRANSCRIPT_BYTES = 16 * 1_048_576
MAX_SCAN_ENTRIES = 32_768
MAX_SCAN_CANDIDATES = 256
MAX_SCAN_BYTES = 64 * 1_048_576
MAX_SCAN_DEPTH = 8
SCAN_MTIME_SLOP_SECONDS = 5
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
TASK_NAME_RE = re.compile(r"^[a-z0-9_]+$")

BLOCK_REASON = (
    "Required independent Plan review is missing. Call the typed "
    "plan-verifier role now, wait for its result, and then continue."
)
BLOCK_OUTPUT = {"decision": "block", "reason": BLOCK_REASON}

_PLAN_RE = re.compile(
    r"(?:\b(?:plan|planning|pre-approval|approval|approve|readiness|proposal)\b|"
    r"計畫|規劃|方案|核准|批准|審核)",
    re.IGNORECASE,
)
_CATEGORY_PATTERNS = {
    "data": re.compile(
        r"\b(?:data|database|schema|serialization|migration|pii|personal data|"
        r"backup|restore)\b|資料|數據|資料庫|結構描述|序列化|遷移|移轉",
        re.IGNORECASE,
    ),
    "external": re.compile(
        r"\b(?:external|third[- ]party|remote system|send (?:email|message)|"
        r"external mutation|external action)\b|外部系統|第三方|對外",
        re.IGNORECASE,
    ),
    "irreversible": re.compile(
        r"\b(?:destructive|irreversible|delete|drop|truncate|purge|overwrite|"
        r"force[- ]push)\b|破壞性|不可逆|刪除|清除|覆寫",
        re.IGNORECASE,
    ),
    "release": re.compile(
        r"\b(?:release|deploy|deployment|production|rollout|publish|shipping)\b|"
        r"發布|發佈|部署|上線|正式環境",
        re.IGNORECASE,
    ),
    "security": re.compile(
        r"\b(?:security|secure|trust boundary|authentication|authorization|"
        r"authn|authz|credential|secret|permission|iam|cryptography|crypto|"
        r"encryption|vulnerabilit(?:y|ies))\b|安全|信任邊界|驗證|授權|"
        r"憑證|密鑰|祕密|秘密|權限|加密|漏洞",
        re.IGNORECASE,
    ),
}
_MARKER_KEYS = frozenset(
    {"schema", "session_id", "turn_id", "categories", "attempted"}
)


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(IDENTIFIER_RE.fullmatch(value))


def classify_prompt(prompt: object) -> tuple[str, ...]:
    """Return only stable policy category labels; never retain prompt text."""
    if not isinstance(prompt, str) or len(prompt) > MAX_PROMPT_CHARS:
        return ()
    if _PLAN_RE.search(prompt) is None:
        return ()
    return tuple(
        sorted(
            category
            for category, pattern in _CATEGORY_PATTERNS.items()
            if pattern.search(prompt) is not None
        )
    )


def _marker_directory(codex_home: Path, *, create: bool) -> Path | None:
    directory = codex_home / MARKER_DIRECTORY
    try:
        home = codex_home.resolve(strict=True)
        if not home.is_dir():
            return None
        if create:
            directory.mkdir(mode=0o700, exist_ok=True)
        info = directory.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            return None
        if not directory.resolve(strict=True).is_relative_to(home):
            return None
        if create:
            os.chmod(directory, 0o700)
        elif stat.S_IMODE(info.st_mode) != 0o700:
            return None
        return directory
    except OSError:
        return None


def _marker_path(codex_home: Path, session_id: str, *, create: bool) -> Path | None:
    directory = _marker_directory(codex_home, create=create)
    if directory is None:
        return None
    filename = hashlib.sha256(session_id.encode("utf-8")).hexdigest() + ".json"
    return directory / filename


def _remove_marker(codex_home: Path, session_id: str) -> None:
    path = _marker_path(codex_home, session_id, create=False)
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _atomic_marker_write(codex_home: Path, marker: dict[str, Any]) -> bool:
    session_id = marker["session_id"]
    path = _marker_path(codex_home, session_id, create=True)
    if path is None:
        return False
    payload = json.dumps(marker, separators=(",", ":"), sort_keys=True).encode() + b"\n"
    if len(payload) > MAX_MARKER_BYTES:
        return False
    descriptor: int | None = None
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=".marker-", dir=path.parent)
        temporary = Path(name)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists() and path.is_symlink():
            return False
        os.replace(temporary, path)
        temporary = None
        return True
    except OSError:
        return False
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _read_bounded(descriptor: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    remaining = limit + 1
    while remaining:
        chunk = os.read(descriptor, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _load_marker(codex_home: Path, session_id: str) -> dict[str, Any] | None:
    path = _marker_path(codex_home, session_id, create=False)
    if path is None:
        return None
    try:
        info = path.lstat()
        if (
            stat.S_ISLNK(info.st_mode)
            or not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_size > MAX_MARKER_BYTES
        ):
            return None
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                return None
            payload = _read_bounded(descriptor, MAX_MARKER_BYTES)
        finally:
            os.close(descriptor)
        if len(payload) > MAX_MARKER_BYTES:
            return None
        marker = json.loads(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(marker, dict) or set(marker) != _MARKER_KEYS:
        return None
    categories = marker.get("categories")
    if (
        marker.get("schema") != SCHEMA
        or marker.get("session_id") != session_id
        or not _valid_identifier(marker.get("turn_id"))
        or not isinstance(marker.get("attempted"), bool)
        or not isinstance(categories, list)
        or categories != sorted(set(categories))
        or any(category not in _CATEGORY_PATTERNS for category in categories)
        or not categories
    ):
        return None
    return marker


def _stat_fingerprint(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_transcript(
    codex_home: Path,
    transcript_value: object,
) -> list[dict[str, Any]] | None:
    if not isinstance(transcript_value, str) or not transcript_value:
        return None
    transcript = Path(transcript_value)
    if not transcript.is_absolute():
        return None
    sessions = codex_home / "sessions"
    descriptor: int | None = None
    try:
        home = codex_home.resolve(strict=True)
        sessions_info = sessions.lstat()
        if stat.S_ISLNK(sessions_info.st_mode) or not stat.S_ISDIR(sessions_info.st_mode):
            return None
        sessions_real = sessions.resolve(strict=True)
        if not sessions_real.is_relative_to(home):
            return None
        before = transcript.lstat()
        if (
            stat.S_ISLNK(before.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or before.st_size > MAX_TRANSCRIPT_BYTES
        ):
            return None
        transcript.resolve(strict=True).relative_to(sessions_real)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(transcript, flags)
        opened = os.fstat(descriptor)
        if _stat_fingerprint(opened) != _stat_fingerprint(before):
            return None
        payload = _read_bounded(descriptor, MAX_TRANSCRIPT_BYTES)
        after_fd = os.fstat(descriptor)
        after_path = transcript.lstat()
        if (
            len(payload) > MAX_TRANSCRIPT_BYTES
            or _stat_fingerprint(after_fd) != _stat_fingerprint(before)
            or _stat_fingerprint(after_path) != _stat_fingerprint(before)
        ):
            return None
    except (OSError, ValueError):
        return None
    finally:
        if descriptor is not None:
            os.close(descriptor)
    try:
        lines = payload.decode("utf-8").splitlines()
        if not lines:
            return None
        events = [json.loads(line) for line in lines]
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not all(isinstance(event, dict) for event in events):
        return None
    return events


def _epoch(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    epoch = float(value)
    return epoch if math.isfinite(epoch) and epoch >= 0 else None


def _timestamp_epoch(value: object) -> float | None:
    if not isinstance(value, str) or not value or len(value) > 64:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    epoch = parsed.timestamp()
    return epoch if math.isfinite(epoch) and epoch >= 0 else None


def _root_task_started_epoch(
    events: list[dict[str, Any]],
    *,
    session_id: str,
    turn_id: str,
) -> float | None:
    sessions = [
        event["payload"]
        for event in events
        if event.get("type") == "session_meta"
        and isinstance(event.get("payload"), dict)
    ]
    if len(sessions) != 1 or sessions[0].get("id") != session_id:
        return None
    boundaries = [
        event["payload"]
        for event in events
        if event.get("type") == "event_msg"
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("type") == "task_started"
    ]
    if not boundaries or boundaries[-1].get("turn_id") != turn_id:
        return None
    return _epoch(boundaries[-1].get("started_at"))


def _terminal_review_output(text: object) -> bool:
    if text == "READY":
        return True
    if not isinstance(text, str) or not text.startswith("REVISE\n"):
        return False
    if text != text.strip():
        return False
    lines = [line for line in text.splitlines()[1:] if line]
    fields = ("Blocker:", "Evidence:", "Minimum revision:", "Acceptance check:")
    if not lines or len(lines) % len(fields):
        return False
    for index, line in enumerate(lines):
        field = fields[index % len(fields)]
        if not line.startswith(field) or not line[len(field) :].strip():
            return False
    return True


def _linked_child_status(
    events: list[dict[str, Any]],
    *,
    parent_id: str,
    root_started_at: float,
    allowed_child_id: str | None,
) -> int:
    """Return 1 for valid, 0 for unrelated, and -1 for invalid candidate."""
    session_events = [event for event in events if event.get("type") == "session_meta"]
    linked = [
        event
        for event in session_events
        if isinstance(event.get("payload"), dict)
        and event["payload"].get("parent_thread_id") == parent_id
    ]
    if not linked:
        return 0
    if len(session_events) != 1 or len(linked) != 1:
        return -1
    session_event = linked[0]
    session = session_event["payload"]
    role = session.get("agent_role")
    if role != "plan-verifier":
        return 0 if isinstance(role, str) and role else -1
    child_id = session.get("id")
    if not _valid_identifier(child_id) or child_id == parent_id:
        return -1
    if allowed_child_id is not None and child_id != allowed_child_id:
        return 0
    session_started_at = _timestamp_epoch(session_event.get("timestamp"))
    if (
        session_started_at is None
        or session_started_at < root_started_at
    ):
        return -1
    for event in events:
        if event.get("type") in {
            "session_meta",
            "turn_context",
            "event_msg",
            "response_item",
        } and not isinstance(event.get("payload"), dict):
            return -1
    contexts = [event["payload"] for event in events if event.get("type") == "turn_context"]
    if len(contexts) != 1 or contexts[0].get("model") != "gpt-5.6-sol" or contexts[0].get("effort") != "high":
        return -1
    if any(
        event.get("type") == "event_msg"
        and event["payload"].get("type")
        in {"error", "task_failed", "turn_aborted", "turn_cancelled"}
        for event in events
    ):
        return -1
    starts = [
        (index, event["payload"])
        for index, event in enumerate(events)
        if event.get("type") == "event_msg"
        and event["payload"].get("type") == "task_started"
    ]
    completes = [
        (index, event["payload"])
        for index, event in enumerate(events)
        if event.get("type") == "event_msg"
        and event["payload"].get("type") == "task_complete"
    ]
    if len(starts) != 1 or len(completes) != 1:
        return -1
    start_index, start = starts[0]
    child_started_at = _epoch(start.get("started_at"))
    if (
        not _valid_identifier(start.get("turn_id"))
        or child_started_at is None
        or child_started_at < root_started_at
        or completes[0][0] <= start_index
        or completes[0][1].get("turn_id") != start.get("turn_id")
    ):
        return -1
    messages = [
        (index, event["payload"])
        for index, event in enumerate(events)
        if event.get("type") == "response_item"
        and event["payload"].get("type") == "message"
        and event["payload"].get("role") == "assistant"
    ]
    if len(messages) != 1 or not start_index < messages[0][0] < completes[0][0]:
        return -1
    content = messages[0][1].get("content")
    if (
        not isinstance(content, list)
        or len(content) != 1
        or not isinstance(content[0], dict)
        or content[0].get("type") != "output_text"
        or not _terminal_review_output(content[0].get("text"))
    ):
        return -1
    return 1


class _ScanRejected(Exception):
    pass


def _decode_jsonl(payload: bytes) -> list[dict[str, Any]]:
    try:
        lines = payload.decode("utf-8").splitlines()
        if not lines:
            raise _ScanRejected
        events = [json.loads(line) for line in lines]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _ScanRejected from exc
    if not all(isinstance(event, dict) for event in events):
        raise _ScanRejected
    return events


def _read_scanned_jsonl(
    directory_fd: int,
    name: str,
    expected: os.stat_result,
) -> list[dict[str, Any]]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(name, flags, dir_fd=directory_fd)
        opened = os.fstat(descriptor)
        if (
            _stat_fingerprint(opened) != _stat_fingerprint(expected)
            or opened.st_uid != expected.st_uid
        ):
            raise _ScanRejected
        payload = _read_bounded(descriptor, MAX_TRANSCRIPT_BYTES)
        after_fd = os.fstat(descriptor)
        after_path = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            len(payload) > MAX_TRANSCRIPT_BYTES
            or _stat_fingerprint(after_fd) != _stat_fingerprint(expected)
            or _stat_fingerprint(after_path) != _stat_fingerprint(expected)
            or after_fd.st_uid != expected.st_uid
            or after_path.st_uid != expected.st_uid
        ):
            raise _ScanRejected
        return _decode_jsonl(payload)
    except OSError as exc:
        raise _ScanRejected from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _intrinsic_child_review_proven(
    codex_home: Path,
    *,
    parent_id: str,
    root_started_at: float,
    allowed_child_id: str | None,
) -> bool:
    getuid = getattr(os, "getuid", None)
    if getuid is None:
        return False
    current_uid = getuid()
    sessions = codex_home / "sessions"
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    root_fd: int | None = None
    state = {"entries": 0, "candidates": 0, "bytes": 0}
    valid_children = 0

    def scan(directory_fd: int, depth: int) -> None:
        nonlocal valid_children
        if depth > MAX_SCAN_DEPTH:
            raise _ScanRejected
        names: list[str] = []
        try:
            with os.scandir(directory_fd) as iterator:
                for entry in iterator:
                    state["entries"] += 1
                    if state["entries"] > MAX_SCAN_ENTRIES:
                        raise _ScanRejected
                    names.append(entry.name)
        except OSError as exc:
            raise _ScanRejected from exc
        for name in sorted(names):
            try:
                info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                raise _ScanRejected from exc
            if stat.S_ISLNK(info.st_mode) or info.st_uid != current_uid:
                raise _ScanRejected
            if stat.S_ISDIR(info.st_mode):
                child_fd: int | None = None
                try:
                    child_fd = os.open(name, flags, dir_fd=directory_fd)
                    opened = os.fstat(child_fd)
                    if (
                        (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)
                        or opened.st_uid != current_uid
                    ):
                        raise _ScanRejected
                    scan(child_fd, depth + 1)
                    after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    if (
                        _stat_fingerprint(after) != _stat_fingerprint(info)
                        or after.st_uid != current_uid
                    ):
                        raise _ScanRejected
                finally:
                    if child_fd is not None:
                        os.close(child_fd)
                continue
            if not stat.S_ISREG(info.st_mode):
                raise _ScanRejected
            if not name.endswith(".jsonl"):
                continue
            if info.st_mtime + SCAN_MTIME_SLOP_SECONDS < root_started_at:
                continue
            state["candidates"] += 1
            state["bytes"] += info.st_size
            if (
                state["candidates"] > MAX_SCAN_CANDIDATES
                or info.st_size > MAX_TRANSCRIPT_BYTES
                or state["bytes"] > MAX_SCAN_BYTES
            ):
                raise _ScanRejected
            events = _read_scanned_jsonl(directory_fd, name, info)
            status = _linked_child_status(
                events,
                parent_id=parent_id,
                root_started_at=root_started_at,
                allowed_child_id=allowed_child_id,
            )
            if status < 0:
                raise _ScanRejected
            valid_children += status

    try:
        root_info = sessions.lstat()
        if (
            stat.S_ISLNK(root_info.st_mode)
            or not stat.S_ISDIR(root_info.st_mode)
            or root_info.st_uid != current_uid
        ):
            return False
        home = codex_home.resolve(strict=True)
        if not sessions.resolve(strict=True).is_relative_to(home):
            return False
        root_fd = os.open(sessions, flags)
        opened = os.fstat(root_fd)
        if (
            (opened.st_dev, opened.st_ino) != (root_info.st_dev, root_info.st_ino)
            or opened.st_uid != current_uid
        ):
            return False
        scan(root_fd, 0)
        after = sessions.lstat()
        if (
            _stat_fingerprint(after) != _stat_fingerprint(root_info)
            or after.st_uid != current_uid
        ):
            return False
    except (OSError, _ScanRejected):
        return False
    finally:
        if root_fd is not None:
            os.close(root_fd)
    return valid_children == 1


def _direct_child_filter(
    events: list[dict[str, Any]],
    *,
    session_id: str,
    turn_id: str,
) -> tuple[bool, str | None]:
    sessions = [
        event["payload"]
        for event in events
        if event.get("type") == "session_meta"
        and isinstance(event.get("payload"), dict)
    ]
    if len(sessions) != 1 or sessions[0].get("id") != session_id:
        return False, None
    boundaries = [
        (index, event["payload"].get("turn_id"))
        for index, event in enumerate(events)
        if event.get("type") == "event_msg"
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("type") == "task_started"
    ]
    if not boundaries or boundaries[-1][1] != turn_id:
        return False, None
    segment = events[boundaries[-1][0] :]
    calls: list[tuple[int, str]] = []
    for index, event in enumerate(segment):
        payload = event.get("payload")
        if (
            event.get("type") != "response_item"
            or not isinstance(payload, dict)
            or payload.get("type") != "function_call"
            or payload.get("name") != "spawn_agent"
        ):
            continue
        try:
            arguments = json.loads(payload.get("arguments", ""))
        except (TypeError, json.JSONDecodeError):
            return False, None
        if not isinstance(arguments, dict):
            return False, None
        if arguments.get("agent_type") != "plan-verifier":
            continue
        if (
            set(arguments) != {"message", "agent_type", "task_name", "fork_turns"}
            or not isinstance(arguments.get("message"), str)
            or not arguments["message"].strip()
            or not isinstance(arguments.get("task_name"), str)
            or TASK_NAME_RE.fullmatch(arguments["task_name"]) is None
            or arguments.get("fork_turns") not in {"none", "1", "2", "3"}
        ):
            return False, None
        call_id = payload.get("call_id")
        if isinstance(call_id, str) and call_id:
            calls.append((index, call_id))
    if not calls:
        return True, None
    if len(calls) != 1:
        return False, None
    call_index, call_id = calls[0]
    activities = [
        payload
        for index, event in enumerate(segment)
        if index > call_index
        and event.get("type") == "event_msg"
        and isinstance((payload := event.get("payload")), dict)
        and payload.get("type") == "sub_agent_activity"
        and payload.get("kind") == "started"
        and payload.get("event_id") == call_id
        and isinstance(payload.get("agent_thread_id"), str)
        and bool(payload["agent_thread_id"])
    ]
    if len(activities) != 1:
        return False, None
    child_id = activities[0].get("agent_thread_id")
    if not _valid_identifier(child_id):
        return False, None
    return True, child_id


def _handle_prompt(payload: dict[str, Any], codex_home: Path) -> None:
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")
    if not _valid_identifier(session_id):
        return
    if payload.get("agent_id") is not None or payload.get("agent_type") is not None:
        _remove_marker(codex_home, session_id)
        return
    categories = classify_prompt(payload.get("prompt"))
    if not _valid_identifier(turn_id) or not categories:
        _remove_marker(codex_home, session_id)
        return
    marker = {
        "schema": SCHEMA,
        "session_id": session_id,
        "turn_id": turn_id,
        "categories": list(categories),
        "attempted": False,
    }
    if not _atomic_marker_write(codex_home, marker):
        _remove_marker(codex_home, session_id)


def _handle_stop(payload: dict[str, Any], codex_home: Path) -> dict[str, str] | None:
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")
    if not _valid_identifier(session_id) or not _valid_identifier(turn_id):
        return None
    marker = _load_marker(codex_home, session_id)
    if marker is None:
        _remove_marker(codex_home, session_id)
        return None
    if marker["turn_id"] != turn_id:
        _remove_marker(codex_home, session_id)
        return None
    events = _read_transcript(codex_home, payload.get("transcript_path"))
    if events is None:
        _remove_marker(codex_home, session_id)
        return None
    direct_chain_valid, allowed_child_id = _direct_child_filter(
        events,
        session_id=session_id,
        turn_id=turn_id,
    )
    root_started_at = _root_task_started_epoch(
        events,
        session_id=session_id,
        turn_id=turn_id,
    )
    if (
        direct_chain_valid
        and root_started_at is not None
        and _intrinsic_child_review_proven(
            codex_home,
            parent_id=session_id,
            root_started_at=root_started_at,
            allowed_child_id=allowed_child_id,
        )
    ):
        _remove_marker(codex_home, session_id)
        return None
    if payload.get("stop_hook_active") is not False or marker["attempted"]:
        _remove_marker(codex_home, session_id)
        return None
    marker["attempted"] = True
    if not _atomic_marker_write(codex_home, marker):
        _remove_marker(codex_home, session_id)
        return None
    return dict(BLOCK_OUTPUT)


def handle(
    payload: object,
    *,
    codex_home: Path | None = None,
) -> dict[str, str] | None:
    """Handle one native hook envelope without emitting sensitive diagnostics."""
    if not isinstance(payload, dict):
        return None
    home = codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    event = payload.get("hook_event_name")
    if event == "UserPromptSubmit":
        _handle_prompt(payload, home)
        return None
    if event == "Stop":
        return _handle_stop(payload, home)
    return None


def main() -> int:
    """Read one bounded JSON hook envelope and print only protocol output."""
    try:
        raw = sys.stdin.buffer.read(MAX_HOOK_INPUT_BYTES + 1)
        if len(raw) > MAX_HOOK_INPUT_BYTES:
            return 0
        payload = json.loads(raw)
        output = handle(payload)
        if output is not None:
            sys.stdout.write(json.dumps(output, separators=(",", ":")) + "\n")
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
