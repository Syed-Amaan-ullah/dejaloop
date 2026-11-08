"""Unit + integration tests driving the real hook handler with simulated
Claude Code payloads (the same JSON Claude Code sends on stdin)."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DEJALOOP_HOME"] = tempfile.mkdtemp(prefix="dejaloop-test-")
os.environ["DEJALOOP_JEV"] = "mock"
os.environ["DEJALOOP_MODE"] = "enforce"

from dejaloop import cli, hook                 # noqa: E402
from dejaloop.core import Config, decide_action  # noqa: E402
from dejaloop.jev import (LocalJudge, MockJev,  # noqa: E402
                            TypeSafeJev, get_client)
from dejaloop.statusline import render         # noqa: E402


@contextmanager
def patched_env(**updates):
    """Set env vars (value None removes the var), restoring originals after."""
    saved = {k: os.environ.get(k) for k in updates}
    try:
        for k, v in updates.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run(payload):
    buf = io.StringIO()
    with redirect_stdout(buf):
        hook.handle(dict(payload))
    txt = buf.getvalue().strip()
    return json.loads(txt) if txt.startswith("{") else {}


def pre(sid, tool, tin):
    return {"hook_event_name": "PreToolUse", "session_id": sid,
            "tool_name": tool, "tool_input": tin}


def post(sid, tool, tin, resp="ok"):
    return {"hook_event_name": "PostToolUse", "session_id": sid,
            "tool_name": tool, "tool_input": tin, "tool_response": resp}


class TestDeterministicBrake(unittest.TestCase):
    def test_repeated_identical_call_is_denied(self):
        sid = "t-repeat"
        for _ in range(3):
            run(pre(sid, "Read", {"file_path": "a.py"}))
            run(post(sid, "Read", {"file_path": "a.py"}))
        out = run(pre(sid, "Read", {"file_path": "a.py"}))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_varied_calls_are_allowed(self):
        sid = "t-varied"
        for i in range(5):
            out = run(pre(sid, "Read", {"file_path": f"f{i}.py"}))
            self.assertNotIn("hookSpecificOutput", out)
            run(post(sid, "Read", {"file_path": f"f{i}.py"}))

    def test_shadow_mode_never_denies(self):
        os.environ["DEJALOOP_MODE"] = "shadow"
        try:
            sid = "t-shadow"
            for _ in range(4):
                run(pre(sid, "Read", {"file_path": "a.py"}))
                run(post(sid, "Read", {"file_path": "a.py"}))
            out = run(pre(sid, "Read", {"file_path": "a.py"}))
            self.assertNotIn("hookSpecificOutput", out)
        finally:
            os.environ["DEJALOOP_MODE"] = "enforce"


class TestDoneClaim(unittest.TestCase):
    def test_stop_blocked_without_verification(self):
        sid = "t-stop-bad"
        run(post(sid, "Write", {"file_path": "x.py"}))
        out = run({"hook_event_name": "Stop", "session_id": sid})
        self.assertEqual(out.get("decision"), "block")

    def test_stop_allowed_after_tests_pass(self):
        sid = "t-stop-good"
        run(post(sid, "Write", {"file_path": "x.py"}))
        run(post(sid, "Bash", {"command": "pytest -q"}, "3 passed"))
        out = run({"hook_event_name": "Stop", "session_id": sid})
        self.assertNotEqual(out.get("decision"), "block")


class TestPolicyAndFailOpen(unittest.TestCase):
    def test_policy_thresholds(self):
        cfg = Config()
        self.assertEqual(decide_action(0.49, cfg), "continue")
        self.assertEqual(decide_action(0.50, cfg), "warn")
        self.assertEqual(decide_action(0.75, cfg), "replan")
        self.assertEqual(decide_action(0.90, cfg), "halt")

    def test_broken_payload_does_not_raise(self):
        # handle() must never raise: Claude Code sessions depend on fail-open
        run({"hook_event_name": "PostToolUse", "session_id": "t-x",
             "tool_name": "Bash", "tool_input": None, "tool_response": 12345})
        run({"hook_event_name": "Nonsense", "session_id": "t-x"})

    def test_statusline_renders(self):
        line = render(json.dumps({"cost": {"total_cost_usd": 1.5}}))
        self.assertIn("DejaLoop", line)
        self.assertIn("$1.50", line)


class TestLocalJudge(unittest.TestCase):
    def setUp(self):
        self.judge = LocalJudge()

    def test_tdd_pattern_scores_low(self):
        # Failures interleaved with edits are progress (TDD), not a loop.
        v = self.judge.evaluate_stall("", {"streak_same": 0, "fail_streak": 1,
                                           "no_progress_steps": 1,
                                           "similarity": 0.5, "edits": 3})
        self.assertLess(v["stuck"], 0.50)
        self.assertEqual(v["progress"], "progressing")

    def test_failing_without_edits_scores_high(self):
        v = self.judge.evaluate_stall("", {"streak_same": 0, "fail_streak": 4,
                                           "no_progress_steps": 6,
                                           "similarity": 0.8, "edits": 0})
        self.assertGreaterEqual(v["stuck"], 0.50)

    def test_thrash_floor_lifts_similar_no_edit_circling(self):
        # No failures, no exact repeats — just near-identical searches,
        # zero edits: the floor must lift this into warn territory.
        v = self.judge.evaluate_stall("", {"streak_same": 0, "fail_streak": 0,
                                           "no_progress_steps": 6,
                                           "similarity": 0.9, "edits": 0})
        self.assertGreaterEqual(v["stuck"], 0.55)

    def test_varied_exploration_stays_low(self):
        # Same step count, but low similarity = real exploration, not thrash.
        v = self.judge.evaluate_stall("", {"streak_same": 0, "fail_streak": 0,
                                           "no_progress_steps": 6,
                                           "similarity": 0.2, "edits": 0})
        self.assertLess(v["stuck"], 0.50)


class TestConfigLoad(unittest.TestCase):
    def test_loads_values_from_config_file(self):
        tmp = tempfile.mkdtemp(prefix="dejaloop-cfg-")
        with open(os.path.join(tmp, "config.json"), "w") as f:
            json.dump({"mode": "shadow", "repeat_limit": 7, "warn_at": 0.42}, f)
        with patched_env(DEJALOOP_HOME=tmp, DEJALOOP_MODE=None):
            cfg = Config.load()
        self.assertEqual(cfg.mode, "shadow")
        self.assertEqual(cfg.repeat_limit, 7)
        self.assertAlmostEqual(cfg.warn_at, 0.42)
        # Untouched fields keep their defaults.
        self.assertEqual(cfg.halt_at, 0.90)

    def test_broken_config_falls_back_to_defaults(self):
        tmp = tempfile.mkdtemp(prefix="dejaloop-cfg-")
        with open(os.path.join(tmp, "config.json"), "w") as f:
            f.write("{not json")
        with patched_env(DEJALOOP_HOME=tmp, DEJALOOP_MODE=None):
            cfg = Config.load()
        self.assertEqual(cfg.repeat_limit, 3)
        self.assertEqual(cfg.mode, "shadow")


class TestGetClient(unittest.TestCase):
    def check(self, env, expect):
        with patched_env(**env):
            client = get_client(Config())
        if expect is None:
            self.assertIsNone(client)
        else:
            self.assertIsInstance(client, expect)

    def test_off_and_none_disable_judge(self):
        self.check({"DEJALOOP_JEV": "off", "TYPESAFE_API_KEY": None}, None)
        self.check({"DEJALOOP_JEV": "none", "TYPESAFE_API_KEY": None}, None)

    def test_off_wins_over_api_key(self):
        self.check({"DEJALOOP_JEV": "off", "TYPESAFE_API_KEY": "sk-test"}, None)

    def test_explicit_local_and_mock(self):
        self.check({"DEJALOOP_JEV": "local", "TYPESAFE_API_KEY": None}, LocalJudge)
        self.check({"DEJALOOP_JEV": "mock", "TYPESAFE_API_KEY": None}, MockJev)

    def test_default_is_local_judge_without_key(self):
        # The v1 default: no env, no key -> built-in LocalJudge, not None.
        self.check({"DEJALOOP_JEV": None, "TYPESAFE_API_KEY": None}, LocalJudge)

    def test_api_key_selects_typesafe(self):
        self.check({"DEJALOOP_JEV": None, "TYPESAFE_API_KEY": "sk-test"},
                   TypeSafeJev)


class _ExplodingJudge:
    def evaluate_stall(self, text, signals):
        raise RuntimeError("judge blew up")


class TestJudgeFailOpen(unittest.TestCase):
    def test_hook_survives_judge_exception(self):
        original = hook.get_client
        hook.get_client = lambda cfg: _ExplodingJudge()
        try:
            sid = "t-explode"
            out = {}
            for i in range(5):  # the 5th PostToolUse triggers a judge check
                out = run(post(sid, "Read", {"file_path": f"f{i}.py"}))
            self.assertEqual(out, {})  # no output, no block, no raise
            state_path = os.path.join(os.environ["DEJALOOP_HOME"],
                                      "sessions", f"{sid}.json")
            with open(state_path) as f:
                state = json.load(f)
            self.assertEqual(len(state["calls"]), 5)  # calls still recorded
            self.assertEqual(state["pending_action"], "")  # nothing queued
        finally:
            hook.get_client = original


class TestCli(unittest.TestCase):
    def test_init_creates_config_and_status_reports(self):
        tmp = tempfile.mkdtemp(prefix="dejaloop-cli-")
        with patched_env(DEJALOOP_HOME=tmp, DEJALOOP_JEV=None,
                         TYPESAFE_API_KEY=None, DEJALOOP_MODE=None):
            out = cli.init_cmd()
            self.assertTrue(os.path.exists(os.path.join(tmp, "config.json")))
            self.assertIn("LocalJudge", out)  # default judge, no key present
            out2 = cli.init_cmd()  # second run must not clobber the config
            self.assertIn("already exists", out2)
            status = cli.status_cmd()
            self.assertIn("Interventions recorded: 0", status)
            self.assertIn("LocalJudge", status)


class TestSavings(unittest.TestCase):
    def _loop_session(self, sid):
        for _ in range(3):
            run(pre(sid, "Read", {"file_path": "a.py"}))
            run(post(sid, "Read", {"file_path": "a.py"}))
        run(pre(sid, "Read", {"file_path": "a.py"}))  # this one gets denied

    def test_stopped_loop_counts_estimated_savings(self):
        from dejaloop.core import home_dir
        self._loop_session("t-save")
        state = json.load(open(os.path.join(
            home_dir(), "sessions", "t-save.json")))
        # one denied call = 10 avoided repeats x $0.05 by default
        self.assertGreaterEqual(state.get("est_saved_usd", 0), 0.5)
        totals = json.load(open(os.path.join(home_dir(), "totals.json")))
        self.assertGreater(totals["est_saved_usd"], 0)
        self.assertGreaterEqual(totals["blocks"], 1)

    def test_statusline_shows_saved_amount(self):
        self._loop_session("t-save-line")
        line = render(json.dumps({"cost": {"total_cost_usd": 2.0}}))
        self.assertIn("saved ~$", line)


if __name__ == "__main__":
    unittest.main(verbosity=2)
