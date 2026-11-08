# r/SideProject — DejaLoop

**Platform:** Reddit — r/SideProject
**Best posting time:** Day +4 after launch, US morning. Space it out from the r/ClaudeAI post — different angle, different day.
**Rules/reminders:** This sub rewards the builder story: what you made, why, what you learned. Screenshots/GIFs help a lot here. It's fine to link your project, but the post should stand on its own as a story. Engage with comments, especially from other builders.

---

## Title

I got tired of my AI coding agent wasting money in loops, so I built it a brake pedal

## Body

Side project story time.

I use Claude Code a lot, and I kept hitting the same stupid problem: the agent would get stuck — re-reading the same file, retrying the same failing command with tiny variations — and just keep burning tokens until I noticed. I'd check my usage afterwards and think, *cool, I paid for that loop.*

Every tool in this space is a dashboard. They show you the wreck after the crash. Nobody had built the brake.

So that's what I made: **DejaLoop**, a small open-source plugin that sits inside Claude Code (via its hooks system) and watches the session *while it runs*:

1. Cheap local checks catch the obvious loops — identical repeated calls, repeated failures.
2. A "judge" scores whether the agent is genuinely progressing. I built a zero-cost local judge so it works with no API key; there's also an optional mode using TypeSafe's Jev decision model for people who want a stronger judge (costs them ~$0.0002 a session, bring-your-own-key).
3. If it's going in circles, it escalates: warn the agent → force it to replan → halt and ask the human. It also refuses to let the agent say "done" if it edited code but never ran a test. That one was personal.

Design rules I set for myself:

- **It can never break a session.** If my code throws an error, everything is allowed through. Fail-open or don't ship.
- **Shadow mode first.** It logs what it *would* do before it's ever allowed to actually block anything.
- **Zero dependencies.** Python standard library only. Nothing hosted, no accounts, no telemetry.

Testing it was the fun part. I wrote 8 labeled scenarios — 4 genuinely stuck sessions, 4 healthy ones (including a proper TDD red-green cycle, which *looks* like failing repeatedly but is actually progress). The local judge caught 4/4 stuck sessions with zero false alarms; simple rules only caught 1/4. Small test set, fully simulated — I know the real test is other people's sessions, which is why it's open source (MIT).

Total spend so far: basically $0. The whole thing runs locally.

GitHub: https://github.com/<owner>/[repo-name]

If you use AI coding agents, I'd love to hear your worst loop story — and whether you'd trust a tool to interrupt your agent, or if that crosses a line for you.
