The skill is written: `release-notes/SKILL.md`, one file. It has not been run against your repository yet, so treat it as a first draft until it has done one real Friday.

**What it tells the agent**

- The two things that bite new people come first: a PR merged by the merge bot has its label on the linked issue (`gh pr view N --json closingIssuesReferences`, then the issue's labels), and the version comes from `scripts/next-version.sh`, never from a guess.
- The PRs come from `git log --merges v<last>..HEAD`. `feat` and `fix` go in, `chore` is left out.
- The entry goes in `CHANGELOG.md` under `## vX.Y.Z (date)`, with breaking changes first under a `**Breaking**` line.
- Notes are written for users, not copied from PR titles.
- Any PR that touches `api/public/` also gets a line in `docs/migration.md`.
- It finishes by accounting for every PR in the range and reporting any it could not place.

**Using it in both Claude Code and Codex**

The frontmatter is only `name` and `description`, which is the set both hosts accept. Codex looks for project skills in `.agents/skills/`, and Claude Code looks in `.claude/skills/`. Put the folder at `.agents/skills/release-notes/` and symlink `.claude/skills/release-notes` to it, so there is one copy to maintain. People call it with `/release-notes` in Claude Code and `$release-notes` in Codex, or just ask for the release notes.

Codex often runs with network access turned off, and `gh` needs the network. The skill tells the agent to stop and say so if `gh` fails, instead of writing notes from the merge commit titles.

**Things I assumed, which you should check**

1. `scripts/next-version.sh` takes no arguments, prints the version, and changes nothing. If it needs an argument or it tags or commits, tell me and I'll change that line.
2. You didn't say how a breaking change is marked. The skill has the agent judge it: a change is breaking when a user has to change something to keep working after upgrading. If you have a label for it, that is more reliable and I'll use it.
3. I had no sample entry, so the skill tells the agent to copy the date format, the headings over the feat and fix groups, and the bullet style from the entries already in `CHANGELOG.md`. Paste one in if you'd like the format fixed in the skill.
4. A breaking change is listed once, under `**Breaking**`, and not again under feat or fix.
5. The `api/public/` rule goes by the files a PR changed, so it also covers `chore` PRs. If one of those changes nothing a caller would notice, the agent reports it and leaves the decision to you.
6. The skill stops at the two edited files. It commits, tags or publishes only when asked.

**Testing it**

The quickest test is last Friday's release. Check out the commit before those notes were written, ask for the release notes in a fresh session, and compare the result with what your teammate wrote. Do it once in Claude Code and once in Codex. Pick a week that had a bot-merged PR and an `api/public/` change, since those are the two cases the skill exists for. If the agent ends up writing the same label-lookup helper on every run, that helper should become a script in the skill folder.
