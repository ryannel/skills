# Grades for rule-that-needs-a-hook

Graded blind on 10 November 2026. A's files are under `A/`, B's under `B/`. In B, `plugin/` below is short for
`B/team-guardrails/plugins/commit-guard/`. Line numbers are the file's own.

What I ran, all inside this folder, with nothing installed:

- `check_skill.py` on `A/commit-guard` and on `plugin/skills/commit-rules`. Both printed "ok", exit 0, no notes.
- B's shipped tests, `node --test` in `plugin/`, with the temp folder pointed inside this folder: 24 pass, 0 fail.
- A's shipped tests (`A/guard-tests/run.mjs`) were not run. They need `npm install` to fetch Prettier, which I was told
  not to do. The file holds 52 `expect(` calls, which matches the count in A's reply.
- My own probe: 22 commit commands fed to both hook scripts in throwaway repositories, with a stand-in for Prettier
  (a `.js` file counts as unformatted when it contains a marker word). Results are quoted below as "probe". The probe
  and its repositories were deleted afterwards.
- A's `setup.mjs`, with and without `--dry-run`, in one of those repositories. It wrote the hook entry and reported
  "already registered" on a second run.
- `claude plugin validate` (Claude Code 2.1.319) on `B/team-guardrails` and on `plugin/`. Both printed "Validation
  passed".
- A lookup of four host facts in the Claude Code documentation, done by a separate agent. Its findings are used in
  check 5 and in the notes.

| # | A | B | Evidence for A | Evidence for B |
|---|---|---|---|---|
| 1 | pass | pass | `A/reply.md` line 3: "A skill is the same kind of thing as CLAUDE.md: words Claude weighs against everything else it has read, and sometimes drops. ... A rule that has to hold every time needs something Claude Code runs whatever Claude decides, so the skill folder carries a hook script". | `B/reply.md` lines 1-3: "A skill would have failed the same way your `CLAUDE.md` lines do. A skill is more instructions, and Claude weighs instructions against everything else it is doing ... A hook is a command that Claude Code itself runs before each shell command, and it can refuse the command." |
| 2 | pass | pass | `A/commit-guard/scripts/guard.mjs` line 337: "if (PROTECTED_BRANCHES.includes(branch)) {", exiting 2. `scripts/setup.mjs` line 51 writes the exact hook entry: "{ matcher: "Bash", hooks: [{ type: "command", command, timeout: 120 }] }". Probe: `git commit -m x` on main was stopped (exit 2), also with a heredoc message, `--amend`, `bash -c` and an env-variable prefix. | `plugin/scripts/commit-guard.mjs` line 496: "if (PROTECTED.includes(branch) && (hasHead \|\| predicted !== undefined)) {", exiting 2. `plugin/hooks/hooks.json` line 10: "node \"${CLAUDE_PLUGIN_ROOT}\"/scripts/commit-guard.mjs". Probe: the same five commands on main were all stopped (exit 2). |
| 3 | pass | pass | `guard.mjs` line 401 runs the project's Prettier over the commit's files before the commit: "prettier(bin, top, ["--list-different", "--ignore-unknown", ...". Probe: an unformatted staged file, `git add -A && git commit`, and `git commit -am` were each stopped. Note the mechanism runs Prettier as a check and refuses; it does not format. `A/reply.md` line 21: "never changes files". I read the check as met because Prettier does run before every commit and an unformatted commit can't go through. | `commit-guard.mjs` line 564: "runPrettier(prettier, ['--list-different', '--ignore-unknown', '--', ...". Probe: the same three commands were each stopped. The same note applies. `B/reply.md` line 15: "The hook only checks. It never formats or stages files itself". |
| 4 | pass | pass | The output is a 569-line hook script, a 93-line setup script and a test file, beside the skill text. | The output is a 661-line hook script, `hooks.json`, a plugin manifest, a marketplace manifest and a test file, beside the skill text. |
| 5 | pass | unclear | `A/reply.md` lines 25-29: "Copy `commit-guard/` to `.claude/skills/commit-guard/` ... run `node .claude/skills/commit-guard/scripts/setup.mjs`. It adds one hook entry to `.claude/settings.json` ... Commit `.claude/skills/commit-guard/` and `.claude/settings.json`. Everyone gets it on their next pull". A hook in the committed project settings file is the documented route, and the documentation lookup confirmed `$CLAUDE_PROJECT_DIR` works in such a command. | The form is right on its face: `B/reply.md` lines 21-23, "copy `team-guardrails/` into the repository at `.claude/team-guardrails` ... add the settings snippet from the README to `.claude/settings.json` and commit both ... Each teammate pulls, and accepts Claude Code's trust prompt". But line 19 says "nobody installs anything", and the documentation says otherwise for the general case: "Committing that entry turns the plugin on for your collaborators but doesn't download it to their machines. Each collaborator also runs `claude plugin install <name>@<marketplace> --scope project` once per clone." (code.claude.com/docs/en/plugins/install.md). One sentence elsewhere in the docs may exempt a marketplace added from a local path, and the docs don't say whether a `directory` marketplace declared in project settings counts. So whether teammates receive a working hook from a pull alone can't be decided without a live session, and B did not run one (`B/reply.md` line 31: "I have not run them"). If the install step is needed, the reply tells teammates too little and the guard is silently off for them. |
| 6 | pass | pass | Checker count of words in capitals for `A/commit-guard/SKILL.md`: none. My own search of every file under `A/` for IMPORTANT, CRITICAL, MUST, NEVER and ALWAYS found nothing. The hook's messages to the agent are plain, for example `guard.mjs` line 339: "this repository takes no commits directly on". | Checker count for `plugin/skills/commit-rules/SKILL.md`: none. The same search of every file under `B/` found nothing. `README.md` has only names in capitals (CI, JSON, MCP, PATH). |
| 7 | pass | pass | `A/reply.md` lines 35-37: "`guard-tests/run.mjs` runs the two scripts against throwaway repositories: 52 cases, all passing ... Not checked: a real Claude Code session with the hook registered." | `B/reply.md` lines 29-31: "Tested: the hook script, with 24 automated tests in throwaway git repositories, all passing ... Not tested: the plugin loaded in a live Claude Code session." |

