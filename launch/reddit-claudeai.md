# r/ClaudeAI — DejaLoop

**Platform:** Reddit — r/ClaudeAI
**Best posting time:** Day +2 after launch (Tue–Thu), US morning (~9–11 AM ET) when the sub is most active.
**Rules/reminders:** The sub expects tools to be free to try — DejaLoop is (open source, local judge needs no key), say so early. Keep self-promo tone minimal: lead with the problem and a demo, not a sales pitch. Check your account meets the sub's karma/age requirements for showcase posts before launch day. Flair the post correctly (check the sub's current flair options). Stay and answer every comment — Reddit reads silence as a dump-and-run promo.

---

## Title

My Claude Code agent looped on the same failing approach and burned tokens — so I built a plugin that stops it mid-session

## Body

We've all watched it happen: Claude Code gets stuck. Same file read six times. Six *different* test commands, all failing, zero edits in between. You come back to the terminal and the session (and the bill) has run away with itself.

The frustrating part: every tool I tried only showed me the damage **afterwards**. Cost dashboards are autopsies. I wanted a brake pedal.

So I built **DejaLoop** — an open-source Claude Code plugin that intervenes *live*, using hooks:

- **Deterministic checks** fingerprint every tool call. Same call 3× in a row, or Bash failing 3× in a row → flagged instantly.
- **A semantic judge** scores whether the agent is making real progress — this is what catches the "every call is different but nothing is progressing" loops that fingerprinting misses.
- **Escalation:** warn → force a replan (the next tool call is denied, with the reason fed back to the agent) → halt and ask you.
- **Done-claim check:** if the agent edited files but never ran a test, build, or lint, it gets sent back when it tries to stop and declare victory.

Things I was careful about:

- **Free to run.** The built-in local judge needs no API key and costs nothing. There's an optional TypeSafe Jev judge if you want a stronger semantic model — bring your own key, it's about $0.0002 per typical session.
- **Fail-open.** If the guard crashes, your session proceeds untouched. It can never brick a session.
- **Shadow mode by default.** It only *logs* what it would have done until you switch it to enforce. I didn't want anyone's first experience to be a false block.
- It only uses Python's standard library, it's MIT licensed, and nothing is hosted or phoned home.

Honest benchmark note: on my small test suite (8 labeled scenarios — 4 stuck, 4 healthy, including TDD patterns that must NOT trip it), the local judge caught 4/4 stuck sessions with 0 false alarms. Rules alone caught 1/4. It's a small, simulated set — real-world numbers will come from people actually using it, which is partly why I'm posting.

[DEMO GIF / LINK HERE]

Install is two commands inside Claude Code (in the README). GitHub: https://github.com/<owner>/[repo-name]

I'd genuinely like feedback: what loop patterns have you seen that this should catch? What would make you trust a tool enough to let it block your agent?
