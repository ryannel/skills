The skill is written: one file, `release-notes/SKILL.md`. I have not run it, because I had no access to your repository, so treat the first Friday as its test.

It follows your process in order:

1. Find the last version tag, run `scripts/next-version.sh` for the new one, and take today's date.
2. List merges with `git log --merges v<last>..HEAD`.
3. Read each pull request's label, falling back to the linked issue when the pull request has none.
4. Write the `## vX.Y.Z (date)` entry in user-facing language, with `**Breaking**` first and chores left out.
5. Add a line to `docs/migration.md` for every pull request that touches `api/public/`.
6. Report what it did and leave both files uncommitted.

## Installing it for both tools

Claude Code and Codex read the same `SKILL.md` format but look in different folders. Keep one copy and link it from the other, from the repository root:

```bash
mkdir -p .agents/skills .claude/skills
mv release-notes .agents/skills/
ln -s ../../.agents/skills/release-notes .claude/skills/release-notes
```

Codex reads `.agents/skills/` and Claude Code reads `.claude/skills/`. The frontmatter uses only `name` and `description`, and the body uses only shell commands, so nothing in it is specific to one tool. Run it with `/release-notes` in Claude Code or `$release-notes` in Codex, or just ask for the release notes.

## Where I filled a gap

You didn't cover these, so I chose something. Each is a line or two to change.

- **What counts as breaking.** I used: a breaking label, `!` or `BREAKING CHANGE` in the title or body, or a removal or rename under `api/public/`. When unsure, the agent asks. If you have a specific label for this, tell me and I'll name it.
- **Chores that touch `api/public/`.** I read "anything touching" literally. They get a migration line but stay out of the changelog.
- **No label on the pull request or its issue.** The agent places the change by what it does and flags it in the report.
- **`scripts/next-version.sh`.** I assumed it runs with no arguments and prints the version. If it does anything else, such as creating the tag, tell me.
- **Layout details.** For the group headings for features and fixes, the date format, and whether lines carry pull request numbers, the agent copies the previous entries in `CHANGELOG.md` and `docs/migration.md`.
- **Committing.** It never commits, tags or pushes. Say if you want it to open a pull request with the notes.

One thing your description didn't mention that I added: the agent checks that the latest tag matches the top heading in `CHANGELOG.md`, and stops if they disagree.
