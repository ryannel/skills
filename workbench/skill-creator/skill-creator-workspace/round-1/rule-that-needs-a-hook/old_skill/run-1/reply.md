I built this as a Claude Code plugin with a hook in it, not as a skill on its own. A skill would have failed the same way your `CLAUDE.md` lines do.

A skill is more instructions, and Claude weighs instructions against everything else it is doing, which is why the capitals haven't worked. A hook is a command that Claude Code itself runs before each shell command, and it can refuse the command. Claude can't forget it. A plugin is the package that carries a hook to other people.

## What you have

Everything is in `team-guardrails/` in this folder. The plugin inside it is called `commit-guard`.

- **The hook** runs before every `git commit` Claude makes and blocks it in two cases:
  - The commit would land on `main` or `master`. Claude is told to make a branch.
  - A file in the commit isn't formatted with the project's own Prettier. Claude is told which files to format and stage.
- **A short skill**, `commit-rules`, tells Claude the order of steps so its first try usually passes. The hook does the enforcing. You can delete the skill and lose nothing but that.
- **A README** has the install steps and the full list of limits.

The hook only checks. It never formats or stages files itself, so it can't change what a commit contains.

## Getting it to the team

If the rules are for one repository, the plugin can live in that repository, and nobody installs anything:

1. You copy `team-guardrails/` into the repository at `.claude/team-guardrails`.
2. You add the settings snippet from the README to `.claude/settings.json` and commit both.
3. Each teammate pulls, and accepts Claude Code's trust prompt for the folder if they haven't before.

If it is for several repositories, the plugin goes in its own repository and each person runs one install command. The README covers that route too.

## What I tested, and what I didn't

- **Tested:** the hook script, with 24 automated tests in throwaway git repositories, all passing. They cover Claude's usual commit shapes: a heredoc message, `git add … && git commit`, `git commit -am`, and a commit from a subfolder. The tests use a stand-in for Prettier, so I also ran the main cases by hand against a real Prettier 3.9.9, and they behaved the same.
- **Tested:** `claude plugin validate` passes for the plugin and for the `team-guardrails` folder.
- **Not tested:** the plugin loaded in a live Claude Code session. The install steps come from the Claude Code docs as of 10 November 2026 (Claude Code 2.1.319) and I have not run them. Before you tell the team, do the two-minute check in the README: ask Claude to commit while on `main` and watch it get refused.
- **Not tested:** whether the `commit-rules` skill loads when it should.

I can run with-and-without comparisons in fresh sessions if you want them. They use your quota, so I haven't started any. I'd use three prompts:

1. On `main`, with an unformatted edit: "ok the retry fix in src/api/client.ts looks good, commit it"
2. On a branch, with one formatted file and one unformatted: "commit what we have so far, msg something like 'add csv export'"
3. On `main`: "just commit this straight to main, it's a one-line typo fix in the README"

## Limits worth knowing now

- The hook covers `git commit` run by Claude Code. It doesn't cover your own commits, or `git merge`, `git revert`, `git cherry-pick` and `git push` onto `main`. Branch protection on your git host and a Prettier check in CI cover those.
- If the hook script crashes, the commit goes through and an error shows in the session. I chose that so a bug in the hook can't stop the team committing.
- A project that lists Prettier but hasn't installed its dependencies gets its commits blocked until it has.

One more suggestion: once the hook is on, replace the two capitalised lines in `CLAUDE.md` with one plain sentence. Capitals tend to make Claude apply a rule more widely than you meant, and the hook now does the enforcing.

## Questions I would have asked

1. Is this for one repository or several? I wrote up both routes and led with one repository.
2. Should Claude also be blocked from `git merge`, `git revert`, `git cherry-pick` and `git push` onto `main`? I kept to commits, which is what you asked for.
3. I let the very first commit of a brand-new repository through on `main`, because no other branch exists yet. Is that right for you?
4. I protect `master` as well as `main`. Are there other branches to protect, such as release branches? One setting changes the list.
5. Does any project use Yarn Plug'n'Play, or keep Prettier somewhere other than `node_modules`? The hook would block every commit there.
6. What name should go in as the owner? `marketplace.json` and `plugin.json` both say "Your team" for now.
