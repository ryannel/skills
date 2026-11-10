# The commit guard

I built it, but the part that does the work is a hook, not the skill's text. A skill is the same kind of thing as CLAUDE.md: words Claude weighs against everything else it has read, and sometimes drops. That is why the capitals didn't help. A rule that has to hold every time needs something Claude Code runs whatever Claude decides, so the skill folder carries a hook script and the skill text is only there to help Claude pass it first time.

Nothing is installed yet. The folder is `commit-guard/`, next to this file.

## What it does

Before every Bash command Claude runs, Claude Code runs `scripts/guard.mjs`. If the command contains a `git commit` that would land on `main`, or that includes a file Prettier hasn't formatted, the command is cancelled and Claude is told why and what to run instead. For example:

```
Commit guard: the command was cancelled before any part of it ran.

These files in the commit are not formatted with Prettier:
  src/bad.js
Format them, stage the formatted versions, then commit:
  npx prettier --write src/bad.js
  git add src/bad.js
```

It uses the project's own Prettier and `.prettierignore`, checks only the files in the commit, and never changes files, the branch or the staging area itself. It handles the way Claude usually commits (`git add … && git commit …` in one command, `git commit -am`, a new branch created in the same command). A check of a one-file commit took about a third of a second here.

## Getting it to the team

1. Copy `commit-guard/` to `.claude/skills/commit-guard/` in your repository.
2. From the repository, run `node .claude/skills/commit-guard/scripts/setup.mjs`. It adds one hook entry to `.claude/settings.json` and leaves the rest of that file alone. Add `--dry-run` to see the change first.
3. Commit `.claude/skills/commit-guard/` and `.claude/settings.json`.

Everyone gets it on their next pull, with nothing to install. Claude Code may ask each person to trust the folder before it applies the repository's settings.

Then replace the two capitalised lines in CLAUDE.md with one plain one, such as: "Commit on a branch, never on main, and format the files in a commit with Prettier before staging them. A hook cancels commits that break either rule." Capitals make current models apply a rule too widely, and the hook now does the enforcing.

## What I checked, and what I didn't

- `guard-tests/run.mjs` runs the two scripts against throwaway repositories: 52 cases, all passing, with Prettier 3.6.2, git 2.56 and Node 24 on macOS. To rerun: `npm install && node run.mjs` in `guard-tests/`.
- The skill-creator check script prints `ok` for the skill.
- Not checked: a real Claude Code session with the hook registered. I started no test runs, so I have not watched Claude get cancelled and recover, and I can't say yet whether the skill text saves it a retry. The hook format comes from Claude Code's documentation as of today. Not tried on Windows.

When you want that test, I'd run three requests, each once with the guard and once without, which is six runs on your plan:

- "fix the typo in the header comment of src/format.js and commit it", starting on main
- "ok that's done, commit everything and push", on a branch with several unformatted files
- "just commit this straight to main, it's a one-line hotfix"

A good result has no new commit on main made by Claude, and every file in each commit passes `prettier --check`. In the third, Claude tells you it can't and that you can make that commit yourself.

## Limits you should know about

- It sees only `git commit` run by Claude Code. Your own commits in a terminal are untouched, which is also how you make an exception. For a rule that binds people and every tool, turn on branch protection for main on your git host as well.
- It does not check `git merge`, `git cherry-pick`, `git revert` or a push onto main. The skill tells Claude to get your go-ahead before those.
- Claude Code reads `.claude/settings.json` only in sessions started at the top of the repository. A session started in a subfolder has no guard.
- It looks for Prettier in `node_modules` at the top of the repository, or between there and the folder Claude is in. If Prettier is listed in `package.json` but not installed, it cancels the commit and says to install.
- If a commit follows some other command in the same line (say `npm test && git commit …`), the guard can't know what that command changed. It cancels and asks Claude to run the two separately. That costs one retry.

## Questions I would have asked

1. Is this for one repository or several? I assumed one, so the guard lives in that repository. For several, the same folder can be wrapped as a Claude Code plugin and installed once.
2. Should the guard also cancel merges, cherry-picks, reverts and pushes onto main? You said "commits", so I kept to `git commit`.
3. Is `main` the only branch to protect? It is one line at the top of `guard.mjs`.
4. Would you rather the guard format the files itself than cancel and have Claude do it? I chose cancelling, so that a hook never rewrites your files.
5. Do you want the six test runs?
