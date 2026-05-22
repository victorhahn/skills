#!/usr/bin/env python3
"""Extract Skill-tool invocations and surrounding context from Claude Code JSONL transcripts.

Designed for the /skill-use-audit skill. Reads one or more JSONL session files,
finds every invocation of a named skill, and emits a JSON document summarizing
each invocation plus near-misses (user messages that arguably should have
triggered the skill but didn't).

Output schema is documented in the parent SKILL.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

# User messages that look like corrections / steering after the skill ran.
CORRECTION_PATTERNS = [
    r"\bno,?\b",
    r"\bthat'?s (not|wrong)\b",
    r"\bactually\b",
    r"\bback up\b",
    r"\bstop\b",
    r"\bwait\b",
    r"\bredo\b",
    r"\bnot what i\b",
    r"\binstead\b",
    r"\bdon'?t\b",
    r"\brevert\b",
    r"\bundo\b",
    r"\bi said\b",
]
CORRECTION_RE = re.compile("|".join(CORRECTION_PATTERNS), re.IGNORECASE)

# Synthetic user messages injected by the harness, not actual user input.
SYNTHETIC_PREFIXES = (
    "Base directory for this skill:",
    "Launching skill:",
    "Caveat: The messages below were generated",
    "[Request interrupted",
)


def is_synthetic_user_message(text: str) -> bool:
    s = (text or "").lstrip()
    return any(s.startswith(p) for p in SYNTHETIC_PREFIXES)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip malformed rows rather than failing the whole audit.
                continue
    return rows


def extract_text(content: Any) -> str:
    """Flatten Claude message content (string or list of blocks) into plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append(block.get("text", ""))
            elif btype == "tool_result":
                # Tool results can be strings or lists of text blocks; flatten conservatively.
                inner = block.get("content")
                if isinstance(inner, str):
                    parts.append(inner)
                elif isinstance(inner, list):
                    for sub in inner:
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            parts.append(sub.get("text", ""))
        return "\n".join(parts)
    return ""


def is_tool_result_only(content: Any) -> bool:
    """Tool results come back with role=user but every block is a tool_result.
    These are echoes of assistant tool calls, not real user input — exclude them
    from steering/correction signal so we don't mistake bash output for the user
    saying 'no'."""
    if not isinstance(content, list) or not content:
        return False
    for b in content:
        if not isinstance(b, dict):
            return False
        if b.get("type") != "tool_result":
            return False
    return True


