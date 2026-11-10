---
name: commit-rules
description: Gives the order of steps for a git commit in this team's repositories, where a hook called commit-guard blocks commits on main and commits with files that aren't Prettier-formatted. Use before running git commit, or when commit-guard has blocked one.
---

# Commit rules

This team has two rules for every commit:

1. Commits never go on `main` (or `master`). They go on a branch.
2. Every file in a commit is formatted with the project's Prettier.

A hook called commit-guard checks both before any `git commit` you run, and blocks the command if either is broken.
Its message names the rule and the files.

The guard looks at the repository as it is when the commit command starts. It can't see what an earlier part of
the same command line is about to change, apart from `git add` and a new branch. So take the steps as separate
commands, in this order:

1. If you're on `main`, move to a branch: `git switch -c <short-name-for-this-work>`. Uncommitted changes come along.
2. Format the files you changed: `npx prettier --write -- <files>`.
3. Stage them and commit. `git add` can share a line with `git commit`.

This one gets blocked, because the files are still unformatted when the guard looks:

```
npx prettier --write src/ && git add -A && git commit -m "Tidy the parser"
```

Run the Prettier step first, on its own, and the same add and commit then pass.

If the person asks for a commit on `main` itself, tell them the guard blocks it and let them make that commit. It
only checks commits made through Claude Code, so theirs will go through.
