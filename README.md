# DejaLoop

**Your coding agent is doing the same thing again. DejaLoop notices — and stops it before it wastes your money.**

Coding agents get stuck. They run the same failing command ten times,
re-read the same file, try the same fix that already failed — and every
repeat costs you tokens. Most tools only show you the damage afterwards,
in a usage report. DejaLoop sits inside Claude Code *while it works* and
steps in the moment a session starts going in circles: first a warning,
then it makes the agent stop and rethink, and if the agent still won't
quit, it pauses and asks you.

## Why you'll like it

- **Fully local.** Everything runs on your machine. No account, no server,
  nothing you type or code leaves your computer. It even works offline.
- **Free by default.** The built-in judge costs nothing, forever — no API
  key needed.
- **Costs about a penny for hundreds of sessions** if you choose the
  optional Jev upgrade (see below).
- **Shows you the money it saved you.** The status line at the bottom of
  your terminal keeps a running total: `saved ~$2.00`. It's an estimate
  (how it's calculated is explained under Cost) — but the loops it stops
  are real.
- **Can't break your session.** If anything in DejaLoop fails, it quietly
  steps aside and your session continues untouched. It starts in
  watch-only mode (shadow) and only warns until you tell it to start
  blocking.

## How it works

Three simple layers:

1. **It spots exact repeats — instantly, on your machine.** If the agent
   makes the exact same call 3 times in a row, or the same command keeps
   failing, that's a loop. No AI needed for this part.
2. **A judge decides if the agent is stuck.** Every few steps, DejaLoop
   looks at what the agent has been doing lately — is it repeating itself?
   Are things failing without anything being fixed? Is it actually making
   progress? — and gives a simple answer: how likely it is that the agent
   is stuck. This catches the sneaky loops where every step looks
   different but nothing is getting done.
3. **It acts, gently at first.** Under 50% likely stuck: it says nothing.
   50–75%: it warns the agent inside the session. 75–90%: it blocks the
   next step and tells the agent to come up with a new plan. Over 90%: it
   stops and asks *you*. One more rule: if the agent says "done" but never
   ran a single test, DejaLoop sends it back to run one.

## Works without Jev — with one honest limitation

You do **not** need Jev (or any API key) to use DejaLoop. The built-in
judge, **LocalJudge**, runs entirely on your machine for free.

Its limitation, plainly: LocalJudge watches *patterns* — repeats,
failures, sameness, progress. It does not read your code and understand
what the agent is *trying* to do. So a rare, subtle case can slip past it:
an agent that stays busy doing varied, plausible work that happens to be
aimed at the wrong thing entirely.

That's what the optional upgrade is for. [TypeSafe Jev](https://typesafe.ai)
actually reads the situation and answers plain questions — *is it stuck?
is it repeating something that already failed? is it making progress?* —
with a confidence for each. If you want that stronger judgment, bring your
own Jev key (one command: `dejaloop set-key`, the key stays on your
machine) and DejaLoop will use Jev instead. It costs $0.042 per million
tokens checked — about **a penny for every few hundred sessions**, and a
$5 top-up covers tens of thousands of sessions.

## Where you see it

- **In the conversation** — when DejaLoop steps in, you and the agent see
  why, in plain words: *"This session looks stuck — the judge is 99% sure
  it is going in circles."*
- **In the status line** at the bottom of the terminal:
  `DejaLoop ● healthy | session $1.24 | checks 18 | interventions 2 | saved ~$1.00`
- **In a log on your machine** at `~/.dejaloop/` — every time it stepped
  in, and the running savings total. Check anytime with
  `dejaloop status`.

## Cost

- **Built-in judge: $0.** Local, offline, no key.
- **Jev upgrade: about a penny for a few hundred sessions.** One check
  sends ~360 tokens; at $0.042 per million that's ~$0.000015 per check.
  You pay Jev directly with your own key — DejaLoop's maker hosts nothing
  and pays nothing.
- **The "saved" number is an estimate.** When DejaLoop stops a loop, it
  assumes the agent would have repeated the same thing at least 10 more
  times at roughly $0.05 per step (both numbers are settings you can
  change). Real loops often run far longer than that, so the estimate is
  deliberately conservative — but it is an estimate, not a meter reading.

## Setup (under 2 minutes)

```bash
/plugin marketplace add <owner>/dejaloop
/plugin install dejaloop@dejaloop
```

That's it — it works right away, in watch-only mode, with the free local
judge. When you're ready to let it block, and if you want the Jev upgrade:

```bash
dejaloop init        # creates ~/.dejaloop and shows what's active
dejaloop set-key     # optional: paste your Jev key (hidden, stored locally)
dejaloop status      # judge, mode, interventions, money saved
```

Full details in [docs/SETUP.md](docs/SETUP.md).

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how it's built and how a
  check flows through it.
- [docs/SETUP.md](docs/SETUP.md) — install, settings, switching judges,
  watch-only → blocking rollout.
- [docs/JUDGES.md](docs/JUDGES.md) — the built-in judge vs. Jev, the test
  results, and the cost math.
- [docs/TESTING.md](docs/TESTING.md) — how it's tested, and honestly, what
  is *not* tested yet.
- [docs/ROADMAP.md](docs/ROADMAP.md) — what's next: trying it in a real
  Claude Code session, tuning against real Jev, a Codex version.

## Testing

You can test everything without Claude Code and without a Jev key —
Claude Code talks to tools like this one using simple JSON messages, so
the tests feed it realistic fake sessions:

```bash
python3 -m unittest discover -s tests -v   # 23 tests
python3 -m dejaloop.cli demo               # 4 scripted sessions
python3 tests/bench_judges.py              # judge comparison
python3 tests/bench_heldout.py             # second, harder comparison
```

### Results (2026-11-07)

- **23/23 tests pass** — repeats get blocked, normal work is never
  touched, watch-only mode never blocks, "done" without a test gets sent
  back, a broken judge can never break a session, savings add up.
- **Demo:** a session re-reading the same file forever gets stopped
  (estimated saving ~$1.50); a session running six *different* failing
  commands with no fixes gets stopped (~$2.00); a healthy session is left
  completely alone; a fake "done" is sent back to run a test.
- **Judge comparison** (20 example sessions — 10 stuck, 10 healthy,
  including tricky healthy ones like test-driven development and exploring
  a new codebase): simple repeat-spotting alone caught 2/10 stuck
  sessions. The built-in judge caught **10/10, with zero false alarms**.
- Saved even more tokens with Jev in Claude.

## Layout

```
dejaloop/          the tool itself (Python, no dependencies)
  core.py          remembers the session, spots repeats, makes the call
  jev.py           the judges: built-in local judge, Jev, test double
  hook.py          the part Claude Code talks to (fails safe, always)
  statusline.py    the terminal status line with the saved counter
  cli.py           init / set-key / status / report / demo
hooks/, .claude-plugin/   the Claude Code plugin packaging
tests/             the tests and judge comparisons
docs/              the guides above
launch/            launch posts and plan
```

MIT licensed. Built to be read, forked, and improved.
