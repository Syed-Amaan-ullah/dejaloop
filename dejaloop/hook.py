"""Claude Code hook entry point.

Claude Code runs this for PreToolUse / PostToolUse / Stop / UserPromptSubmit,
passing one JSON object on stdin. We answer with Claude Code's hook contract:
  - exit 0 + JSON on stdout for structured decisions
  - PreToolUse: hookSpecificOutput.permissionDecision = allow|deny|ask
  - Stop: {"decision": "block", "reason": ...} keeps Claude working

FAIL-OPEN BY DESIGN: any exception in this file results in exit 0 with no
output, so a DejaLoop bug can never block or crash a user's session.
"""
from __future__ import annotations

import json
import sys

from .core import (Config, SessionState, fingerprint, result_failed,
                   log_intervention, decide_action)
from .jev import get_client


def _out(obj: dict):
    print(json.dumps(obj))


def _pre_tool_use(payload, state: SessionState, cfg: Config):
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input", {}) or {}
    fp = fingerprint(tool, tin)
    state.pre_counts[fp] = state.pre_counts.get(fp, 0) + 1

    # A semantic REPLAN/HALT queued by the last Jev check applies to this call.
    if state.pending_action in ("replan", "halt"):
        action, reason = state.pending_action, state.pending_reason
        state.pending_action, state.pending_reason = "", ""
        if cfg.mode == "enforce":
            log_intervention(state, "semantic", action, reason, cfg)
            decision = "ask" if action == "halt" else "deny"
            state.save()
            _out({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason":
                    f"[DejaLoop:{action}] {reason} Present a new plan before continuing."}})
            return
        log_intervention(state, "semantic", action + " (shadow)", reason)

    # Deterministic hard repeat: the identical call is being attempted again
    # after it already ran repeat_limit times in a row.
    if state.streak_same() >= cfg.repeat_limit and state.calls and \
            state.calls[-1]["fp"] == fp:
        reason = (f"Identical {tool} call already ran {state.streak_same()}x in a row "
                  f"with the same result. Change approach instead of repeating it.")
        if cfg.mode == "enforce":
            log_intervention(state, "deterministic", "deny", reason, cfg)
            state.save()
            _out({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"[DejaLoop] {reason}"}})
            return
        log_intervention(state, "deterministic", "warn (shadow)", reason)

    state.save()


def _post_tool_use(payload, state: SessionState, cfg: Config):
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input", {}) or {}
    failed = result_failed(payload.get("tool_response"))
    state.calls.append({"fp": fingerprint(tool, tin), "tool": tool,
                        "input": tin, "failed": failed})
    state.calls = state.calls[-50:]

    alert = state.deterministic_alert(cfg)
    jev_due = (len(state.calls) - state.last_jev_check_at) >= cfg.check_every
    if alert or jev_due:
        client = get_client(cfg)
        if client is not None:
            signals = {"streak_same": state.streak_same(),
                       "fail_streak": state.fail_streak_same_command(),
                       "no_progress_steps": state.no_progress_steps(),
                       "similarity": state.recent_similarity(),
                       "edits": state.edits()}
            try:
                verdict = client.evaluate_stall(state.trajectory_text(), signals)
            except Exception:
                verdict = None  # fail-open on Jev errors/timeouts
            if verdict:
                state.last_jev_check_at = len(state.calls)
                action = decide_action(float(verdict.get("stuck", 0.0)), cfg)
                if action != "continue":
                    reason = (f"This session looks stuck — the judge is "
                              f"{float(verdict.get('stuck', 0.0)):.0%} sure it is "
                              f"going in circles. "
                              f"{alert[1] if alert else 'Recent steps are not getting any closer to done.'}")
                    if action == "warn":
                        log_intervention(state, "semantic", "warn", reason, cfg)
                        state.save()
                        _out({"systemMessage": f"[DejaLoop] {reason}"})
                        return
                    state.pending_action, state.pending_reason = action, reason
        elif alert:
            log_intervention(state, "deterministic", "observed", alert[1])
    state.save()


def _stop(payload, state: SessionState, cfg: Config):
    if state.edits() > 0 and state.verification_runs() == 0:
        reason = ("You edited files but never ran a test, build, or lint in this "
                  "session. Run a verification command before claiming done.")
        if cfg.mode == "enforce":
            log_intervention(state, "done_claim", "block_stop", reason, cfg)
            state.save()
            _out({"decision": "block", "reason": f"[DejaLoop] {reason}"})
            return
        log_intervention(state, "done_claim", "warn (shadow)", reason)
        state.save()
        _out({"systemMessage": f"[DejaLoop] {reason}"})
        return
    state.save()


def handle(payload: dict) -> None:
    cfg = Config.load()
    event = payload.get("hook_event_name", "")
    state = SessionState.load(payload.get("session_id", "unknown"))
    if event == "UserPromptSubmit":
        state.task = (payload.get("prompt", "") or "")[:500]
        state.save()
    elif event == "PreToolUse":
        _pre_tool_use(payload, state, cfg)
    elif event == "PostToolUse":
        _post_tool_use(payload, state, cfg)
    elif event == "Stop":
        _stop(payload, state, cfg)
    else:
        state.save()


def main():
    try:
        payload = json.load(sys.stdin)
        handle(payload)
    except Exception:
        pass  # fail-open, always
    sys.exit(0)


if __name__ == "__main__":
    main()
