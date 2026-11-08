# X Build-in-Public Post — the benchmark

**Platform:** X (Twitter)
**Best posting time:** Pre-launch week or the day after launch, US morning. Works as a standalone — doesn't depend on the launch thread.
**Rules/reminders:** Build-in-public posts do best when they show a real number and an honest caveat in the same breath. Don't oversell the benchmark — its smallness is part of the credibility. Reply to skeptics; they're your best testers.

---

Building in public, day [N] of my agent loop-guard:

I benchmarked three ways of detecting a stuck coding agent on 8 labeled scenarios (4 stuck, 4 healthy — including TDD cycles that look like loops but aren't):

· Dumb rules (repeat fingerprints): caught 1/4 stuck sessions
· The zero-cost local judge I built: caught 4/4 stuck sessions, 0 false alarms

The gap is the semantic cases: six *different* failing commands, zero edits. Rules see variety. The judge sees no progress.

Honest caveat: 8 scenarios, all simulated. Real sessions are messier. That's why it ships in shadow mode first — it logs what it *would* block, so I can measure it on real work before it ever touches anyone's session.

Benchmark code is in the repo if you want to break it: https://github.com/<owner>/[repo-name]
