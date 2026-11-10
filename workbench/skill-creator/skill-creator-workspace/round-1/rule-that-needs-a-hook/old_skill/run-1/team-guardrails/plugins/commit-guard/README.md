# commit-guard

A Claude Code plugin that stops two things: a `git commit` on `main`, and a `git commit` that contains files not
formatted with Prettier. It does this with a hook, which Claude Code runs before every Bash command. Claude can't
forget a hook the way it forgets a line in `CLAUDE.md`.

## What's in it

| File | What it does |
| --- | --- |
| `hooks/hooks.json` | Tells Claude Code to run the guard before every Bash command. |
| `scripts/commit-guard.mjs` | The guard. Plain Node, no dependencies. |
| `skills/commit-rules/SKILL.md` | A short skill that tells Claude the order of steps, so its first try passes. |
| `tests/commit-guard.test.mjs` | Tests for the guard. Run `node --test` in this folder. |

## What the guard checks

When a Bash command contains a `git commit`, the guard checks:

1. **The branch.** If the commit would land on `main` or `master`, it is blocked, and Claude is told to make a
   branch. The first commit of a brand-new repository is let through.
2. **The formatting.** It works out which files the commit would contain, and runs the project's own Prettier over
   them (`node_modules/prettier`, with the project's config and `.prettierignore`). If any file would change, the
   commit is blocked, and Claude is told which files to format and stage.

The guard reads the files. It never changes them, and it never stages anything.

A blocked commit looks like this to Claude:

```
commit-guard blocked this commit.

These files would be committed without Prettier formatting (paths from /work/shop):
  src/cart.ts
Format them, stage the result, then run the commit again:
  npx prettier --write -- src/cart.ts
  git add -- src/cart.ts
```

## Installing it for the team

There are two ways. Pick by how many repositories need it.

### One repository: keep the plugin in the repository

Nobody has to install anything. Everyone who pulls gets the guard.

1. Copy the whole `team-guardrails` folder into the repository, at `.claude/team-guardrails`.
2. Add this to the repository's `.claude/settings.json`, and commit both:

   ```json
   {
     "extraKnownMarketplaces": {
       "team-guardrails": {
         "source": { "source": "directory", "path": "./.claude/team-guardrails" }
       }
     },
     "enabledPlugins": {
       "commit-guard@team-guardrails": true
     }
   }
   ```

3. Each person starts Claude Code in the repository and accepts the trust prompt for the folder, if they haven't
   already. Claude Code ignores `extraKnownMarketplaces` in a folder that isn't trusted, and says nothing about it.

### Several repositories: give the plugin its own repository

1. Push the `team-guardrails` folder as its own git repository, for example `your-org/team-guardrails`.
2. In each repository that needs the guard, add this to `.claude/settings.json`:

   ```json
   {
     "extraKnownMarketplaces": {
       "team-guardrails": {
         "source": { "source": "github", "repo": "your-org/team-guardrails" }
       }
     },
     "enabledPlugins": {
       "commit-guard@team-guardrails": true
     }
   }
   ```

3. Each person runs this once in each of those repositories:
   `claude plugin install commit-guard@team-guardrails --scope project`.
   Project settings enable the plugin but don't download it.

If your organisation has managed settings, an admin can put the same two keys there instead. Then Claude Code
installs the plugin on every machine by itself, and nobody can turn it off.

When you change the plugin, raise `version` in `.claude-plugin/plugin.json`. People who installed it from a hosted
repository stay on their copy until the version changes.

### Check that it's on

Run `/plugin` in Claude Code and look for `commit-guard` under the installed plugins, with no entry in the Errors
tab. Then ask Claude to commit something while on `main`. The commit should be refused with the message above.

## Settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `COMMIT_GUARD_BRANCHES` (environment variable) | `main,master` | Branches the guard protects, separated by commas. Set it under `env` in `.claude/settings.json`. |

## What it doesn't do

- It only sees commits Claude makes with `git commit` through the Bash tool. A person's own commits, commits made
  by a git MCP server, and commits made inside a script that Claude runs are not checked. Branch protection on the
  server and a `prettier --check` step in CI cover those.
- It doesn't block `git merge`, `git cherry-pick`, `git revert` or `git push` on `main`.
- It checks files as they are when the command starts. If Claude chains `prettier --write` in front of the commit
  on one line, the guard blocks it, and Claude has to run Prettier first as its own command. The message says so.
- It needs Prettier in `node_modules`, between the folder the commit runs in and the top of the repository. A
  project that lists Prettier but hasn't installed it gets its commits blocked until it is installed. Yarn
  Plug'n'Play projects have no `node_modules`, so they would be blocked every time.
- A project with no sign of Prettier is not checked for formatting. The branch rule still applies.
- If the guard itself crashes, the commit goes ahead and the error is shown to the person. It fails open so that a
  bug in the guard can't stop the team committing.
- It needs `node` on the PATH, which a project that uses Prettier has.

## Host facts this relies on

Checked on 10 November 2026 against the Claude Code docs, with Claude Code 2.1.319 installed. Recheck them if a
later release changes hooks or plugins.

- A plugin's `hooks/hooks.json` loads when the plugin is enabled, and `${CLAUDE_PLUGIN_ROOT}` is the plugin's folder.
- A `PreToolUse` hook gets JSON on stdin with `tool_name`, `tool_input.command` and `cwd`. Exit code 2 blocks the
  tool call and shows stderr to Claude. Other non-zero codes don't block.
- A hook with no `args` runs through a shell, so the plugin path is quoted in `hooks.json`.
- In a repository's `.claude/settings.json`, a `directory` marketplace with a relative path resolves against the
  repository's main checkout, and its plugins load without an install step.
