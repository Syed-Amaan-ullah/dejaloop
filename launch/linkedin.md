# LinkedIn — DejaLoop

**Platform:** LinkedIn
**Best posting time:** Week 2 or as a launch-week follow-up, Tue–Thu 8–9 AM in your timezone (LinkedIn peaks before the workday). Don't post the same morning as Show HN — different audience, give it its own moment.
**Rules/reminders:** Professional angle, no hype-speak, no hashtag walls (3 max). A short personal story outperforms a feature list here. If you have a demo GIF or a clean screenshot of the status line, attach it — native media gets far more reach than external links. Put the GitHub link in the first comment if link-in-post reach is a concern; either way, respond to comments within the first two hours.

---

Every developer using AI coding agents has seen this moment:

You come back to your terminal and the agent has been stuck — re-reading the same file, retrying the same failing command in slightly different ways, burning tokens the entire time.

The tools we have today are dashboards. They tell you exactly what that session cost... after it's over.

I wanted the opposite: something that intervenes while there's still something to save.

So I built DejaLoop, an open-source plugin for Claude Code that acts as a live brake for coding agents:

→ Deterministic checks catch obvious loops instantly (repeated calls, repeated failures)
→ A semantic judge scores whether the agent is genuinely progressing — including the subtle loops where every action looks different but nothing is moving
→ Intervention escalates gradually: warn → require a new plan → stop and ask the human
→ It also challenges "done" claims when code was edited but no test was ever run

Two engineering principles guided the build:

1. Fail-open: if the guard itself fails, the developer's session is never blocked. Safety tooling must never become the risk.
2. Shadow mode first: it observes and logs before it's allowed to act. Trust in automation is earned with evidence.

It runs locally, costs nothing in its default configuration, and is MIT-licensed — because tools that sit inside a developer's workflow should be inspectable.

Building it reinforced something I keep relearning: as agents do more of the work, the valuable software increasingly isn't the agent — it's the judgment layer around it. Knowing when to let it run, when to nudge it, and when to stop it is becoming a core engineering discipline.

Repo link in the comments. If your team is adopting coding agents, I'd be interested in how you're supervising them today.

#AI #SoftwareEngineering #OpenSource
