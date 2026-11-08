# DejaLoop — Testing

> **DejaLoop** is a working codename; the final name is still to be
> decided.

## The core idea: hooks are just JSON

Claude Code hooks receive one JSON object on stdin and answer with one
JSON object on stdout. That makes the whole system testable **without
Claude Code and without any API key**: the test suite builds payloads in
exactly the shape Claude Code sends — `hook_event_name`, `session_id`,
`tool_name`, `tool_input`, `tool_response` — and feeds them through the
*real* handler (`dejaloop.hook.handle`), capturing what it prints.

No mocks of DejaLoop itself. The only test double in the system is
`MockJev`, standing in for the external Jev API (and clearly labelled as
such). Tests run against a throwaway `DEJALOOP_HOME` temp directory,
so real state in `~/.dejaloop` is never touched.

## Run everything

```bash
cd dejaloop

# Unit + integration tests
python3 -m unittest discover -s tests -v

# Scripted demo: 4 sessions through the real handler
python3 -m dejaloop.cli demo

# Judge benchmarks
python3 tests/bench_judges.py     # original 8 labelled scenarios
python3 tests/bench_heldout.py    # 12 held-out scenarios (never tune against this file)
```

All of it runs offline, in well under a second, with no keys.

## What the unit tests cover

The suite in `tests/test_dejaloop.py` is **all passing** (run it for
the current count — it grows as features land). Current coverage:

- **Deterministic brake** — an identical call repeated to the limit is
  denied at the next `PreToolUse`; varied calls are never denied.
- **Shadow mode** — the same runaway loop in shadow mode produces no
  denial, ever.
- **Done-claim check** — a `Stop` after edits with no verification is
  blocked; a `Stop` after a passing test run is allowed.
- **Policy thresholds** — `decide_action` maps 0.49 → continue,
  0.50 → warn, 0.75 → replan, 0.90 → halt.
- **Fail-open** — malformed payloads (null tool input, non-string tool
  response, unknown event names) never raise. This is a hard
  requirement, not a nicety: the hook sits in the path of every tool
  call, and an exception that blocked a session would be worse than the
  loops DejaLoop exists to stop.
- **Status line** — renders the session cost and health summary from a
  Claude Code–shaped stdin payload.

## The demo

`python3 -m dejaloop.cli demo` scripts four sessions end-to-end:

| Scenario | Expected | Result |
|---|---|---|
| Runaway identical loop (same file read 6×) | Calls blocked, escalating warn → replan → halt | 3 calls blocked |
| Semantic failing loop (6 *different* test commands, all failing, zero edits) | Caught and blocked | 4 interventions |
| Healthy session (read → edit → tests pass → stop) | Untouched | 0 blocks, 0 interventions |
| Unverified done claim (edit, no test, stop) | Stop blocked | Stop blocked |

The demo runs with `MockJev` as judge so it works with no key — fine
for proving plumbing and policy, not evidence about a real judge (see
[JUDGES.md](JUDGES.md)).

## The judge benchmarks

`tests/bench_judges.py` and `tests/bench_heldout.py` run labelled
scenarios — stuck ones that **must** be flagged (any intervention,
warn or stronger; mere `observed` log lines don't count) and healthy
ones that **must not** — through each judge configuration:
deterministic-only, LocalJudge, and MockJev. The healthy set is
deliberately adversarial: TDD fail→edit cycles, broad exploration,
legitimate test re-runs.

Current results (full tables and caveats in [JUDGES.md](JUDGES.md)):

- Original 8 scenarios: LocalJudge **4/4 stuck, 0/4 false alarms**;
  deterministic only 1/4 stuck.
- Held-out 12 scenarios (written after tuning, different tools and
  patterns, never tuned against): LocalJudge **6/6 stuck, 0/6 false
  alarms**; deterministic only 1/6 stuck.

## What is NOT tested yet — honestly

1. **A real Claude Code session.** The Claude CLI is not instuck on
   the build machine, so nothing has run end-to-end inside a live
   session. Hook behaviour is verified against the documented Claude
   Code hook contract and simulated payloads only. Exact payload shapes
   for every tool, status-line rendering in the real terminal, and
   plugin install mechanics all still need a live pass on a machine
   with Claude Code and an Anthropic sign-in.
2. **Real Jev.** No TypeSafe API key was available during development.
   The Jev client is implemented against the documented System One API
   (`POST https://api.typesafe.ai/v1/systemone`), but:
   - its accuracy at spotting loops is unmeasured,
   - the policy thresholds (0.50 / 0.75 / 0.90) are uncalibrated
     against real Jev probability distributions,
   - response-shape edge cases can only be found with live calls.
   Calibration means running these same benchmarks and demo scenarios
   against live Jev with a bring-your-own key and tuning from the
   results.
3. **Real-world sessions.** All scenarios so far are scripted. The
   decisive test is shadow mode on real work: does it flag real loops,
   stay quiet on real healthy sessions, and never get in the way? That
   data comes from the ledger (`~/.dejaloop/ledger.jsonl`) once the
   plugin is in daily use.
4. **Publishing mechanics.** The repo is local. The marketplace
   install flow in [SETUP.md](SETUP.md) can only be verified end-to-end
   once the project is pushed to GitHub under the maintainer's account.

Nothing in the results above should be read as covering these four
items. They're the top of the [roadmap](ROADMAP.md) for a reason.
