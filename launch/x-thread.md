# X Launch Thread — DejaLoop

**Platform:** X (Twitter)
**Best posting time:** Launch day (Tue–Thu), ~9:00 AM US Eastern, same morning as Show HN so the two can feed each other.
**Rules/reminders:** First tweet must stand completely alone — most people never expand the thread. Put the demo GIF in tweet 1 or 2, not at the end. No hashtag spam (1–2 max, or none). Pin the thread to your profile for launch week. Reply to every quote-tweet and question the same day. Link goes in the last tweet and/or first reply — links in tweet 1 can suppress reach.

---

## Thread

**1/**
Your Claude Code agent is looping right now.

Same file, read 6 times. Same failing test, retried 6 ways. Tokens burning the whole time.

Every cost tool tells you afterwards. I built one that stops it mid-session. 🧵

[GIF]

**2/**
Meet DejaLoop — an open-source plugin that acts as a live brake for coding agents.

It watches the session through Claude Code's hooks and intervenes *before* the money is gone — not in a report you read tomorrow.

**3/**
How it works, layer 1: fingerprints.

Every tool call gets hashed. The same call 3× in a row, or Bash failing 3× in a row, trips the brake instantly.

Local. Free. No model call needed.

**4/**
Layer 2 is the interesting part: a semantic judge.

Fingerprinting misses the smart loops — every call different, zero progress. So a judge scores the trajectory: is it stuck? repeating a failed strategy? actually progressing?

**5/**
Two judges, your choice:

→ A zero-cost local judge, built in. No API key, works offline.
→ An optional TypeSafe Jev judge (BYOK). Costs ~$0.0002 per typical session. A $5 Jev credit covers tens of thousands of sessions.

**6/**
When it fires, it escalates:

⚠️ warn the agent
🔁 force a replan (next call denied, reason fed back)
🛑 halt and ask you

And my favorite: it blocks "done" claims when the agent edited files but never ran a single test.

**7/**
I tested it on 8 labeled scenarios — 4 stuck, 4 healthy (including TDD cycles that *look* like loops but aren't).

Local judge: 4/4 stuck sessions caught, 0 false alarms.
Rules only: 1/4.

Small simulated set — the code and benchmark are public, check my work.

**8/**
It also keeps score. Every loop it stops adds to a running total in your status line:

`DejaLoop ● healthy | session $1.24 | checks 18 | saved ~$2.00`

(An estimate — it assumes the loop would have repeated ~10 more times. Real loops usually run far longer.)

**9/**
Safety rules I shipped with:

→ Fail-open: if the guard errors, your session is never blocked
→ Shadow mode by default: it only logs until you trust it
→ Python stdlib only, MIT, nothing hosted, no telemetry

Repo + install (2 commands): https://github.com/<owner>/dejaloop

If your agent has ever burned you in a loop, I'd love to hear it 👇
