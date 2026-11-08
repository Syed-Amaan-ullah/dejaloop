"""DejaLoop CLI: `init`, `status`, `demo` (no keys needed) and `report`."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from dataclasses import asdict

from . import hook
from .core import Config, home_dir
from .jev import LocalJudge, MockJev, TypeSafeJev, get_client


def judge_label(cfg: Config) -> str:
    """Human-readable name of the judge get_client() would select right now."""
    client = get_client(cfg)
    if client is None:
        return "none (deterministic layer only)"
    if isinstance(client, LocalJudge):
        return "LocalJudge (built-in, zero-cost, offline)"
    if isinstance(client, MockJev):
        return "MockJev (test double)"
    if isinstance(client, TypeSafeJev):
        return "TypeSafe Jev (API)"
    return type(client).__name__


def judge_source() -> str:
    mode = os.environ.get("DEJALOOP_JEV", "").strip()
    if mode:
        return f"DEJALOOP_JEV={mode}"
    if os.environ.get("TYPESAFE_API_KEY"):
        return "default (TYPESAFE_API_KEY present)"
    return "default (built-in LocalJudge)"


def ledger_count() -> int:
    path = os.path.join(home_dir(), "ledger.jsonl")
    if not os.path.exists(path):
        return 0
    with open(path) as f:
        return sum(1 for line in f if line.strip())


def init_cmd() -> str:
    """Create the DejaLoop home + default config, and report what's active."""
    home = home_dir()
    os.makedirs(os.path.join(home, "sessions"), exist_ok=True)
    cfg_path = os.path.join(home, "config.json")
    created = False
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w") as f:
            json.dump(asdict(Config()), f, indent=2)
            f.write("\n")
        created = True
    cfg = Config.load()
    from .jev import load_api_key
    key = bool(load_api_key())
    lines = [
        f"DejaLoop home: {home}",
        f"Config: {cfg_path} ({'created with defaults' if created else 'already exists, left unchanged'})",
        f"Mode: {cfg.mode} (shadow = warn only, enforce = can block)",
        f"Active judge: {judge_label(cfg)} [via {judge_source()}]",
        f"TypeSafe API key: {'present' if key else 'not set'}",
    ]
    if not key:
        lines.append("No key needed: the built-in LocalJudge is active by default. "
                     "Run `dejaloop set-key` or set TYPESAFE_API_KEY to upgrade "
                     "to real Jev judgments.")
    lines.append("Next: install the plugin in Claude Code, then run "
                 "`python3 -m dejaloop.cli status` anytime.")
    return "\n".join(lines)


def set_key_cmd(key: str) -> str:
    """Store the TypeSafe key locally: ~/.dejaloop/credentials.json (0600).
    The key is never printed back and never goes in the project/config."""
    from .jev import load_api_key  # noqa: F401  (kept import surface obvious)
    home = home_dir()
    os.makedirs(home, exist_ok=True)
    path = os.path.join(home, "credentials.json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump({"typesafe_api_key": key.strip()}, f)
    os.chmod(path, 0o600)
    return (f"TypeSafe key saved to {path} (permissions 0600, only you can read it).\n"
            f"Active judge is now: {judge_label(Config.load())}. "
            "Restart Claude Code to pick it up.")


def status_cmd() -> str:
    """Summarize config, active judge, and recorded interventions."""
    cfg = Config.load()
    from .jev import load_api_key
    key = bool(load_api_key())
    sessions_dir = os.path.join(home_dir(), "sessions")
    n_sessions = 0
    if os.path.isdir(sessions_dir):
        n_sessions = len([f for f in os.listdir(sessions_dir) if f.endswith(".json")])
    lines = [
        f"DejaLoop home: {home_dir()}",
        f"Mode: {cfg.mode} | check every {cfg.check_every} calls | "
        f"warn ≥ {cfg.warn_at:.2f} | replan ≥ {cfg.replan_at:.2f} | halt ≥ {cfg.halt_at:.2f}",
        f"Active judge: {judge_label(cfg)} [via {judge_source()}]",
        f"TypeSafe API key: {'present' if key else 'not set'}",
        f"Sessions tracked: {n_sessions}",
        f"Interventions recorded: {ledger_count()}",
    ]
    from .core import read_totals
    totals = read_totals()
    if totals["est_saved_usd"] > 0:
        lines.append(f"Estimated money saved by stopped loops: ~${totals['est_saved_usd']:.2f} "
                     f"across {totals['blocks']} stopped loop(s) — a rough estimate: each "
                     "stopped loop would likely have repeated ~10 more times at ~$0.05 a step.")
    return "\n".join(lines)


def run_payload(payload: dict) -> dict | None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        hook.handle(payload)
    out = buf.getvalue().strip()
    return json.loads(out) if out.startswith("{") else None


def scenario(name: str, steps: list[dict]) -> dict:
    """Feed a scripted session through the real hook handler."""
    sid = f"demo-{name}"
    results = {"scenario": name, "blocked_calls": 0, "stop_blocked": False,
               "interventions": 0, "notes": []}
    for step in steps:
        step = dict(step, session_id=sid)
        out = run_payload(step)
        if not out:
            continue
        hso = out.get("hookSpecificOutput", {})
        if hso.get("permissionDecision") in ("deny", "ask"):
            results["blocked_calls"] += 1
            results["notes"].append(hso.get("permissionDecisionReason", "")[:110])
        if out.get("decision") == "block":
            results["stop_blocked"] = True
            results["notes"].append(out.get("reason", "")[:110])
        if out.get("systemMessage"):
            results["notes"].append(out["systemMessage"][:110])
    home = os.environ["DEJALOOP_HOME"]
    state = json.load(open(os.path.join(home, "sessions", f"{sid}.json")))
    results["interventions"] = len(state.get("interventions", []))
    results["est_saved_usd"] = state.get("est_saved_usd", 0.0)
    return results


def pre(tool, tin):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tin}


