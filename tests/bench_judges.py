"""Head-to-head benchmark: deterministic-only vs LocalJudge vs MockJev
(real Jev joins once a key exists). Scenarios are labelled; a 'flag' is any
intervention (warn or stronger). Healthy scenarios must NOT be flagged."""
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def pre(tool, tin):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tin}


def post(tool, tin, resp="ok"):
    return {"hook_event_name": "PostToolUse", "tool_name": tool,
            "tool_input": tin, "tool_response": resp}


def pair(tool, tin, resp="ok"):
    return [pre(tool, tin), post(tool, tin, resp)]


FAIL = "Error: assertion failed\nTraceback (most recent call last)"

SCENARIOS = [
    # ---- stuck (must flag) ----
    ("STUCK identical re-read loop", True,
     sum([pair("Read", {"file_path": "auth.py"}) for _ in range(6)], [])),
    ("STUCK varying failing test commands, no edits", True,
     sum([pair("Bash", {"command": c}, FAIL) for c in
          ["pytest -q", "pytest tests/", "python -m pytest",
           "pytest -q -x", "pytest tests/ -q", "python -m pytest -q"]], [])),
    ("STUCK alternating two failing strategies A/B/A/B", True,
     sum([pair("Bash", {"command": c}, FAIL) for c in
          ["npm run build", "yarn build", "npm run build",
           "yarn build", "npm run build", "yarn build"]], [])),
    ("STUCK near-identical greps, no edits ever", True,
     sum([pair("Grep", {"pattern": p}) for p in
          ["def login", "def login(", "login handler", "def login user",
           "login session", "def login auth"]], [])),
    # ---- healthy (must NOT flag) ----
    ("HEALTHY read -> edit -> test passes", False,
     pair("Read", {"file_path": "auth.py"}) + pair("Edit", {"file_path": "auth.py"})
     + pair("Bash", {"command": "pytest -q"}, "3 passed")),
    ("HEALTHY TDD: edit, fail, edit, fail, edit, pass", False,
     pair("Edit", {"file_path": "calc.py"})
     + pair("Bash", {"command": "pytest -q"}, FAIL)
     + pair("Edit", {"file_path": "calc.py"})
     + pair("Bash", {"command": "pytest -q"}, FAIL)
     + pair("Edit", {"file_path": "calc.py"})
     + pair("Bash", {"command": "pytest -q"}, "5 passed")),
    ("HEALTHY exploration: read 6 different files, then edit+test", False,
     sum([pair("Read", {"file_path": f}) for f in
          ["main.py", "db/models.py", "api/routes.py",
           "auth/session.py", "utils/log.py", "config.py"]], [])
     + pair("Edit", {"file_path": "auth/session.py"})
     + pair("Bash", {"command": "pytest -q"}, "ok")),
    ("HEALTHY same test re-run after each edit (legit repeats)", False,
     sum([pair("Edit", {"file_path": "a.py"})
          + pair("Bash", {"command": "pytest -q"}, "1 failed") for _ in range(3)], [])
     + pair("Bash", {"command": "pytest -q"}, "all passed")),
]


def run_config(judge_mode):
    os.environ["DEJALOOP_HOME"] = tempfile.mkdtemp(prefix="bench-")
    os.environ["DEJALOOP_MODE"] = "enforce"
    if judge_mode:
        os.environ["DEJALOOP_JEV"] = judge_mode
    else:
        # Explicit "off": unset would now select the default LocalJudge.
        os.environ["DEJALOOP_JEV"] = "off"
    from dejaloop import hook
    results = []
    for name, is_stuck, steps in SCENARIOS:
        sid = "bench-" + str(abs(hash(name)) % 99999)
        flagged = False
        for step in steps:
            buf = io.StringIO()
            with redirect_stdout(buf):
                hook.handle(dict(step, session_id=sid))
            out = buf.getvalue()
            if "DejaLoop" in out:
                flagged = True
        state_file = os.path.join(os.environ["DEJALOOP_HOME"], "sessions", f"{sid}.json")
        if os.path.exists(state_file):
            st = json.load(open(state_file))
            # 'observed' log lines don't count — only real interventions
            real = [i for i in st.get("interventions", [])
                    if i.get("action") not in ("observed",)]
            if real:
                flagged = True
        correct = (flagged == is_stuck)
        results.append((name, is_stuck, flagged, correct))
    return results


def main():
    for label, mode in [("deterministic only", None),
                        ("+ LocalJudge (zero-cost)", "local"),
                        ("+ MockJev (toy, reference)", "mock")]:
        res = run_config(mode)
        tp = sum(1 for _, s, f, _ in res if s and f)
        fp = sum(1 for _, s, f, _ in res if not s and f)
        fn = sum(1 for _, s, f, _ in res if s and not f)
        print(f"\n### {label}: caught {tp}/4 stuck, false alarms {fp}/4 healthy")
        for name, s, f, ok in res:
            mark = "OK " if ok else "MISS"
            print(f"  [{mark}] {'stuck' if s else 'healthy'} | flagged={f} | {name}")


if __name__ == "__main__":
    main()
