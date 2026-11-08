# DejaLoop — Architecture

> **DejaLoop** is a working codename. The final product name is still to be
> decided; nothing in the design depends on the name.

DejaLoop is a Claude Code plugin that watches a coding-agent session
*live*, decides whether the agent is stuck or looping, and intervenes
inside the session — before more tokens burn — instead of reporting on the
damage afterwards.

It is built from three layers:

1. **Deterministic layer** — local, instant, free. Fingerprints and pattern
   signals over the tool-call history.
2. **Judge layer** — a pluggable scorer that turns a session trajectory into
   a chance it's stuck (0–1). The default judge is a local, zero-cost
   pattern scorer; TypeSafe Jev is an optional upgrade. See
   [JUDGES.md](JUDGES.md).
3. **Policy layer** — fixed thresholds that map a chance it's stuck to an
   action: continue, warn, replan, or halt-and-ask.

Everything is Python standard library only. There is no server, no database,
and no account. All state lives on the user's machine.

---

## Components

| Component | File | Responsibility |
|---|---|---|
| Hook entry point | `dejaloop/hook.py` | Implements the Claude Code hook contract for `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, and `Stop`. Routes each payload, emits decisions. |
| Core | `dejaloop/core.py` | Session state, call fingerprints, deterministic signals, config loading, the intervention ledger, and the policy function. No network calls. |
| Judges | `dejaloop/jev.py` | The judge interface (`evaluate_stall`) and its implementations: `LocalJudge` (default), `TypeSafeJev` (optional), `MockJev` (test double). Client selection from the environment. |
| Status line | `dejaloop/statusline.py` | Renders the one-line session health summary Claude Code shows at the bottom of the terminal. |
| CLI | `dejaloop/cli.py` | `demo` (scripted sessions through the real handler) and `report` (intervention ledger). Setup/status helpers are covered in [SETUP.md](SETUP.md). |
| Plugin packaging | `.claude-plugin/plugin.json`, `hooks/hooks.json` | Plugin manifest and hook registrations: all four events invoke `python3 -m dejaloop.hook` (5s timeout, 10s for `PostToolUse`). |

### Signals computed by the core

All signals are derived from the recorded call history — no extra data is
collected:

- **Fingerprint** — truncated SHA-256 of `{tool_name, tool_input}`. Identical
  calls produce identical fingerprints.
- **Streak** — how many times in a row the most recent call has repeated.
- **Failure streak** — consecutive failed `Bash` calls (failure is detected
  best-effort from the tool response: error flags, non-zero exit codes, or
  markers such as `Traceback` / `error:` / `failed` in the output).
- **No-progress steps** — calls since the last file edit
  (`Write` / `Edit` / `NotebookEdit`).
- **Edits / verification runs** — counts of edit calls and of successful
  test/build/lint commands (matched against a pattern list: pytest, jest,
  vitest, `go test`, `cargo test`, `npm test`, `tsc`, eslint, …).
- **Recent similarity** — average Jaccard similarity between consecutive
  recent call inputs. ~1.0 means the agent keeps doing near-identical things
  even when the calls aren't byte-identical (so fingerprints miss it); ~0
  means varied work.

### Deterministic alerts

Two patterns are recognised without any judge:

- **Repeat** — the same call has run `repeat_limit` (default 3) times in a row.
- **Fail loop** — `Bash` has failed more than `fail_limit` (default 2) times
  in a row.

---

## Data flow of a hook call

Claude Code runs the hook as a subprocess for each event, passing one JSON
object on **stdin** and reading a JSON decision from **stdout**. DejaLoop's
handler (`hook.handle`) works the same way for every event:

1. Load config (`Config.load`) and the session's saved state.
2. Dispatch on `hook_event_name`.
3. Persist state, and print at most one JSON decision object.

### `UserPromptSubmit`

Records the user's prompt (truncated to 500 chars) as the session's task.
The task is part of the trajectory a judge later reads. No output.

### `PreToolUse` — where blocking happens

Runs *before* a tool executes, in this order:

1. **Apply a queued semantic action.** If the last judge check queued a
   REPLAN or HALT (see below), it lands here:
   - REPLAN → `permissionDecision: "deny"`, with the reason fed back to the
     agent plus an instruction to present a new plan.
   - HALT → `permissionDecision: "ask"`, surfacing the decision to the user.
   - In shadow mode the action is logged instead and the call proceeds.
2. **Deterministic hard repeat.** If the identical call is being attempted
   again after already running `repeat_limit` times in a row, it is denied
   in enforce mode (logged as a warning in shadow mode).
3. Otherwise the call is allowed silently (no output).

### `PostToolUse` — where judging happens

Runs *after* a tool executes:

1. Append the call record (fingerprint, tool, input, failed?) to the
   session history. Only the last **50** calls are kept.
2. Compute the deterministic alert (repeat / fail loop).
3. A judge check is **due** when a deterministic alert fired, or every
   `check_every` (default 5) tool calls — whichever comes first.
4. If a check is due and a judge is configured, the judge receives:
   - a **trajectory text**: the task, the last 8 calls (inputs truncated to
     160 chars, marked ok/FAILED), and the edit/verification totals; and
   - the **signal dict**: streak, failure streak, no-progress steps, recent
     similarity, edit count.
5. The returned chance it's stuck goes through policy:
   - **warn** → a `systemMessage` is emitted immediately, injecting the
     warning into the session.
   - **replan / halt** → stored as a *pending action* on the session state;
     it is applied at the next `PreToolUse` (step 1 above).
   - **continue** → nothing happens.
6. If no judge is configured and a deterministic alert fired, the alert is
   logged as `observed` in the ledger.

### `Stop` — the done-claim check

When the agent tries to finish:

- If the session contains **edits but zero successful verification runs**
  (no test, build, or lint ever passed), the stop is blocked in enforce
  mode with `{"decision": "block", "reason": …}` — the agent is sent back
  to run a verification command. In shadow mode it logs and warns instead.
- Otherwise the stop is allowed.

This check is purely deterministic; no judge is consulted.

---

## Policy

`decide_action` in `core.py` maps a judge's chance it's stuck to an action.
The thresholds are configuration, not constants — they can be tuned in
`~/.dejaloop/config.json`.

| Chance it's stuck | Action | What happens |
|---|---|---|
| < 0.50 | **continue** | Nothing. The session proceeds silently. |
| 0.50 – 0.75 | **warn** | A `[DejaLoop]` message is injected into the session via `systemMessage`. Logged. |
| 0.75 – 0.90 | **replan** | The *next* tool call is denied (`PreToolUse` deny); the denial reason tells the agent to present a new plan. |
| ≥ 0.90 | **halt** | The next tool call is surfaced to the user (`PreToolUse` ask) instead of running. |

Two independent mechanisms sit outside this table:

- The **deterministic hard repeat** deny (identical call at the repeat
  limit) does not need a judge score.
- The **Stop-hook done-claim block** does not use probabilities at all.

### Modes

- **enforce** — warnings are injected, replans deny, halts ask, unverified
  stops are blocked.
- **shadow** — DejaLoop observes, warns, and logs, but **never blocks
  anything**: no denies, no asks, no blocked stops. This is the recommended
  way to run your first week (see [SETUP.md](SETUP.md)); the ledger it
  produces is the data used to tune thresholds before enforcing.

---

## State storage

Everything lives under the DejaLoop home directory — `~/.dejaloop` by
default, overridable with the `DEJALOOP_HOME` environment variable:

```
~/.dejaloop/
  config.json            # optional overrides (mode, thresholds, limits)
  ledger.jsonl           # append-only log of every intervention
  sessions/
    <session_id>.json    # one file per Claude Code session