def post(tool, tin, resp="ok"):
    return {"hook_event_name": "PostToolUse", "tool_name": tool,
            "tool_input": tin, "tool_response": resp}


def demo() -> list[dict]:
    os.environ["DEJALOOP_HOME"] = tempfile.mkdtemp(prefix="dejaloop-demo-")
    os.environ.setdefault("DEJALOOP_JEV", "mock")
    os.environ.setdefault("DEJALOOP_MODE", "enforce")
    out = []

    # A: runaway identical loop — agent re-reads the same file forever
    steps = [{"hook_event_name": "UserPromptSubmit", "prompt": "Fix the login bug"}]
    for _ in range(6):
        steps += [pre("Read", {"file_path": "auth.py"}), post("Read", {"file_path": "auth.py"})]
    out.append(scenario("runaway-identical-loop", steps))

    # B: semantic loop — different commands, same failure, no edits
    steps = [{"hook_event_name": "UserPromptSubmit", "prompt": "Make the tests pass"}]
    for i, cmd in enumerate(["pytest -q", "pytest tests/", "python -m pytest",
                             "pytest -q -x", "pytest tests/ -q", "python -m pytest -q"]):
        steps += [pre("Bash", {"command": cmd}),
                  post("Bash", {"command": cmd}, "Error: assertion failed\nTraceback...")]
    steps += [pre("Bash", {"command": "pytest -q"}), {"hook_event_name": "Stop"}]
    out.append(scenario("semantic-failing-loop", steps))

    # C: healthy session — read, edit, test passes, stop allowed
    steps = [{"hook_event_name": "UserPromptSubmit", "prompt": "Fix the login bug"},
             pre("Read", {"file_path": "auth.py"}), post("Read", {"file_path": "auth.py"}),
             pre("Edit", {"file_path": "auth.py"}), post("Edit", {"file_path": "auth.py"}),
             pre("Bash", {"command": "pytest -q"}), post("Bash", {"command": "pytest -q"}, "3 passed"),
             {"hook_event_name": "Stop"}]
    out.append(scenario("healthy-session", steps))

    # D: fake done — edits but never verifies, then tries to stop
    steps = [{"hook_event_name": "UserPromptSubmit", "prompt": "Add a feature"},
             pre("Write", {"file_path": "feat.py"}), post("Write", {"file_path": "feat.py"}),
             {"hook_event_name": "Stop"}]
    out.append(scenario("unverified-done-claim", steps))
    return out


def report() -> str:
    path = os.path.join(home_dir(), "ledger.jsonl")
    if not os.path.exists(path):
        return "No interventions recorded yet."
    rows = [json.loads(l) for l in open(path) if l.strip()]
    lines = [f"{len(rows)} intervention(s) recorded:"]
    for r in rows[-20:]:
        lines.append(f"- [{r['kind']}/{r['action']}] {r['reason']}")
    return "\n".join(lines)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if cmd == "init":
        print(init_cmd())
    elif cmd == "set-key":
        import getpass
        key = getpass.getpass("Paste your TypeSafe API key (hidden, not shown): ")
        if not key.strip():
            print("No key entered — nothing saved.")
            return 1
        print(set_key_cmd(key))
    elif cmd == "status":
        print(status_cmd())
    elif cmd == "demo":
        for r in demo():
            print(f"\n== {r['scenario']} ==")
            print(f"blocked calls: {r['blocked_calls']} | stop blocked: {r['stop_blocked']} "
                  f"| interventions logged: {r['interventions']} "
                  f"| est. saved ~${r.get('est_saved_usd', 0.0):.2f}")
            for n in r["notes"][:3]:
                print(f"  • {n}")
    elif cmd == "report":
        print(report())
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
