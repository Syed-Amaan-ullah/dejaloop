# DejaLoop — Setup

> **DejaLoop** is a working codename; the final name is still to be
> decided. `<owner>` below is a placeholder for the GitHub handle the
> project is published under.

Target: instuck and running in under 2 minutes. No account, no server,
and — with the default judge — no API key.

## Requirements

- Claude Code with plugin support
- Python 3.10+ available as `python3` on your PATH (DejaLoop is
  standard-library only; there is nothing to pip-install)

## Install

Inside Claude Code:

```
/plugin marketplace add <owner>/dejaloop
/plugin install dejaloop@dejaloop
```

Then restart Claude Code (or start a new session) so the hooks load.
That's it — the plugin registers four hooks (`UserPromptSubmit`,
`PreToolUse`, `PostToolUse`, `Stop`) that invoke the DejaLoop hook
module on every event.

### Verify it's alive

- Start a session and look at the bottom of the terminal: the status line
  reads `DejaLoop ● healthy | session $0.00 | checks 0 | interventions 0`
  and updates as the session runs.
- Or run the built-in demo — four scripted sessions fed through the real
  hook handler, no Claude Code session needed:

```bash
python3 -m dejaloop.cli demo
```

## First week: shadow mode, then enforce

DejaLoop has two modes:

- **shadow** — warns and logs, **never blocks anything**. You see what it
  *would* have done.
- **enforce** — warnings are injected into the session, stuck calls are
  denied (replan) or surfaced to you (halt), and unverified "done" claims
  are blocked.

**Recommended rollout:** run your first week in shadow mode. Then read
your ledger (below), confirm the interventions it logged were real
stuck sessions — and that it stayed quiet during your healthy sessions — and
only then switch to enforce. Shadow-mode logs are also the data used to
tune the thresholds, so the week isn't just caution, it's calibration.

Set the mode in `~/.dejaloop/config.json`:

```json
{ "mode": "shadow" }
```

…and change `"shadow"` to `"enforce"` when you're ready. The
`DEJALOOP_MODE` environment variable overrides the file (handy for a
one-off session):

```bash
DEJALOOP_MODE=enforce claude
```

## Configuration

Configuration is layered: built-in defaults ← `~/.dejaloop/config.json`
← environment variables.

### Environment variables

| Variable | Values | Purpose |
|---|---|---|
| `DEJALOOP_JEV` | `local` (default), `typesafe`, `mock` | Selects the judge. See [JUDGES.md](JUDGES.md). |
| `DEJALOOP_MODE` | `shadow`, `enforce` | Overrides the mode from `config.json`. |
| `DEJALOOP_HOME` | any path | Where state lives. Default `~/.dejaloop`. Useful for tests and for keeping separate profiles. |
| `TYPESAFE_API_KEY` | your key | Only needed for the Jev judge. Setting it (without `DEJALOOP_JEV`) also selects Jev. Never committed anywhere — it is read from your environment at call time. **Simpler alternative:** run `dejaloop set-key` once and the key is stored in `~/.dejaloop/credentials.json` (0600 permissions) instead — no env var needed. |

### `~/.dejaloop/config.json`

Every field is optional; anything omitted keeps its default.

| Key | Default | Meaning |
|---|---|---|
| `mode` | `shadow` | `shadow` or `enforce` (see above — start with `shadow`, switch to `enforce` when ready). |
| `warn_at` | `0.50` | Chance it's stuck that triggers a warning. |
| `replan_at` | `0.75` | Chance it's stuck that denies the next call and demands a new plan. |
| `halt_at` | `0.90` | Chance it's stuck that stops and asks you. |
| `repeat_limit` | `3` | Identical calls in a row before the deterministic brake trips. |
| `fail_limit` | `2` | Consecutive `Bash` failures tolerated before a fail-loop alert. |
| `check_every` | `5` | Judge is consulted at least every N tool calls (and immediately on any deterministic alert). |
| `jev_timeout_s` | `2.0` | Jev request timeout. On timeout the session continues unchecked (fail-open). |

## CLI commands

The CLI module is `dejaloop.cli`:

```bash
python3 -m dejaloop.cli init     # first-time setup: pick judge + mode, write ~/.dejaloop/config.json
python3 -m dejaloop.cli status   # show active judge, mode, state location, sessions & interventions on record
python3 -m dejaloop.cli report   # print the most recent interventions from ~/.dejaloop/ledger.jsonl
python3 -m dejaloop.cli demo     # run the 4 scripted demo sessions (no keys, no Claude Code needed)
```

`report` is the command you'll use most: after a shadow-mode week, it's
your evidence for switching to enforce.

## Choosing a judge

The judge is the component that scores "is this agent stuck?" Full
comparison in [JUDGES.md](JUDGES.md); the short version:

- **`local` (default)** — the built-in LocalJudge. Zero cost, offline, no
  key, nothing leaves your machine. This is what you get out of the box.
- **`typesafe`** — TypeSafe Jev, a general trained decision model, as an
  optional upgrade for subtle subtle stuck cases. Bring your own key:

  ```bash
  export DEJALOOP_JEV=typesafe
  export TYPESAFE_API_KEY=<your key>
  ```

  Jev pricing is $0.042 per million input tokens with output free; a
  DejaLoop check sends ~360 tokens, so even a $5 credit covers
  thousands of sessions (math in [JUDGES.md](JUDGES.md)).
- **`mock`** — a deterministic test double for development and the demo.
  Never use it for real judgments.

Switching judges needs no reinstall — it's one environment variable,
picked up on the next hook call.

## Where things live

```
~/.dejaloop/
  config.json     # your overrides (created by init, or by hand)
  ledger.jsonl    # every intervention, append-only
  sessions/       # per-session state files
```

## Troubleshooting

- **Nothing in the status line / no interventions ever.** Check the
  plugin is instuck (`/plugin list`) and that you restarted Claude
  Code after installing. Confirm `python3` is on your PATH.
- **DejaLoop seems to do nothing during a stuck session.** If you're in shadow
  mode, that's by design — check `report` to see what it logged. If
  you're expecting judge checks, confirm `DEJALOOP_JEV` isn't set to
  `mock`.
- **Jev selected but never fires.** `TYPESAFE_API_KEY` must be set in
  the environment Claude Code was launched from. Jev failures are
  silent by design (fail-open) — the session never breaks, the check is
  simply skipped.
- **Too eager / too quiet.** Tune `warn_at` / `replan_at` / `halt_at`
  in `config.json`, and bring your ledger to the discussion — see
  [TESTING.md](TESTING.md) for how the thresholds were benchmarked.
- **Reset everything.** Delete `~/.dejaloop/` (or point
  `DEJALOOP_HOME` elsewhere). Sessions in progress start fresh.
