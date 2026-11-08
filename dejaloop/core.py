"""Core state, deterministic loop detection, and intervention policy.

No network calls live here. Everything is stdlib-only and unit-testable.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict

VERIFY_RE = re.compile(r"\b(pytest|unittest|npm test|yarn test|pnpm test|"
                       r"npm run build|yarn build|tsc\b|eslint|lint|go test|"
                       r"cargo test|make test|vitest|jest)\b", re.I)


def home_dir() -> str:
    return os.environ.get("DEJALOOP_HOME") or os.path.expanduser("~/.dejaloop")


def fingerprint(tool_name: str, tool_input) -> str:
    blob = json.dumps({"t": tool_name, "i": tool_input}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def result_failed(tool_response) -> bool:
    """Best-effort failure detection from a Claude Code tool_response payload."""
    if isinstance(tool_response, dict):
        if tool_response.get("is_error") or tool_response.get("error"):
            return True
        if tool_response.get("success") is False:
            return True
        code = tool_response.get("exit_code", tool_response.get("exitCode"))
        if isinstance(code, int) and code != 0:
            return True
        text = str(tool_response.get("stdout", "")) + str(tool_response.get("stderr", ""))
    else:
        text = str(tool_response or "")
    low = text.lower()
    return ("traceback" in low or "error:" in low or "failed" in low
            or "command not found" in low)


@dataclass
class Config:
    mode: str = "shadow"             # default: "shadow" (log only); "enforce" can block
    repeat_limit: int = 3            # identical call+result streak that trips the brake
    fail_limit: int = 2              # same command failing this many times = suspicious
    check_every: int = 5             # ask Jev at least this often (tool calls)
    warn_at: float = 0.50
    replan_at: float = 0.75
    halt_at: float = 0.90
    jev_timeout_s: float = 2.0
    # Savings estimate (shown as "~$X saved"): when DejaLoop stops a loop, we
    # estimate what it would have kept burning. Deliberately conservative and
    # always labelled an estimate: the pattern would have repeated at least
    # est_avoided_repeats more times, at roughly est_usd_per_call per step.
    est_usd_per_call: float = 0.05
    est_avoided_repeats: int = 10

    @classmethod
    def load(cls) -> "Config":
        path = os.path.join(home_dir(), "config.json")
        cfg = cls()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
            except Exception:
                pass  # fail-open: a broken config must never break a session
        if os.environ.get("DEJALOOP_MODE"):
            cfg.mode = os.environ["DEJALOOP_MODE"]
        return cfg


@dataclass
class SessionState:
    session_id: str
    task: str = ""
    calls: list = field(default_factory=list)        # post-tool records
    pre_counts: dict = field(default_factory=dict)   # fingerprint -> pre-tool count
    interventions: list = field(default_factory=list)
    pending_action: str = ""                          # "", "warn", "replan", "halt"
    pending_reason: str = ""
    est_saved_usd: float = 0.0                        # estimated $ saved by blocks
    last_jev_check_at: int = 0
    created_at: float = field(default_factory=time.time)

    # ---- derived signals -------------------------------------------------
    def streak_same(self) -> int:
        if not self.calls:
            return 0
        last, n = self.calls[-1]["fp"], 0
        for c in reversed(self.calls):
            if c["fp"] == last:
                n += 1
            else:
                break
        return n

    def fail_streak_same_command(self) -> int:
        n = 0
        for c in reversed(self.calls):
            if c["tool"] == "Bash" and c.get("failed"):
                n += 1
            else:
                break
        return n

    def no_progress_steps(self) -> int:
        n = 0
        for c in reversed(self.calls):
            if c["tool"] in ("Write", "Edit", "NotebookEdit"):
                break
            n += 1
        return n

    def edits(self) -> int:
        return sum(1 for c in self.calls if c["tool"] in ("Write", "Edit", "NotebookEdit"))

    def verification_runs(self) -> int:
        n = 0
        for c in self.calls:
            if c["tool"] == "Bash" and VERIFY_RE.search(str(c.get("input", {}).get("command", ""))):
                if not c.get("failed"):
                    n += 1
        return n

    def recent_similarity(self) -> float:
        """Average Jaccard similarity of consecutive recent call inputs.

        ~1.0 = the agent keeps doing near-identical things (even if not
        byte-identical, so fingerprints miss it). ~0 = varied work.
        """
        def toks(c):
            return set(re.findall(r"[a-z0-9_./-]+",
                                  json.dumps(c.get("input", {}), default=str).lower()))
        recent = self.calls[-6:]
        if len(recent) < 2:
            return 0.0
        sims = []
        for a, b in zip(recent, recent[1:]):
            ta, tb = toks(a), toks(b)
            if ta or tb:
                sims.append(len(ta & tb) / max(1, len(ta | tb)))
        return sum(sims) / len(sims) if sims else 0.0

    def deterministic_alert(self, cfg: Config):
        """Return (kind, reason) or None. kind in {repeat, fail_loop, no_progress}."""
        if self.streak_same() >= cfg.repeat_limit:
            return ("repeat",
                    f"Same tool call repeated {self.streak_same()}x with no change in between.")
        if self.fail_streak_same_command() >= cfg.fail_limit + 1:
            return ("fail_loop",
                    f"Bash has failed {self.fail_streak_same_command()}x in a row.")
        return None

    def trajectory_text(self, limit: int = 8) -> str:
        lines = [f"Task: {self.task or '(unknown)'}", "Recent tool calls:"]
        for c in self.calls[-limit:]:
            lines.append(f"- {c['tool']} {json.dumps(c.get('input', {}), default=str)[:160]}"
                         f" -> {'FAILED' if c.get('failed') else 'ok'}")
        lines.append(f"Edits so far: {self.edits()} | verified runs: {self.verification_runs()} "
                     f"| total calls: {len(self.calls)}")
        return "\n".join(lines)

    # ---- persistence ------------------------------------------------------
    def path(self) -> str:
        d = os.path.join(home_dir(), "sessions")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"{self.session_id}.json")

    def save(self):
        tmp = self.path() + ".tmp"
        with open(tmp, "w") as f:
            json.dump(asdict(self), f)
        os.replace(tmp, self.path())

    @classmethod
    def load(cls, session_id: str) -> "SessionState":
        p = os.path.join(home_dir(), "sessions", f"{session_id}.json")
        if os.path.exists(p):
            try:
                with open(p) as f:
                    return cls(**json.load(f))
            except Exception:
                pass
        return cls(session_id=session_id)


BLOCKING_ACTIONS = {"deny", "replan", "halt", "ask", "block_stop"}


def read_totals() -> dict:
    """Lifetime totals across all sessions: {'est_saved_usd': float, 'blocks': int}"""
    p = os.path.join(home_dir(), "totals.json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                t = json.load(f)
            return {"est_saved_usd": float(t.get("est_saved_usd", 0.0)),
                    "blocks": int(t.get("blocks", 0))}
        except Exception:
            pass
    return {"est_saved_usd": 0.0, "blocks": 0}


def log_intervention(state: SessionState, kind: str, action: str, reason: str,
                     cfg: Config | None = None):
    cfg = cfg or Config()
    saved = (cfg.est_usd_per_call * cfg.est_avoided_repeats
             if action in BLOCKING_ACTIONS else 0.0)
    entry = {"ts": time.time(), "session_id": state.session_id, "kind": kind,
             "action": action, "reason": reason, "est_saved_usd": round(saved, 4)}
    state.interventions.append(entry)
    state.est_saved_usd = round(state.est_saved_usd + saved, 4)
    d = home_dir()
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "ledger.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")
    if saved > 0:
        totals = read_totals()
        totals["est_saved_usd"] = round(totals["est_saved_usd"] + saved, 4)
        totals["blocks"] += 1
        tmp = os.path.join(d, "totals.json.tmp")
        with open(tmp, "w") as f:
            json.dump(totals, f)
        os.replace(tmp, os.path.join(d, "totals.json"))


def decide_action(stuck_p: float, cfg: Config) -> str:
    if stuck_p >= cfg.halt_at:
        return "halt"
    if stuck_p >= cfg.replan_at:
        return "replan"
    if stuck_p >= cfg.warn_at:
        return "warn"
    return "continue"
