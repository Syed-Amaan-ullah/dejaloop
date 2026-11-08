"""Semantic judges: TypeSafe Jev client, the built-in LocalJudge, and a mock.

Real client: POST https://api.typesafe.ai/v1/systemone
  body: {"model": "jev-latest", "state": <text>, "questions": {...}}
  Noul answers come back as {"type": "noul", "noul": <0..1>} under each id.
Auth: TYPESAFE_API_KEY env var. OpenRouter is a possible later transport.

Judge selection (DEJALOOP_JEV env var, see get_client):
  - "local" (or unset, no TypeSafe key): LocalJudge — zero-cost, offline,
    no key. This is the default so the tool works fully out of the box.
  - "typesafe" (or unset with TYPESAFE_API_KEY set): real Jev via the API.
  - "mock": deterministic test double for tests/demos, never a real default.
  - "off" / "none": no judge — deterministic layer only.
"""
from __future__ import annotations

import json
import os
import urllib.request


class JevError(Exception):
    pass


def load_api_key() -> str:
    """TypeSafe key lookup: TYPESAFE_API_KEY env var first, then the local
    credentials file written by `dejaloop set-key`
    (~/.dejaloop/credentials.json, created with 0600 permissions).
    The key is never stored inside the project or in config.json."""
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key
    try:
        from .core import home_dir
        path = os.path.join(home_dir(), "credentials.json")
        if os.path.exists(path):
            with open(path) as f:
                return str(json.load(f).get("typesafe_api_key", "")).strip()
    except Exception:
        pass
    return ""


class TypeSafeJev:
    def __init__(self, api_key: str | None = None, timeout: float = 2.0,
                 endpoint: str = "https://api.typesafe.ai/v1/systemone",
                 model: str = "jev-latest"):
        self.api_key = api_key or load_api_key()
        self.timeout = timeout
        self.endpoint = endpoint
        self.model = model

    def evaluate_stall(self, trajectory_text: str, signals: dict) -> dict:
        """Return {'stuck': float, 'repeating_strategy': float, 'progress': str}"""
        if not self.api_key:
            raise JevError("TYPESAFE_API_KEY not set")
        body = {
            "model": self.model,
            "state": trajectory_text,
            "questions": {
                "stuck": {"type": "noul",
                            "instructions": "Is this agent stuck — doing things but not "
                                            "getting any closer to finishing the task?"},
                "repeating": {"type": "noul",
                              "instructions": "Is the agent repeating a strategy that has "
                                              "already failed, even if the exact calls differ?"},
                "progress": {"type": "choice",
                             "instructions": "How would you rate the agent's recent progress?",
                             "criteria": {
                                 "progressing": "Recent calls clearly advance the task.",
                                 "slow": "Some progress, but inefficient.",
                                 "stuck": "No real progress in recent calls.",
                                 "looping": "Recent calls repeat earlier failed attempts."}},
            },
        }
        req = urllib.request.Request(
            self.endpoint, data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode())
        answers = data.get("answers", data.get("questions", data))
        def noul(key):
            a = answers.get(key, {})
            return float(a.get("noul", 0.0)) if isinstance(a, dict) else float(a or 0.0)
        prog = answers.get("progress", {})
        return {"stuck": noul("stuck"), "repeating_strategy": noul("repeating"),
                "progress": prog.get("choice", "progressing") if isinstance(prog, dict) else "progressing"}


class MockJev:
    """Deterministic test double. Scores obvious stuck features high."""
    def evaluate_stall(self, trajectory_text: str, signals: dict) -> dict:
        streak = signals.get("streak_same", 0)
        fails = signals.get("fail_streak", 0)
        no_prog = signals.get("no_progress_steps", 0)
        score = 0.05 + 0.22 * streak + 0.18 * fails + 0.03 * no_prog
        stuck_p = max(0.0, min(0.99, score))
        progress = ("looping" if stuck_p >= 0.75 else
                    "stuck" if stuck_p >= 0.5 else
                    "slow" if stuck_p >= 0.3 else "progressing")
        return {"stuck": stuck_p, "repeating_strategy": stuck_p * 0.9,
                "progress": progress}


class LocalJudge:
    """Zero-cost local judge: no API, no key, no network.

    NOT a Jev clone — Jev is a general trained decision model. This is a
    narrow stuck-spotter for coding trajectories, built from progress
    features: repetition, failure patterns, call similarity, and whether
    edits/tests are actually happening. Its key insight: failures *with*
    intervening edits are progress (TDD); failures *without* edits are a loop.
    """
    def evaluate_stall(self, trajectory_text: str, signals: dict) -> dict:
        streak = min(signals.get("streak_same", 0), 4) / 4
        fails = min(signals.get("fail_streak", 0), 4) / 4
        no_prog = min(signals.get("no_progress_steps", 0), 12) / 12
        sim = signals.get("similarity", 0.0)
        edits = signals.get("edits", 0)
        # Failure only counts against the agent when nothing is being changed.
        fail_weight = fails if edits == 0 else fails * 0.25
        score = (0.05 + 0.30 * streak + 0.30 * fail_weight
                 + 0.25 * sim * max(fail_weight, streak) + 0.15 * no_prog * sim)
        # Read/search thrash: many highly similar non-edit calls, zero edits,
        # zero verifications — the agent is circling, not exploring. (Varied
        # exploration has low similarity, so it stays under this floor.)
        if edits == 0 and sim >= 0.5 and signals.get("no_progress_steps", 0) >= 5:
            score = max(score, 0.55)
        stuck_p = max(0.0, min(0.99, score))
        progress = ("looping" if stuck_p >= 0.75 else
                    "stuck" if stuck_p >= 0.5 else
                    "slow" if stuck_p >= 0.3 else "progressing")
        return {"stuck": round(stuck_p, 3),
                "repeating_strategy": round(stuck_p * 0.9, 3),
                "progress": progress}


def get_client(cfg) -> object | None:
    """Pick the active judge from the environment.

    DEJALOOP_JEV=off|none returns None (deterministic layer only).
    Otherwise an explicit DEJALOOP_JEV wins; with it unset, a present
    TYPESAFE_API_KEY selects real Jev, and the fallback default is the
    zero-cost LocalJudge so a fresh install judges semantically with
    no key, no account, and no network.
    """
    mode = os.environ.get("DEJALOOP_JEV", "").lower().strip()
    if mode in ("off", "none"):
        return None
    if mode == "mock":
        return MockJev()
    if mode == "local":
        return LocalJudge()
    if mode == "typesafe" or load_api_key():
        return TypeSafeJev(timeout=cfg.jev_timeout_s)
    return LocalJudge()