```

**Session state** (`sessions/<session_id>.json`) holds: the task text, the
call history (last 50 calls), per-fingerprint pre-tool counts, the
intervention list for the session, any pending replan/halt action, and the
call index of the last judge check. Writes are atomic (write to a temp file,
then replace), so a crash mid-write can't corrupt a session.

**The ledger** (`ledger.jsonl`) is the cross-session record: one JSON line
per intervention with timestamp, session id, kind (`deterministic`,
`semantic`, `done_claim`), action, and the human-readable reason. It backs
`python3 -m dejaloop.cli report` and is the raw material for threshold
tuning.

Nothing is uploaded anywhere by DejaLoop itself. The only data that can
leave the machine is the trajectory text sent to TypeSafe when — and only
when — the Jev judge is explicitly selected (see [JUDGES.md](JUDGES.md)).

---

## Fail-open design

DejaLoop sits in the path of every tool call, so its first design rule
is: **a DejaLoop failure must never break, block, or crash a session.** A
guard that can brick your work is worse than no guard. This is enforced at
every layer:

- **The hook process never fails.** `hook.main` wraps everything in a
  catch-all: any exception results in exit code 0 with no output, which
  Claude Code treats as "no opinion — proceed".
- **Judge failures are ignored.** If the judge raises, times out (the Jev
  client defaults to a 2-second timeout), or is unreachable, the verdict is
  discarded and the session continues on the deterministic layer alone.
- **A broken config is ignored.** If `config.json` can't be parsed, the
  defaults are used.
- **Corrupt session state is discarded.** If a session file can't be loaded,
  a fresh state is started rather than erroring.
- **No key, no problem.** With no judge available, checks are skipped and
  only deterministic alerts are logged.

The test suite covers this explicitly: malformed payloads (null inputs,
nonsense event names, non-string responses) must never raise. See
[TESTING.md](TESTING.md).
