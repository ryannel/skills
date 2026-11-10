---
tags: [prompting-agents]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

can you turn our release notes process into a skill? every friday someone runs `git log --merges v<last>..HEAD`, groups the PRs by label (feat / fix / chore, chore gets left out), and writes notes in CHANGELOG.md under a new `## vX.Y.Z (date)` heading. it has to be user-facing language, not PR titles. breaking changes go first under a **Breaking** line, and anything touching api/public/ needs a line in docs/migration.md too.

gotcha that bites every new person: PRs merged by the merge bot have the label on the linked issue, not on the PR. you get it with `gh pr view N --json closingIssuesReferences`. and the version number comes from `scripts/next-version.sh`, don't guess it.

people on the team use both claude code and codex so it needs to work in both. put it in a folder called release-notes/