def iter_messages(rows: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    """Yield normalized message records: {role, text, tool_uses, raw, ts, is_tool_result}."""
    for row in rows:
        rtype = row.get("type")
        msg = row.get("message") or {}
        if rtype == "user":
            content = msg.get("content", row.get("content", ""))
            yield {
                "role": "user",
                "text": extract_text(content),
                "tool_uses": [],
                "ts": row.get("timestamp"),
                "is_tool_result": is_tool_result_only(content),
                "raw": row,
            }
        elif rtype == "assistant":
            content = msg.get("content", [])
            text_parts: list[str] = []
            tool_uses: list[dict[str, Any]] = []
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_uses.append(
                            {
                                "name": block.get("name"),
                                "input": block.get("input", {}),
                                "id": block.get("id"),
                            }
                        )
            yield {
                "role": "assistant",
                "text": "\n".join(text_parts),
                "tool_uses": tool_uses,
                "ts": row.get("timestamp"),
                "is_tool_result": False,
                "raw": row,
            }


def find_invocations(messages: list[dict[str, Any]], skill_name: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for i, m in enumerate(messages):
        if m["role"] != "assistant":
            continue
        for tu in m["tool_uses"]:
            # Match either the Skill tool with input.skill, OR a slash-command invocation
            # surfaced as a user command-message (handled in find_slash_invocations below).
            if tu["name"] == "Skill" and tu["input"].get("skill") == skill_name:
                results.append(
                    {
                        "index": i,
                        "ts": m["ts"],
                        "args": tu["input"].get("args", ""),
                        "source": "Skill-tool",
                    }
                )
    return results


def find_slash_invocations(messages: list[dict[str, Any]], skill_name: str) -> list[dict[str, Any]]:
    """Find slash-command invocations of the skill (user-typed `/skill-name`)."""
    results: list[dict[str, Any]] = []
    pat = re.compile(rf"<command-name>/{re.escape(skill_name)}</command-name>")
    for i, m in enumerate(messages):
        if m["role"] != "user":
            continue
        if pat.search(m["text"] or ""):
            results.append(
                {
                    "index": i,
                    "ts": m["ts"],
                    "args": "",
                    "source": "slash-command",
                }
            )
    return results


def trigger_user_message(messages: list[dict[str, Any]], idx: int) -> str:
    """The most recent non-command user message before idx — what kicked off the invocation."""
    for j in range(idx - 1, -1, -1):
        m = messages[j]
        if m["role"] != "user" or m.get("is_tool_result"):
            continue
        text = m["text"] or ""
        if "<command-name>" in text or "<command-message>" in text:
            # The slash command itself was the trigger — return it so the auditor
            # can see what was invoked.
            return text[:600]
        if text.strip():
            return text[:600]
    return ""


def subsequent_context(
    messages: list[dict[str, Any]], idx: int, window: int = 30
) -> dict[str, Any]:
    """Look at the N messages after an invocation and summarize them."""
    user_msgs: list[str] = []
    tool_uses: list[str] = []
    corrections: list[str] = []
    end = min(len(messages), idx + 1 + window)
    for j in range(idx + 1, end):
        m = messages[j]
        if m["role"] == "user":
            if m.get("is_tool_result"):
                continue
            text = (m["text"] or "").strip()
            if not text or "<command-name>" in text or "<system-reminder>" in text:
                continue
            if is_synthetic_user_message(text):
                continue
            user_msgs.append(text[:400])
            if CORRECTION_RE.search(text):
                corrections.append(text[:200])
        elif m["role"] == "assistant":
            for tu in m["tool_uses"]:
                name = tu.get("name") or ""
                if name:
                    tool_uses.append(name)
    return {
        "subsequent_user_messages": user_msgs,
        "subsequent_tool_uses": tool_uses,
        "ended_with_user_correction": bool(corrections),
        "correction_excerpts": corrections,
    }


def find_near_misses(
    messages: list[dict[str, Any]], skill_name: str, invocation_indices: set[int]
) -> list[dict[str, Any]]:
    """Heuristic: flag user messages mentioning the skill name (or close variants)
    where the skill did NOT subsequently run within the next few assistant turns.

    Intentionally conservative — a few false positives are acceptable; the human
    auditor can dismiss them. The goal is just to surface candidates the rubric's
    "false negative" axis should consider.
    """
    near: list[dict[str, Any]] = []
    name_re = re.compile(rf"\b/?{re.escape(skill_name)}\b", re.IGNORECASE)

    # Build set of indices where a Skill-tool invocation of skill_name occurred,
    # to detect whether one followed shortly after a candidate message.
    invocation_set = invocation_indices

    for i, m in enumerate(messages):
        if m["role"] != "user" or m.get("is_tool_result"):
            continue
        text = m["text"] or ""
        if "<system-reminder>" in text or "<command-name>" in text:
            continue
        if is_synthetic_user_message(text):
            continue
        if not name_re.search(text):
            continue
        # Did the skill run in the next ~5 assistant messages?
        followed = False
        seen_assistant = 0
        for j in range(i + 1, min(len(messages), i + 12)):
            mm = messages[j]
            if mm["role"] != "assistant":
                continue
            seen_assistant += 1
            if j in invocation_set:
                followed = True
                break
            if seen_assistant >= 5:
                break
        if followed:
            continue
        # What did the assistant do instead in the next ~3 tool uses?
        used_instead: list[str] = []
        for j in range(i + 1, min(len(messages), i + 12)):
            mm = messages[j]
            if mm["role"] == "assistant":
                for tu in mm["tool_uses"]:
                    used_instead.append(tu.get("name") or "")
                    if len(used_instead) >= 3:
                        break
            if len(used_instead) >= 3:
                break
        near.append(
            {
                "timestamp": m["ts"],
                "user_message": text[:600],
                "what_was_used_instead": ", ".join(used_instead) or "nothing",
            }
        )
    return near


def audit_transcript(path: Path, skill_name: str) -> dict[str, Any]:
    rows = load_jsonl(path)
    messages = list(iter_messages(rows))

    session_id = ""
    for r in rows:
        if "sessionId" in r:
            session_id = r["sessionId"]
            break

    tool_invocations = find_invocations(messages, skill_name)
    slash_invocations = find_slash_invocations(messages, skill_name)

    # Merge and dedupe by index.
    by_index: dict[int, dict[str, Any]] = {}
    for inv in tool_invocations + slash_invocations:
        by_index.setdefault(inv["index"], inv)
    all_invocations = sorted(by_index.values(), key=lambda x: x["index"])

    invocation_records: list[dict[str, Any]] = []
    for inv in all_invocations:
        ctx = subsequent_context(messages, inv["index"])
        invocation_records.append(
            {
                "session_id": session_id,
                "timestamp": inv["ts"],
                "source": inv["source"],
                "trigger_user_message": trigger_user_message(messages, inv["index"]),
                "skill_args": inv["args"],
                **ctx,
            }
        )

    near_misses = find_near_misses(messages, skill_name, set(by_index.keys()))

    return {
        "skill": skill_name,
        "transcript": str(path),
        "session_id": session_id,
        "invocation_count": len(invocation_records),
        "invocations": invocation_records,
        "near_misses": near_misses,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--skill", required=True, help="Skill name (without leading slash)")
    ap.add_argument(
        "--transcript",
        action="append",
        required=True,
        help="Path to a JSONL transcript file (repeat for multiple).",
    )
    args = ap.parse_args()

    skill = args.skill.lstrip("/")

    audits = []
    for t in args.transcript:
        p = Path(t).expanduser()
        if not p.exists():
            print(f"warning: transcript not found: {p}", file=sys.stderr)
            continue
        audits.append(audit_transcript(p, skill))

    merged = {
        "skill": skill,
        "transcripts_scanned": len(audits),
        "per_transcript": audits,
        "invocations": [inv for a in audits for inv in a["invocations"]],
        "near_misses": [nm for a in audits for nm in a["near_misses"]],
    }
    print(json.dumps(merged, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
