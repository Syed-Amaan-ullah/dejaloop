# Indie Hackers — DejaLoop

**Platform:** Indie Hackers
**Best posting time:** Week 2 after launch, US morning. IH moves slowly — a good post keeps getting comments for days, so don't post it on a day you can't check back.
**Rules/reminders:** This audience wants the journey and the numbers, honestly told — including the zeros. Don't dress it up as a revenue story when it isn't one (yet): the honest angle here is "$0 product, $0 running cost, built for adoption and learning." Milestone-style posts do well. Link in the post is fine; leading with the link is not.

---

## Title

I built a "brake pedal" for AI coding agents — $0 to build, $0 to run, open source

## Body

**The problem I kept paying for**

I use Claude Code heavily, and I kept losing money to the dumbest failure mode in AI coding: the loop. The agent re-reads the same file six times. Retries the same failing test with six cosmetic variations. Every call plausible, none of them progress, all of them billed.

The tooling that exists — usage dashboards, cost trackers — tells you what happened *afterwards*. I was paying for autopsies. I wanted a brake.

**What I built**

DejaLoop: an open-source Claude Code plugin that watches a session live through the hooks system and intervenes mid-session:

- Local fingerprinting catches the obvious loops (same call 3× in a row, same command failing 3× in a row)
- A semantic judge scores whether the agent is actually progressing — this catches the "every call is different, nothing is moving" loops
- Escalation: warn → force a replan → halt and ask the human
- Bonus check: the agent can't declare "done" if it edited files and never ran a test

**The numbers (small, but real)**

- Build cost: ~$0. It's Python standard library only, no dependencies, nothing hosted.
- Running cost for users: $0 with the built-in local judge. Optional Jev-powered judge for those who want it: ~$0.0002 per session, bring-your-own-key. A $5 Jev credit covers tens of thousands of sessions, so even the "paid" path is effectively free.
- Benchmark: on 8 labeled test scenarios, the local judge caught 4/4 stuck sessions with 0 false alarms — rules alone caught 1/4. It's a small, simulated set; I'm not pretending it's more than it is.
- Revenue: $0. Stars/users: just launched — will update this post honestly as numbers come in.

**Why free and open source?**

Deliberately. The wedge isn't charging — it's adoption. Every competing tool in this space is either a dashboard (after the fact) or tied to one agent. A free, live, cross-cutting brake that never phones home is the version of this that spreads. And the BYOK design means my cost of serving 10 users and 10,000 users is identical: zero. That's a business model I can sustain as a solo builder.

**The two design decisions I'd defend anywhere**

1. **Fail-open.** If my guard crashes, your session proceeds untouched. A safety tool that can brick your work is worse than no tool.
2. **Shadow mode by default.** It logs what it *would* have blocked before it's ever allowed to block anything. Trust is earned with receipts.

**What I'm watching next**

- Do the shadow-mode logs from real sessions match my simulated benchmark, or do real agents loop in ways I haven't imagined?
- Does anyone actually flip it from shadow to enforce? That conversion is the real product metric.
- Judge calibration against live Jev on real trajectories.

Repo: https://github.com/<owner>/[repo-name]

Fellow builders: if you've shipped dev tools, what made people trust your tool enough to let it *interfere* with their workflow? That trust problem feels like the whole game here.
