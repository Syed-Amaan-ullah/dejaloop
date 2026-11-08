# r/ChatGPTCoding — DejaLoop (pain-story variant)

**Platform:** Reddit — r/ChatGPTCoding (adaptable to other coding-agent subs)
**Best posting time:** Day +3 or +5, US morning. Don't post the same day as r/ClaudeAI — stagger them, and never paste the same text into two subs.
**Rules/reminders:** This sub is practitioner-first: open with the pain story, keep the product mention earned and late, and expect "how is this different from X" questions. Free-to-try matters — it is (open source, no key needed for the default judge). Swap in your *real* worst-loop story and numbers before posting — the bracketed prompt below must be replaced with something true, not a plausible invention.

---

## Title

My agent burned a session looping on the same bug — so I built a brake that stops it mid-loop

## Body

Genuine question first: what's the worst loop you've caught your coding agent in?

Mine: [REPLACE WITH YOUR REAL STORY — e.g. "I left Claude Code running on a test failure, came back to find it had retried the same failing approach a dozen different ways. Every call looked different. Nothing had progressed. The session cost was real money for literally zero movement."]

That session is what got me. Because afterwards I went looking for a tool that would have stopped it — and everything I found was a cost dashboard. ccusage and friends are fine tools, but they tell you the damage *after* the session ends. Nobody was watching the session **while it ran**.

So I built the thing I wanted: **DejaLoop**, a free, open-source plugin for Claude Code that works like a brake:

- It fingerprints tool calls, so the dumb loops (same file read 6×, same command failing 3×) trip instantly.
- A judge scores actual progress, which catches the smart loops — varied commands, same failing strategy, no edits.
- When it's confident the agent is stuck, it escalates: warn → deny the next call and force a replan (the reason goes back to the agent) → halt and ask you.
- It also won't let the agent say "done" if it edited code and never ran a test. That one's saved me from myself more than once.

Built paranoid, because it's a tool that interrupts your agent:

- **Fail-open** — if the guard errors, your session proceeds. It cannot brick anything.
- **Shadow mode by default** — it only logs what it *would* do until you switch on blocking.
- **Free to run** — the built-in judge is local, no API key. Optional TypeSafe Jev judge if you want a stronger model (BYOK, ~$0.0002/session — a $5 credit covers tens of thousands of sessions).
- MIT, Python stdlib only, no telemetry, nothing hosted.

Early benchmark honesty: I tested it on 8 scripted scenarios (4 stuck, 4 healthy, including TDD cycles that must NOT trip it). The local judge caught 4/4 stuck sessions, 0 false alarms; plain repeat-detection caught 1/4. Small simulated set — real sessions are the true test, which is why it's open source.

GitHub: https://github.com/<owner>/[repo-name]

Curious about two things from this sub: (1) your worst loop story, and (2) would you actually let a tool block your agent, or is warn-only the line for you?
