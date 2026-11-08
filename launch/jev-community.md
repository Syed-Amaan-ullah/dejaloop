# Jev Ecosystem Submissions — DejaLoop

**Platform:** Jev community directories — awesome-jev (GitHub list), madewithjev, jev-directory
**Best posting time:** Pre-launch week. Directory submissions are PRs/forms, not timed posts — get them in *before* launch day so the listings are live when launch traffic looks for social proof.
**Rules/reminders:** The Jev angle goes front and center here — this audience cares about decision models, typed questions, and probabilities, so lead with how DejaLoop uses Jev, not with the loop problem. Be precise about the integration: which question types (Noul for stuck/repeat probabilities, Choice for progress rating), how often it's called, and what it costs. Follow each repo's contribution format exactly (alphabetical placement, their entry template). One PR per list; don't spam maintainers — a polite ping after a week is fine.

---

## 1. awesome-jev — list entry + PR description

### Suggested list entry (adapt to the list's exact format)

```markdown
- **DejaLoop (https://github.com/<owner>/dejaloop)** — A live brake for Claude Code agents: uses Jev to judge whether a coding agent is stuck or going in circles, mid-session, and escalates from warning to forcing a replan to halting. Open source (MIT), BYOK, ~$0.0002/session.
```

### PR title

Add DejaLoop — Jev-powered loop guard for Claude Code

### PR description

Hi! Adding DejaLoop, an open-source Claude Code plugin I built that uses Jev as a live semantic judge for coding-agent sessions.

**How it uses Jev:** every few tool calls (or when deterministic checks suspect trouble), the plugin sends Jev the session's recent trajectory and asks three typed questions:

- `stuck` — Noul: how sure Jev is that the agent is stuck and making no real progress
- `repeating` — Noul: probability it's repeating an already-failed strategy
- `progress` — Choice: progressing / slow / stuck / looping

The probabilities drive an escalation policy: <0.50 continue, 0.50–0.75 warn, 0.75–0.90 force a replan, >0.90 halt and ask the user.

**Why Jev fits:** at $0.042 per million input tokens, a checked session costs ~$0.0002, so users bring their own key and a $5 credit covers tens of thousands of sessions. Jev is an optional upgrade judge in DejaLoop — a zero-cost local judge ships built in so the tool works with no key at all — but Jev is the judge I recommend for subtle semantic loops (varied calls, no progress) that local heuristics and fingerprinting miss.

Fail-open throughout: if Jev times out or errors, the session is never blocked.

Repo: https://github.com/<owner>/[repo-name] (MIT, Python stdlib only)

Thanks for maintaining the list!

---

## 2. madewithjev — submission text

**Project name:** DejaLoop

**Link:** https://github.com/<owner>/[repo-name]

**One-liner:** A live brake for Claude Code — Jev judges whether your coding agent is stuck or going in circles, mid-session, before the tokens burn.

**Description:**

DejaLoop is an open-source Claude Code plugin that stops runaway agent sessions while they're still running. Cost tools like ccusage only report what a session cost after it ends; DejaLoop intervenes live via Claude Code hooks.

Deterministic checks catch the obvious loops for free. For the subtle ones — every tool call different, zero progress — DejaLoop asks Jev. It sends the recent trajectory as state and asks typed questions: a Noul for how likely the agent is stuck, a Noul for "repeating a failed strategy," and a Choice for progress rating. Jev's probabilities map to escalating interventions: warn the agent, force a replan by denying its next call, or halt and ask the human. It also blocks "done" claims when the agent edited files but never ran a test.

Jev's pricing makes this practical as a bring-your-own-key feature: ~$0.0002 per typical session, so a $5 credit lasts tens of thousands of sessions. The tool is fail-open (a Jev timeout never blocks a session), defaults to a log-only shadow mode, and also ships a zero-cost local judge so it works with no key at all — Jev is the recommended judge for the cases heuristics can't read.

MIT licensed, Python standard library only, nothing hosted.

---

## 3. jev-directory — submission text

**Name:** DejaLoop
**URL:** https://github.com/<owner>/[repo-name]
**Category:** Developer tools / AI agents (adapt to the directory's category list)
**Pricing:** Free & open source (MIT); optional Jev judging is BYOK at ~$0.0002/session

**Short description (for the listing card):**

Open-source Claude Code plugin that uses Jev to detect agent sessions going in circles, live and intervene — warn, force a replan, or halt — before tokens burn. Fail-open, shadow-mode by default, zero-cost local judge built in.

**Long description (if the form allows):**

DejaLoop answers a question no existing tool answers in time: *is my coding agent stuck right now?* Existing tools report cost after the session. DejaLoop judges the session while it runs, using Claude Code hooks, and uses Jev's typed questions (Noul stuck probability, Noul repeat-strategy probability, Choice progress rating) as its semantic layer. Jev's probabilities drive a graduated policy — silent, warn, replan, halt-and-ask — and a separate check refuses "done" claims from agents that edited code without ever running a test. Built by an independent developer, MIT licensed, Python stdlib only, bring-your-own-key, nothing hosted, no telemetry.