Passes: A 7 of 7. B 6 of 7, with check 5 unclear.

## Which I would hand to the person

A. Its delivery is the plain, documented one (a hook entry in the committed `.claude/settings.json`), where B's
one-repository route rests on plugin-loading behaviour that the documentation contradicts in general and B never
tried. A's guard also fits "never" better: when it can't tell what a command will commit, it stops the command, where
B's lets it through. In my probe B allowed `git checkout - && git commit -m x` from a branch whose previous branch
was main, which lands on main, and allowed an unformatted file written and committed in one command; A stopped both.
B has real strengths: its tests ship with the plugin and run with no install (I ran them, 24 pass), its README is
thorough, and its plugin route is the right one if the team has several repositories.

## What the checks don't cover

- **B's guard lets through what it can't work out; A's stops it.** Probe, B allowed and A stopped:
  `git checkout - && git commit -m x` (commit lands on main), and
  `printf '...' > new.js && git add new.js && git commit -m x` (the unformatted file is committed). B also lets a commit
  through when the guard itself crashes (`B/reply.md` line 43, a stated choice); A cancels the command and tells the
  agent to tell the person (`guard.mjs` lines 558-561). For a rule the person wants held every time, B's choices are
  the weaker ones, and only the crash case is disclosed.
- **A's strictness costs retries on correct commits.** Probe: on a branch with formatted files, A stopped
  `npm test && git commit -m x` and `npx prettier --write a.js && git add a.js && git commit -m x`; B allowed both.
  A says so (`A/reply.md` line 53: "That costs one retry") and the skill teaches the allowed forms. Whether agents
  learn it or loop is untested.
- **Neither sees a commit made through a git alias.** Probe: with `alias.ci = commit`, `git ci -m x` on main was
  allowed by both. Neither output mentions this. Both do disclose that merge, cherry-pick, revert and push onto main
  are not checked, and both point to branch protection.
- **Neither one runs Prettier for the person; both refuse and make the agent run it.** The request was "always runs
  prettier before committing". Both chose refusing over formatting and both say why. A asks the person about it
  (`A/reply.md` line 60); B doesn't ask.
- **Neither mentions an ordinary git pre-commit hook** (for example husky with lint-staged), which is the usual way
  to run Prettier on every commit, would format the files, and would bind people and every tool. Each instead ships
  600-odd lines of hand-written shell-command reading for the team to own. A person might reasonably prefer the
  smaller thing.
- **Things B added or decided without being asked, all disclosed:** it protects `master` as well as `main`
  (`B/reply.md` line 53), and it lets the first commit of a new repository through on main (line 52; probe confirms,
  and A stops that commit). The manifests carry a placeholder owner, "Your team" (line 55).
- **A's claims I could check held up.** The documentation confirms that the shared settings file is read from the
  session's starting folder, so A's warning that "a session started in a subfolder has no guard" (`A/reply.md` line
  51) is correct, and B doesn't mention that limit even though its route also depends on that file. A's 52-case
  figure matches the test file but I could not rerun it. B's "Prettier 3.9.9" hand run and A's "Prettier 3.6.2" run
  are unverified.
- **A's tests sit outside the skill folder** (`A/guard-tests/`), so they don't travel with the copy the team commits
  unless the person moves them, and they need a network install to run.
- **Neither was tried in a live Claude Code session**, and both say so. So that the hook fires, that the agent
  recovers after being stopped, and that either skill's text saves a retry are all unproven.
