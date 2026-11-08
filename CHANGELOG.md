# Changelog

All notable changes to DejaLoop are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-07

First working release (MVP, built and tested locally).

Project name chosen: **DejaLoop** (earlier codenames LoopBrake and
StallWatch were dropped — LoopBrake was taken, DejaLoop was clear).

### Added (later same day)
- **Savings counter**: every stopped loop adds an estimated saving
  (~10 avoided repeats × ~$0.05/step, both configurable) to a lifetime
  total shown in the status line (`saved ~$2.00`), `status`, and the demo.
- **`dejaloop set-key`**: stores the optional Jev key in
  `~/.dejaloop/credentials.json` (0600) instead of requiring an env var.
- Plain-English pass: user-facing text says "stuck / going in circles",
  no jargon.

### Added
- Claude Code plugin: `PreToolUse` / `PostToolUse` / `Stop` /
  `UserPromptSubmit` hooks packaged in `hooks/hooks.json` with a plugin
  manifest and single-plugin marketplace file.
- Three-layer detection:
  - **Deterministic layer** (local, free): fingerprints every tool call;
    identical-call streaks and repeated Bash failure streaks trip instantly.
  - **Semantic judge layer** (pluggable via `DEJALOOP_JEV`):
    - `LocalJudge` — built-in zero-cost judge scoring repetition, failure
      patterns, call similarity, and edit/test activity. **Default** when no
      TypeSafe key is present: no account, no key, no network.
    - TypeSafe Jev client (`api.typesafe.ai/v1/systemone`) — used when
      `TYPESAFE_API_KEY` is set or `DEJALOOP_JEV=typesafe`.
    - `MockJev` deterministic test double for tests and the demo.
    - `DEJALOOP_JEV=off` / `none` runs the deterministic layer alone.
  - **Policy layer**: chance it's stuck < 0.50 continue, 0.50–0.75 WARN,
    0.75–0.90 REPLAN (next call denied), > 0.90 HALT & ASK the user.
- Done-claim check: a `Stop` after file edits with no test/build/lint run
  is blocked (enforce mode) or warned (shadow mode).
- Shadow mode (`DEJALOOP_MODE=shadow`, recommended for first installs)
  logs interventions without ever blocking.
- Fail-open design throughout: judge errors, timeouts, broken configs, and
  malformed hook payloads never block or crash a session.
- Terminal status line showing health, session cost, checks, and
  intervention count; local ledger at `~/.dejaloop/ledger.jsonl`.
- CLI: `init` (create `~/.dejaloop` + default config, report the active
  judge), `status`, `demo` (four scripted sessions, no keys needed),
  `report`.
- Test suite (simulated Claude Code hook payloads) and a judge benchmark
  with labelled stuck/healthy scenarios, including hard negatives
  (TDD cycles, exploration, legitimate test re-runs).

### Known limitations
- Not yet exercised inside a live Claude Code session or against live Jev;
  judge thresholds (0.50 / 0.75 / 0.90) are uncalibrated against real Jev
  probabilities.
- "DejaLoop" is a working codename; a final name is still to be chosen.
