# DejaLoop — Judges

The **judge** is the component that answers the one question DejaLoop
exists to ask: *given what this agent has just done, what is the
probability it is stuck?* It receives a trajectory (the task, the last
8 tool calls, and progress totals) plus a signal dict (repetition streak,
failure streak, steps since last edit, recent-call similarity, edit
count), and returns a chance it's stuck, a repeating-strategy
probability, and a progress rating (`progressing` / `slow` / `stuck` /
`looping`). The [policy layer](ARCHITECTURE.md#policy) turns that
probability into continue / warn / replan / halt.

Judges are pluggable — one environment variable, `DEJALOOP_JEV` —
because "best" depends on what you value: zero friction, or the deepest
semantic read. DejaLoop ships with the zero-friction option as the
default and keeps the deep option one variable away.

---

## The three judges

### LocalJudge — the default

`DEJALOOP_JEV=local` (or unset). Pure Python, in-process.

- **Zero cost, zero friction.** No API, no key, no signup, no network.
  Works offline. Nothing about your session ever leaves your machine.
- **It is not a Jev clone.** Jev is a general trained decision model.
  LocalJudge is a narrow, purpose-built stuck-spotter for coding
  trajectories — DejaLoop needs exactly one judgment, and a scorer
  built for that one judgment covers the structured cases well.
- **How it scores.** A weighted combination of progress features:
  repetition streak, failure streak, no-progress steps, and Jaccard
  similarity between consecutive call inputs — plus a floor rule for
  read/search *thrash* (many highly similar non-edit calls, zero edits:
  score at least 0.55). Similarity matters because it catches loops
  where every call is slightly different, so fingerprints alone miss
  them.
- **Its key insight:** failures *with* edits between them are progress —
  that's a normal TDD cycle of fail → fix → fail → fix, and the failure
  weight is cut to a quarter when edits are happening. Failures *without*
  edits are an agent repeating a strategy that already failed: a loop.
  This one distinction is what keeps healthy TDD sessions at 0 false
  alarms in the benchmarks below.
- **Limits.** It sees *patterns*, not *meaning*. An agent doing
  plausible-looking, varied, edit-heavy work that is nonetheless going
  nowhere — misunderstanding the task, rewriting the wrong module well —
  can stay under its thresholds. That is the case the Jev upgrade exists
  for.

### TypeSafeJev — the optional upgrade

`DEJALOOP_JEV=typesafe` plus your own `TYPESAFE_API_KEY` (bring your
own key; the key lives in your environment, never in the repo).

- **What it is.** [TypeSafe AI's Jev](https://typesafe.ai) ("System
  One"), a trained general decision model. It doesn't generate text: you
  send a state and typed questions, it returns typed answers with
  probabilities. DejaLoop asks three questions per check:
  - *stuck?* — a yes/no probability (Noul),
  - *repeating a failed strategy?* — a yes/no probability (Noul),
  - *progress rating* — a choice among progressing / slow / stuck /
    looping, each with written criteria.
- **How it connects.** `POST https://api.typesafe.ai/v1/systemone`,
  model `jev-latest`, 2-second default timeout. Any error or timeout
  discards the check — the session continues (fail-open, like
  everything else in DejaLoop).
- **When it's the better choice.** Subtle subtle stuck cases: the agent is
  busy, varied, and editing — but the work doesn't advance the task.
  Jev reads the meaning of the trajectory, not just its shape.
- **Status.** The client is implemented against the documented API, but
  real Jev has **not yet been measured** in DejaLoop — no API key was
  available during development, so its row in the benchmark is empty and
  the 0.50 / 0.75 / 0.90 thresholds are uncalibrated against real Jev
  probabilities. Calibration is on the [roadmap](ROADMAP.md). Any claim
  that Jev is more accurate *here* is an expectation, not data — yet.

### MockJev — the test double

`DEJALOOP_JEV=mock`. A small deterministic heuristic used by the unit
tests and the CLI demo so the full pipeline can run with no key and no
network. It is clearly labelled, never selected by default, and is **not
evidence about any real judge's quality**. Never run it in a real
session expecting real judgments.

### No judge — deterministic only

If the judge layer is unavailable, DejaLoop degrades to the
deterministic layer alone: identical-call denies and the done-claim
check still work, deterministic alerts are logged as `observed`, and
semantic loops pass undetected. The benchmarks below show what that
costs.

---

## Head-to-head benchmark

Two suites of labelled scenarios are fed through the real hook handler
as simulated Claude Code payloads (methodology in
[TESTING.md](TESTING.md)). A "flag" is any real intervention — warn or
stronger. Healthy scenarios must **not** be flagged.

### Original suite — `tests/bench_judges.py` (8 scenarios)

4 stuck, 4 healthy, including hard healthy negatives: a TDD
fail→edit→fail→pass cycle, varied exploration across 6 files, and the
same test legitimately re-run after each edit.

| Judge | Stuck caught | False alarms |
|---|---|---|
| Deterministic only | 1/4 | 0/4 |
| **LocalJudge (default)** | **4/4** | **0/4** |
| MockJev (reference) | 3/4 | 0/4 |
| Real Jev | not yet measured — needs a key | — |

### Held-out suite — `tests/bench_heldout.py` (12 scenarios)

Written *after* LocalJudge was tuned, with different tools, commands,
and patterns, and never used for tuning — a miss here is the honest
generalisation result.

| Judge | Stuck caught | False alarms |
|---|---|---|
| Deterministic only | 1/6 | 0/6 |
| **LocalJudge (default)** | **6/6** | **0/6** |
| MockJev (reference) | 6/6 | 0/6 |

Combined: **LocalJudge 10/10 stuck, 0/10 false alarms**; deterministic
only 2/10 stuck.

### Caveats — read these before quoting the table

- **20 scenarios is a small set**, and all of them are simulated. They
  show the pipeline discriminates structured loops from structured
  healthy work; they do not prove real-world accuracy.
- LocalJudge was iterated against the original 8. The held-out 12 exist
  precisely to check that it generalises — so far it does, but the
  held-out set must never be tuned against, or it stops being evidence.
- Real-world validation comes from **shadow-mode logs on real
  sessions**: what DejaLoop flags, and what it misses, on work nobody
  scripted. That data collection is the next phase (see
  [ROADMAP.md](ROADMAP.md)).

### Run it yourself

```bash
python3 tests/bench_judges.py     # original 8 scenarios, all judge configs
python3 tests/bench_heldout.py    # held-out 12 scenarios
python3 -m dejaloop.cli demo    # 4 scripted sessions end-to-end
```

Once a TypeSafe key exists, the same harness runs the live head-to-head:
set `TYPESAFE_API_KEY` and select `DEJALOOP_JEV=typesafe` — that
calibration run is what fills in Jev's row.

---

## Jev cost math

Jev pricing: **$0.042 per million input tokens, output free.** No
subscription, no per-seat fee, no free tier — you add credit and pay for
what you send.

A DejaLoop check is deliberately lean: the task plus the last 8 calls
with inputs truncated, plus the three questions — **~360 input tokens
per check**, measured from a realistic mid-session state. That's about
**$0.000015 per check** (a check runs every 5 tool calls, or immediately
when the deterministic layer suspects trouble).

$5 of credit buys ~119 million input tokens ≈ ~330,000 checks:

| Session size | Checks | Sessions per $5 |
|---|---|---|
| Light (25 tool calls) | 5 | ~66,000 |
| Typical (50 tool calls) | 10 | ~33,000 |
| Long (100 tool calls) | 20 | ~16,600 |
| Marathon (200 tool calls) | 40 | ~8,300 |

So per-session Jev cost is roughly **$0.0001–$0.0006** — a fiftieth of a
cent at the heavy end. Caveats: token counts use the ~4-chars-per-token
rule of thumb, and if the trajectory payload grows richer in future
(more context per check), divide the session counts proportionally —
it stays in the thousands per $5 regardless.

And because DejaLoop is BYOK, the user who runs it pays their own
fraction-of-a-cent bill; the project hosts nothing and pays nothing.

---

## Why local by default, Jev as upgrade

- **Adoption friction is the whole ballgame for an open-source tool.**
  "Install it and it works" beats "install it, then go sign up
  somewhere, add credit, create a key, export a variable." LocalJudge
  removes every step after install.
- **Privacy and offline use come free.** With LocalJudge, trajectory
  data never leaves the machine and the guard works on a plane.
- **The benchmark says the local judge is already strong** at the
  structured failures that burn most tokens: repeated calls, failing
  strategies, read/search thrash — with zero false alarms on healthy
  TDD, exploration, and test re-runs.
- **Jev remains the upgrade path** for the failures patterns can't see:
  semantically empty progress. It's pluggable today and cheap when
  used — the door is open the moment its accuracy here is actually
  measured.

This isn't a bet on one judge. The interface is the product surface;
judges compete behind it, and the benchmark decides.
