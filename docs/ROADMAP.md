# DejaLoop — Roadmap

> **DejaLoop** is a working codename. The final name is the
> maintainer's decision and is **pending** — it gates the public launch,
> not the engineering. (The earlier working name, "LoopBrake", turned
> out to be taken by multiple existing projects.)

DejaLoop today: a working Claude Code plugin — deterministic loop
detection, a pluggable judge layer with a zero-cost local judge as the
default, warn/replan/halt policy, an unverified-done-claim guard, a
status line, and a full simulated-payload test suite. What follows is
what's missing, in the order it unblocks.

## Next: prove it in the real world

### 1. Real-session validation
Nothing has run inside a live Claude Code session yet (no Claude CLI on
the build machine; everything so far is verified against the documented
hook contract with simulated payloads). First live pass:

- Install via the plugin marketplace flow exactly as a user would.
- Confirm real payload shapes for every tool, status-line rendering,
  and the deny/ask/block UX in the actual terminal.
- Run one deliberately looped session and one normal working session;
  compare behaviour against the simulated results.

### 2. Live Jev calibration
The Jev client is implemented against the documented System One API
but has never made a live call (no API key yet). With a bring-your-own
key:

- Run the demo scenarios and both benchmark suites against real Jev.
- Fill in Jev's empty row in the [benchmark](JUDGES.md#head-to-head-benchmark).
- Calibrate the policy thresholds (0.50 / 0.75 / 0.90) against real Jev
  probability distributions — today they are sensible defaults, not
  measured values.
- Decide from data whether Jev earns the "upgrade" label, and for
  which kinds of loops.

### 3. Shadow-log-driven tuning
The real dataset is the ledger from shadow-mode use on real sessions
(`~/.dejaloop/ledger.jsonl` — what was flagged, what was missed, what
was noise). Use it to:

- Tune LocalJudge's feature weights and the thrash floor against
  unscripted work, not just scenarios.
- Grow the held-out benchmark with real (anonymised) stuck-session traces —
  new held-out cases only; never tune against them after adding.
- Revisit `check_every`, `repeat_limit`, and `fail_limit` defaults.

## Then: widen the surface

### 4. v1.1 — Codex adapter
DejaLoop's core (state, signals, judges, policy) is agent-agnostic;
only the hook layer is Claude Code–specific. The Codex adapter maps
the same lifecycle onto Codex's hooks/events so one install guards
both agents. This is the planned v1.1 headline: the competing tools in
this space are single-agent, and cross-agent coverage is the open
lane.

### 5. Name decision → public launch
Once the maintainer picks the final name:

- Rename pass (plugin manifest, status line, docs, codename
  references).
- Push to GitHub under the maintainer's account (publishing needs
  their sign-in; the repo is local until then).
- Launch sequence across the Jev and Claude Code communities, with the
  benchmark tables and demo as the evidence.

## Later / under consideration

- **Additional judge transports** — e.g. Jev via OpenRouter for users
  who already keep credit there.
- **More judges behind the interface** — the judge slot is deliberately
  generic; any scorer that returns a chance it's stuck can compete in
  the benchmark.
- **Richer trajectory context for judges** — more than the last 8 calls
  when a loop is suspected, balanced against per-check cost (the math
  in [JUDGES.md](JUDGES.md#jev-cost-math) has ample headroom).
- **Session cost-saved estimate** — surfacing "~$X of runaway spend
  avoided" in the status line/report, computed from interventions and
  session burn rate. Only if it can be computed honestly.

## Explicit non-goals (for now)

- No dashboard or hosted SaaS — DejaLoop is local by design.
- No process-killing — intervention happens through the agent's own
  hook contract (warn / deny / ask), never by force.
- No context compaction — a different problem, already served by other
  tools.
- No general Jev clone — LocalJudge stays a narrow stuck-spotter; depth
  comes from the pluggable Jev upgrade, not from rebuilding a decision
  model.
