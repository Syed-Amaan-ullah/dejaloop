# Product Hunt — DejaLoop

**Platform:** Product Hunt
**Best posting time:** Week 2 after launch. Product Hunt days start at 12:01 AM Pacific — schedule the launch for 12:01 AM PT on a Tue–Thu and be awake for the first hours.
**Rules/reminders:** You need a hunter account in good standing; the maker must be present in the comments all day. No asking for upvotes directly (PH penalizes it) — you can ask people to "check it out and share feedback." Prepare the gallery images and a short demo GIF/video in advance; listings without media underperform badly. First comment from the maker is standard practice and expected.

---

## Name

DejaLoop

## Tagline options (pick one — 60 chars max)

1. A live brake for AI coding agents stuck in loops
2. Stop your coding agent from burning tokens in loops
3. Claude Code plugin that halts runaway agent sessions

## Description

AI coding agents get stuck. They re-read the same file, retry the same failing command six different ways, and burn tokens the whole time — and every existing cost tool only shows you the damage *after* the session ends.

DejaLoop is an open-source Claude Code plugin that intervenes **live**, while the session is still running:

🔍 **Deterministic checks** fingerprint every tool call — identical repeats and repeated failures trip instantly, locally, free.

💸 **A savings counter** lives in your status line — every loop it stops adds an estimated saving (saved ~$2.00), based on the repeats it prevented.

🧠 **A semantic judge** scores whether the agent is actually progressing — catching the smart loops where every call is different but nothing is moving. A zero-cost local judge is built in (no API key needed); an optional TypeSafe Jev judge is available bring-your-own-key at ~$0.0002 per session (about a penny for a few hundred sessions).

🛑 **Graduated intervention** — warn → force a replan → halt and ask you. Plus a check that blocks "done" claims when the agent edited code but never ran a test.

Safety-first by design: **fail-open** (if the guard errors, your session is never blocked) and **shadow mode by default** (it only logs what it *would* do until you trust it).

On a small benchmark of 8 labeled scenarios, the built-in judge caught 4/4 stuck sessions with 0 false alarms on healthy ones (rules-only detection caught 1/4).

Free, MIT-licensed, Python stdlib only, nothing hosted, no telemetry.

## First comment (maker)

Hey Product Hunt 👋 I'm the maker of DejaLoop.

I built this after watching one too many Claude Code sessions quietly loop — same file read over and over, same test failing six different ways — while the token meter ran. The dashboards I used told me the cost the next day. I wanted a brake pedal instead of a report.

Two things I obsessed over: it can never block a healthy session by accident (fail-open, shadow mode first), and it costs nothing to run — the built-in judge is local, and the optional Jev judge runs about $0.0002 a session on your own key.

It's open source and I'd genuinely love your feedback — especially the hard kind. What loop patterns has your agent fallen into? What would a tool have to prove before you'd let it interrupt your agent?

I'll be here all day answering questions.
