# LAUNCH PLAN — DejaLoop

**Platform:** Master plan (all channels)
**Best posting time:** Launch day is a Tue–Thu, first post ~9:00 AM US Eastern (Show HN + X thread together).
**Rules/reminders:** Nothing in this plan works if the repo isn't public, installable, and named. Every post links to the same repo — make sure the README's install commands work from a clean machine before day one. You (the author) are the face of this launch: your presence in comment threads is not delegable. All draft copy lives in this folder — swap DejaLoop and <owner> throughout before posting anything.

---

## Phase 0 — Must be true before anything posts (hard gate)

- [ ] **Final name chosen** and checked: GitHub repo name available, no obvious conflicting project, npm/PyPI name sanity-checked if relevant
- [ ] Repo renamed from the DejaLoop codename; DejaLoop and <owner> replaced in every draft in this folder
- [ ] **Repo public** on GitHub under your account, MIT license file in place
- [ ] README finalized: what it is, 2-command install, how it works, benchmark table *with* the small-test-set caveat, fail-open + shadow mode explained
- [ ] Install verified from a clean environment (fresh clone → plugin installs → status line renders)
- [ ] **Demo GIF recorded** (~20–30 seconds): a session looping → DejaLoop warns → forces replan → halts; plus a healthy session left alone. This GIF is the single highest-leverage asset — it goes in the README, tweet 1/2, Reddit posts, and Product Hunt gallery
- [ ] Tests + benchmark run clean from the public repo (`python3 -m unittest discover -s tests`, `python3 -m dejaloop.cli demo`)
- [ ] Your accounts ready: Hacker News account exists (not brand-new if avoidable), Reddit account meets r/ClaudeAI's karma/age bar for showcases, X profile has a real bio/photo, Product Hunt account in good standing
- [ ] Launch-day calendar blocked: you are online and replying for at least 4–5 hours after the Show HN post

## Phase 1 — Pre-launch (the week before)

- [ ] **Directory submissions in:** awesome-jev PR opened, madewithjev submission sent, jev-directory submission sent (copy: `jev-community.md`) — these take days to merge, so they must precede launch day
- [ ] Build-in-public post on X (`x-buildinpublic.md`) — the benchmark result, posted as a standalone; warms up your profile and tests the story on a small audience
- [ ] Optional: one or two genuine participation comments in r/ClaudeAI and on HN in the preceding days (be a community member, not a promoter — do NOT mention the project)
- [ ] Soft-test the README on 2–3 developer friends: can they install it in under 2 minutes without asking you anything? Fix what they trip on
- [ ] Prepare the demo GIF file in the exact formats each platform wants (README embed, X upload, Product Hunt gallery)

## Phase 2 — Launch day (Tue–Thu)

**~9:00 AM ET**
- [ ] **Show HN** (`show-hn.md`) — post, then immediately add the first comment
- [ ] **X launch thread** (`x-thread.md`) — post within the same hour so each can reference the other's traction

**All day**
- [ ] You are in the HN thread answering questions — this is the job for launch day; everything else is secondary
- [ ] Reply to every X reply/quote; pin the thread to your profile
- [ ] Fix anything broken that commenters find, and comment publicly when a fix ships (HN especially rewards this)
- [ ] Log every substantive criticism/feature request somewhere durable — this is your v1.1 roadmap and your week-2 content

## Phase 3 — Days +2 to +5

- [ ] **Day +2: r/ClaudeAI** (`reddit-claudeai.md`) — problem/demo-led angle; US morning
- [ ] **Day +3 or +4: r/ChatGPTCoding** (`reddit-coding.md`) — pain-story angle; replace the bracketed story prompt with your real worst-loop story first
- [ ] **Day +4: r/SideProject** (`reddit-sideproject.md`) — builder-story angle
- [ ] Keep answering comments on all prior posts daily; Reddit threads have a long tail
- [ ] If launch feedback produced a fix or a new benchmark, that's a natural follow-up post/comment — real updates, never manufactured ones

## Phase 4 — Week 2

- [ ] **dev.to deep-dive** (`devto-article.md`) — publish Tue–Thu morning; update it first with anything real you learned from launch-week feedback
- [ ] **Product Hunt** (`product-hunt.md`) — launch at 12:01 AM PT on a Tue–Thu; gallery + GIF ready; maker in comments all day; ask for feedback, never for upvotes
- [ ] **Indie Hackers** (`indie-hackers.md`) — numbers/journey post; update the "users/stars" line with the real figures by then, even if they're small
- [ ] **LinkedIn** (`linkedin.md`) — professional-angle post, 8–9 AM local, GitHub link in first comment
- [ ] Follow-ups on the Jev directories: confirm listings are live; if a listing merged during launch week, thank the maintainer in the PR thread

## What only you (the author) can do — non-delegable

- Choose the final name and own the GitHub account the repo lives under
- Record the demo GIF from a real session on your machine
- Post from your own accounts (HN, Reddit, X, PH, IH, LinkedIn)
- **Be present in every launch thread** — answer technical questions, concede good criticism fast, ship fixes publicly. People star the maker as much as the repo; the recognition you're after attaches to a person who shows up
- Give the final read to every post before it goes live — they're written in your voice, and only you can confirm they sound like you and that every claim in them is one you're willing to defend in comments

## Post-launch (week 3+)

- [ ] Write the "what I learned" follow-up (X + IH) with honest numbers — downloads, stars, shadow-mode logs, what broke
- [ ] Publish the first real-session findings (with any sharers' consent) — this is the benchmark that actually matters
- [ ] Turn launch-thread feature requests into a public v1.1 roadmap in the repo
