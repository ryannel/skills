---
tags: [prompting-agents]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

our AGENTS.md is a mess and I think it's making things worse. the team uses both claude code (fable 5.2) and codex (astra) on this repo, CLAUDE.md just imports AGENTS.md. two complaints this week: agents keep stopping to ask permission before running the unit tests, and they run the whole e2e suite (25 min) for one-line changes. also last week one of them hand-edited a file in src/gen/ again even though the file says not to.

can you fix it? write the new version to AGENTS.md and tell me what else I should do, if anything.

Input files: AGENTS.md
