# Show HN — DejaLoop

**Platform:** Hacker News (news.ycombinator.com/submit)
**Best posting time:** Launch day (Tue–Thu), ~9:00 AM US Eastern — early enough to catch the US workday and still be on the front page by EU evening.
**Rules/reminders:** Show HN requires something people can actually try right now — the repo must be public and installable before posting. No hype, no superlatives, no "revolutionary." The maker (you) must be in the comments answering questions for at least the first few hours — HN penalizes drive-by launches. Don't ask anyone to upvote. Link goes directly to the repo, not a landing page.

---

## Title

Show HN: DejaLoop – a live brake for Claude Code agents stuck in loops

## URL

https://github.com/<owner>/[repo-name]

## Body (text field, optional — keep it short)

I built DejaLoop because my coding agent kept getting stuck in loops and burning tokens, and every tool I found (ccusage, CodeBurn, etc.) only told me the cost *after* the session was over.

DejaLoop is a Claude Code plugin that watches a session live, through hooks, and intervenes while there's still money to save:

- A deterministic layer fingerprints tool calls — the same call 3× in a row, or Bash failing 3× in a row, trips instantly, locally, for free.
- A semantic judge then scores whether the agent is actually making progress. There are two judges: a zero-cost local one that ships built in (no API key needed), and an optional TypeSafe Jev judge (bring your own key — roughly $0.0002 per typical session).
- Intervention escalates: warn → force a replan → halt and ask the user. It also blocks "done" claims when the agent edited files but never ran a test.

Two safety properties I cared about: it's fail-open (if the guard itself errors, your session is never blocked — a guard that can brick a session is worse than none), and it defaults to shadow mode, where it only logs what it *would* have done until you tell it to enforce.

On a small benchmark of 8 labeled scenarios (4 stuck, 4 healthy — including TDD cycles and exploration patterns that shouldn't trip it), the local judge caught 4/4 stuck sessions with 0 false alarms; rules-only detection caught 1/4. Small test set, simulated sessions — the code and the benchmark are in the repo so you can check my work.

It runs fully locally — no account, no server, nothing leaves your machine — and the built-in judge is free, no key needed. One honest limitation: the local judge watches patterns, not meaning, so a subtle case (agent busy doing varied work aimed at the wrong thing) can slip past it. For that there's an optional Jev upgrade, bring-your-own-key, at about a penny for a few hundred sessions. There's also a small savings counter in the status line (saved ~$2.00) that estimates what each stopped loop would have kept burning.

Python, stdlib only, MIT, nothing hosted, no telemetry. Happy to answer questions about the hook mechanics or the judging approach.

## Notes for posting day (not part of the post)

- Post, then immediately drop a first comment with: why you built it, the one-line install, and an open question ("curious how people handle runaway sessions today").
- Stay in the thread. Technical criticism on HN is usually right — concede fast, fix fast, and comment when a fix lands.
- If it gets flagged or dies, do not repost the same day.
