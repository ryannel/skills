---
name: commit-guard
description: Makes commits that pass this repository's commit guard, a hook that cancels any `git commit` on main and any commit holding a file Prettier has not formatted. Use when committing changes, or when a commit was cancelled by the guard.
compatibility: Claude Code, with Node 18 or later and git. The hook is registered once per repository with scripts/setup.mjs.
---

# Commit guard

This repository has two rules for commits. No commit is made on `main`, and every file in a commit is formatted
with Prettier. A hook enforces both: before each Bash command, Claude Code runs `scripts/guard.mjs`, which
cancels a command whose `git commit` breaks a rule and prints the reason. Knowing what the guard checks lets
you make a commit that goes through the first time.

This skill says how to commit, not when. Commit when the task calls for a commit.

## Before you commit

Be on a branch other than `main`. If you are on `main`, run `git switch -c <branch-name>`. Staged and unstaged
changes come along.

Format the files that will be in the commit with the project's own Prettier, and stage them after formatting:

```
npx prettier --write <files>
git add <files>
```

The guard checks the staged content. A file that was staged and then formatted still fails until you stage it
again. Format only the files in your commit, because formatting the whole repository puts files nobody asked
you to change into the diff.

The guard reads the repository before the command starts. So in the Bash command that holds `git commit`, the
only things that may come before it are `cd`, `git add`, `git status`, `git diff`, `git log`, `git show`,
`git switch -c <name>` and `git checkout -b <name>`. The guard works out what those will do. Run anything else,
such as the Prettier command above, as a separate command first. What comes after `git commit` is not
restricted.

The commit is finished when `git commit` ran without being cancelled and `git log -1` shows it on your branch.

## When the guard cancels a command

None of the cancelled command ran, including the parts before `git commit`. The message names the rule and the
files. Fix that cause and run the commit again.

Don't make the commit some other way, such as through a script, another tool, or a change to the guard or to
`.claude/settings.json`. The team agreed these two rules, and the person has not agreed an exception. If the
person wants a commit the guard won't allow, such as a hotfix on `main`, tell them the guard applies only to
commands you run, so they can make that commit themselves in a terminal.

## What the guard doesn't see

The guard checks `git commit` in this repository and its worktrees. A commit in any other repository is let
through.

It doesn't check the other commands that put commits on `main`: `git merge`, `git cherry-pick` and `git revert`
run while on `main`, and a push to `main`. Get the person's go-ahead before you run one of those.

The hook is registered in `.claude/settings.json` at the top of the repository, and Claude Code reads that file
only when the session was started there. In a session started in a subfolder nothing cancels a wrong commit.
The two rules hold all the same.

## The scripts

- `scripts/guard.mjs` is the hook. Claude Code runs it, so you don't need to.
- `scripts/setup.mjs` registers the hook in the repository's `.claude/settings.json`. Whoever installs this
  skill runs it once for the repository. Run it only when the person asks you to set the guard up.
  `node scripts/setup.mjs --dry-run` prints the change and writes nothing.
