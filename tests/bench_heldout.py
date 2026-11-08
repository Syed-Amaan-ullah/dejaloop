"""Held-out benchmark for DejaLoop judges — written 2026-11-07, AFTER
LocalJudge was tuned on the original 8 scenarios in bench_judges.py.

These 12 scenarios are NEW (different tools/commands/patterns) and were
NOT used to tune LocalJudge. Do not tune against this file — if a judge
misses here, that is the honest generalisation result. A 'flag' is any
real intervention (warn or stronger). Healthy scenarios must NOT flag.
"""
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
NETFAIL = "Error: Could not resolve host / network unreachable"

SCENARIOS = [
    # ---- stuck (must flag) ----
    ("STUCK install loop: pip/yarn/pnpm all fail, no edits", True,
     sum([pair("Bash", {"command": c}, NETFAIL) for c in
          ["pip install requests", "pip install -U requests",
           "yarn add requests", "pnpm add requests",
           "pip install requests==2.31", "pip3 install requests"]], [])),
    ("STUCK import-name guessing, no edits", True,
     sum([pair("Bash", {"command": c}, "Error: ModuleNotFoundError") for c in
          ["python -c 'import foo'", "python -c 'import foo2'",
           "python -c 'import myfoo'", "python -c 'import foo_lib'",
           "python -c 'import foopkg'", "python -c 'import foo_core'"]], [])),
    ("STUCK re-fetching same docs URL, no edits", True,
     sum([pair("WebFetch", {"url": "https://example.com/docs/auth"}) for _ in range(6)], [])),
    ("STUCK build flags loop, all failing, no edits", True,
     sum([pair("Bash", {"command": c}, FAIL) for c in
          ["npm run build", "npm run build -- --prod", "npm run build --watch",
           "npx tsc --noEmit", "npm run build -- --minify",
           "npm run build -- --sourcemap"]], [])),
    ("STUCK git checkout/stash cycling, no edits", True,
     sum([pair("Bash", {"command": c}, "Error: Your local changes would be overwritten") for c in
          ["git checkout main", "git stash", "git checkout main",
           "git stash pop", "git checkout main", "git stash"]], [])),
    ("STUCK same lint error, re-running linter with new flags", True,
     sum([pair("Bash", {"command": c}, "Error: lint failed: 12 errors") for c in
          ["npx eslint .", "npx eslint src/", "npx eslint --fix .",
           "npx eslint src/ --ext .ts", "npx eslint . --quiet",
           "npx eslint src/ --no-eslintrc"]], [])),
    # ---- healthy (must NOT flag) ----
    ("HEALTHY long exploration: 8 files, then Write + test pass", False,
     sum([pair("Read", {"file_path": f}) for f in
          ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py", "g.py", "h.py"]], [])
     + pair("Write", {"file_path": "new.py"})
     + pair("Bash", {"command": "pytest -q"}, "2 passed")),
    ("HEALTHY refactor: edits across files, tests pass", False,
     pair("Edit", {"file_path": "x.py"}) + pair("Edit", {"file_path": "y.py"})
     + pair("Edit", {"file_path": "z.py"})
     + pair("Bash", {"command": "pytest -q"}, "9 passed")),
    ("HEALTHY debug: 4 fail-edit cycles, then pass", False,
     sum([pair("Edit", {"file_path": "calc.py"})
          + pair("Bash", {"command": "pytest -q"}, FAIL) for _ in range(4)], [])
     + pair("Edit", {"file_path": "calc.py"})
     + pair("Bash", {"command": "pytest -q"}, "all passed")),
    ("HEALTHY search phase: varied greps, then edit + test", False,
     sum([pair("Grep", {"pattern": p}) for p in
          ["TODO auth", "session expiry", "refresh token", "cookie domain",
           "logout handler", "token revoke"]], [])
     + pair("Edit", {"file_path": "auth.py"})
     + pair("Bash", {"command": "pytest -q"}, "ok")),
    ("HEALTHY build fails once, edit, build passes", False,
     pair("Bash", {"command": "npm run build"}, FAIL)
     + pair("Edit", {"file_path": "src/index.ts"})
     + pair("Bash", {"command": "npm run build"}, "built in 2.1s")),
    ("HEALTHY config edit, test re-run passes", False,
     pair("Read", {"file_path": "config.yaml"})
     + pair("Edit", {"file_path": "config.yaml"})
     + pair("Bash", {"command": "pytest -q"}, "4 passed")),
]


def run_config(judge_mode):
    os.environ["DEJALOOP_HOME"] = tempfile.mkdtemp(prefix="heldout-")
    os.environ["DEJALOOP_MODE"] = "enforce"
    if judge_mode:
        os.environ["DEJALOOP_JEV"] = judge_mode
    else:
        os.environ["DEJALOOP_JEV"] = "off"
    from dejaloop import hook
    results = []
    for name, is_stuck, steps in SCENARIOS:
        sid = "heldout-" + str(abs(hash(name)) % 99999)
        flagged = False
        for step in steps:
            buf = io.StringIO()
            with redirect_stdout(buf):
                hook.handle(dict(step, session_id=sid))
            if "DejaLoop" in buf.getvalue():
                flagged = True
        state_file = os.path.join(os.environ["DEJALOOP_HOME"], "sessions", f"{sid}.json")
        if os.path.exists(state_file):
            st = json.load(open(state_file))
            real = [i for i in st.get("interventions", [])
                    if i.get("action") not in ("observed",)]
            if real:
                flagged = True
        results.append((name, is_stuck, flagged, flagged == is_stuck))
    return results


def main():
    for label, mode in [("deterministic only", None),
                        ("+ LocalJudge (zero-cost)", "local"),
                        ("+ MockJev (toy, reference)", "mock")]:
        res = run_config(mode)
        tp = sum(1 for _, s, f, _ in res if s and f)
        fp = sum(1 for _, s, f, _ in res if not s and f)
        print(f"\n### {label}: caught {tp}/6 stuck, false alarms {fp}/6 healthy")
        for name, s, f, ok in res:
            print(f"  [{'OK ' if ok else 'MISS'}] {'stuck' if s else 'healthy'} | flagged={f} | {name}")


if __name__ == "__main__":
    main()
