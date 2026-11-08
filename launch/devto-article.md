# dev.to Deep-Dive — DejaLoop

**Platform:** dev.to
**Best posting time:** Week 2 after launch (after Show HN / Reddit feedback is in, so the article can address real questions). Tue–Thu morning US time.
**Rules/reminders:** dev.to rewards genuine technical depth and honesty over launches — write it as an engineering article, with the repo link woven in, not as an ad. Use the tags: #ai #opensource #programming #tooling (max 4). Include the benchmark caveats; this audience will find them anyway and respect you more for stating them first. A cover image helps (use the demo GIF's best frame).

---

title: "My coding agent burned tokens in a loop. So I built it a brake."
published: false
tags: ai, opensource, programming, tooling
---

# My coding agent burned tokens in a loop. So I built it a brake.

Here's a failure mode every heavy user of coding agents has seen: the agent gets stuck. It re-reads the same file. It retries the same failing test with cosmetically different commands. It makes call after call, each one plausible, none of them progress — and every call costs tokens.

When I went looking for tooling, I found plenty of cost dashboards: ccusage, CodeBurn, and friends. They're good tools. But they all share one property — they tell you what a session cost **after it ended**. That's an autopsy, not a safety system.

I wanted something that intervenes **live**, inside the session, while there's still something to save. So I built DejaLoop, an open-source Claude Code plugin. This post is about the interesting engineering problem underneath it: *how do you tell a stuck agent from a busy one, in real time, cheaply enough to run on every session?*

## Why fingerprints aren't enough

The naive approach is fingerprinting: hash each tool call (tool name + inputs), and flag repeats. It works — for the dumbest loops. An agent reading the same file six times in a row is trivially detectable.

But the expensive loops are smarter than that. Consider this trajectory:

```
pytest -q            → FAILED
pytest tests/        → FAILED
python -m pytest     → FAILED
pytest -q -x         → FAILED
pytest tests/ -q     → FAILED
```

Six calls, six *different* fingerprints, zero edits in between. A fingerprint detector sees variety and concludes the agent is exploring. A human sees an agent that has retried the same failing strategy six ways and changed nothing. The difference between those two readings is **semantics**: you have to judge whether the trajectory constitutes progress, not whether the calls are identical.

The opposite failure matters just as much. A TDD session — edit, test fails, edit, test fails, edit, test passes — *looks* like a failing loop to naive detection. Flag that, and your guard becomes the most annoying tool on someone's machine. Any detector in this space lives or dies on its false-alarm rate.

## The design: three layers

DejaLoop runs inside Claude Code via its hooks system (`PreToolUse`, `PostToolUse`, `Stop`). Every tool call flows through three layers:

### Layer 1 — Deterministic checks (free, instant)

Fingerprint every call. Same call 3× consecutively, or Bash failing 3× in a row, is a strong local signal that costs nothing to compute. This layer also maintains the trajectory features the judge needs: repetition streaks, failure streaks, call-similarity, steps since the last edit, whether any verification (test/build/lint) has run.

### Layer 2 — A semantic judge

Every few tool calls — or immediately when layer 1 smells trouble — the recent trajectory is scored by a judge answering typed questions: *Is the agent stuck? Is it repeating a failed strategy? How would you rate its progress?*

The judge is pluggable, and there are two real options:

- **A zero-cost local judge** that ships built in. No API key, no network, works offline. It's a purpose-built scorer for this one narrow judgment — not a general model.
- **TypeSafe Jev** (bring your own key). Jev is a dedicated decision model that returns probabilities for typed questions, which is exactly the shape this problem wants. It costs about $0.0002 per typical session at current pricing — a $5 credit covers tens of thousands of sessions.

A general lesson here: I did **not** need a general-purpose decision model. I needed one judgment, made cheaply and often. Narrow judges are dramatically easier to build, test, and afford.

### Layer 3 — Policy: escalate, don't amputate

A "chance it's stuck" score isn't an action. The policy layer maps it to escalating interventions:

| Signal | Action |
|---|---|
| < 0.50 | Continue silently |
| 0.50–0.75 | **Warn** — inject a message into the session |
| 0.75–0.90 | **Replan** — deny the next tool call, feed the reason back to the agent |
| > 0.90 | **Halt & ask** — stop and let the human decide |

There's also a separate check on the `Stop` event: if the agent edited files but never ran a test, build, or lint, its "done" claim gets blocked and it's sent back to verify. Anyone who has reviewed agent output knows why that one exists.

## Two safety properties that are not optional

**Fail-open.** If the judge times out, if the plugin throws, if anything at all goes wrong in the guard — the session proceeds, untouched. A safety tool that can brick your session is a liability, not a safety tool. Every exception path in the hook handler resolves to "allow."

**Shadow mode by default.** New installs only *log* what the guard would have done. Blocking is opt-in, after you've read the logs and trust it. This is how security tooling earns adoption, and it's also how I get real-world false-alarm data without hurting anyone's work.

## The benchmark (and its limits)

I built 8 labeled scenarios — 4 stuck, 4 healthy — with the healthy set deliberately including the hard negatives: a TDD red-green cycle, varied exploration across files, and legitimate repeated test runs. A scenario counts as "caught" if the guard intervenes; a healthy scenario counts as a false alarm if it intervenes at all.

| Judge | Stuck caught | False alarms |
|---|---|---|
| Deterministic rules only | 1/4 | 0/4 |
| Local judge (zero-cost) | 4/4 | 0/4 |

Rules alone miss exactly the cases I built this for — the varied-command failing loop, the alternating two-strategy loop, the near-identical search thrash. The local judge caught all of them and left every healthy pattern alone.

Now the honesty paragraph, because this audience deserves it: **8 scenarios is a small set, and they're simulated.** Claude Code hooks are just JSON on stdin, which makes the whole pipeline testable offline with scripted payloads — that's how these numbers were produced — but real sessions are longer, messier, and weirder than anything I scripted. The benchmark code is in the repo; the real validation will be shadow-mode logs from actual use, and I'd rather tell you that up front than dress up a small number as a big one.

## What I'd do differently / what's next

- **Calibrate against real Jev.** The Jev client is implemented against the documented API, but its thresholds (0.50 / 0.75 / 0.90) are uncalibrated against real Jev probabilities. That's the first job once it's running with a live key on real sessions.
- **More agents.** v1 is Claude Code only, because that's where the hooks are documented and where I work. A Codex adapter is the obvious next step.
- **Learn from the ledger.** Every intervention is logged locally (`~/.dejaloop/ledger.jsonl` in the current build). Aggregate patterns — with consent, never by default — are how the judge gets smarter than my 8 scenarios.

## Try it

DejaLoop is MIT-licensed, Python standard library only, nothing hosted, no telemetry, bring-your-own-key only if you opt into Jev.

Repo: https://github.com/<owner>/[repo-name]

If you've watched an agent loop your money away, I want to hear the story — and if you run it in shadow mode, I want to hear what it *would* have caught. That's the data that makes v2 real.
