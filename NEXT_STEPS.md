# Q: what was built, and what you do next

Written 19 Nov 2026. Matches Chapter 6 of your guidebook (Project 1, Q).

## Where Q stands

| Milestone (guidebook) | Status |
| --- | --- |
| 1 Streaming chat | Built |
| 2 A real CLI (Typer, Rich Markdown, slash commands, SQLite history, kind errors, `q ask -f`) | Built |
| 3 Tool calling and agent loop (`read_file`, `list_dir`, `search_files`, `web_fetch`, `run_shell` with y/N) | Built |
| 4 Folder search, 5 Images, 6 Benchmark, 7 PyPI | Not started |

36 tests pass and `ruff` is clean. The tests use a fake model, and I also ran `q chat` and `q agent` against a fake Ollama server, so the real `ollama` library, streaming and tool calls work together. **It has not been run with a real model yet.** That is your step 1.

No numbers for your resume were measured. Speeds, accuracy, installs and stars all come later, from your own runs.

## Your steps, in order

**1. Setup and first run (20 min).** Do the "Before lesson 1" block at the top of [HOW_Q_WORKS.md](HOW_Q_WORKS.md). Then `uv run q chat`. Why: everything so far was checked with a fake model; only your PC can prove it works for real.

**2. Put it on GitHub (15 min).** Create an empty public repo named `q` on github.com (no README, this folder has one). Then in PowerShell, in this folder:

```powershell
mkdir .github\workflows -Force; Move-Item ci.yml.move-me .github\workflows\ci.yml
git init -b main
git add .
git commit -m "Q v0.0.1: chat, ask, agent, history, safe tools, tests, CI"
git remote add origin https://github.com/FlameBLIZZard/q.git
git push -u origin main
```

Why: from today, every commit is public evidence you build steadily, and CI gives the repo a green tick. (My tools can't write into a `.github` folder on your PC, so the CI file arrived as `ci.yml.move-me`; the first line moves it into place.)

**3. Study the lessons (about 5 hours total, spread out).** [HOW_Q_WORKS.md](HOW_Q_WORKS.md) has 13 lessons. Before exams start on 25 Nov, aim for lessons 1 to 6. After exams (from 3 Dec), lessons 7 to 13. Why: on the resume this is *your* project. An interviewer will ask how the agent decides to stop and what keeps it out of your home folder. The lessons, and especially the "Try it yourself" exercises, are how you earn the answers. Commit after each exercise you keep.

**4. Then milestones 4 to 7** as in the guidebook (index and search, images, the benchmark, PyPI by Sat 19 Dec). I can build each one with a lesson, the same way.

## Timeline note

The guidebook had milestones 1 and 2 for 9 to 15 Nov and milestone 3 split around the exams. Q's code is now ahead of that plan. What is behind is *you running and understanding it*, so steps 1 to 3 are this week's real work. The exam fortnight (25 Nov to 2 Dec) stays free.
