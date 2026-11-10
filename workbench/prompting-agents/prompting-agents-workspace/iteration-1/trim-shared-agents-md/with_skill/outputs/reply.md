I rewrote `AGENTS.md`. The old file was causing the first two complaints directly, and the third one can't be fixed by an instruction file at all, so there is one thing for you to add outside it.

## What was causing each complaint

**Asking before the unit tests.** The old file told agents to ask first in five separate lines ("NEVER make changes without asking", "ALWAYS ask for confirmation before running commands", "Ask before doing anything", and so on). Fable 5.2 and Astra both take that wording at full strength. The new file drops all of those lines and says plainly that reading files, editing hand-written code and running `make check` need no approval, with the reason: it takes 40 seconds, uses an in-memory database and has no network access.

**Running the whole e2e suite for a one-line change.** The old file said "ALWAYS run `make check` AND `make e2e` after EVERY change, no exceptions", and three more lines told them to run the tests. The agents were doing what they were told. The new file says `make check` is the check for an ordinary change, and that `make e2e` is for a change that alters a flow a test in `tests/e2e/` covers, or when the person asks.

**Hand-editing `src/gen/`.** The old rule was already as loud as a rule can be, and it was still missed. Louder wording won't help. The new file says what to do instead (edit `api/schema.yaml`, run `make codegen`), which helps, but an instruction file is something the model tries to follow, and nothing forces it to. See the first item below.

## What else you should do

1. **Enforce the `src/gen/` rule outside the model.** Add a CI step that runs `make codegen` and then fails if `git diff --exit-code src/gen/` reports a difference. That catches a hand edit from Claude Code, from Codex and from a person. If you also want to stop the edit before it happens in Claude Code, add a permission deny rule to the checked-in `.claude/settings.json`, something like `"deny": ["Edit(/src/gen/**)"]`. Check the exact syntax against the current Claude Code documentation. It won't block `make codegen`, which writes through the shell.

2. **Find out which kind of "asking" you were seeing.** If the agent asked in its reply ("shall I run the tests?"), the new file fixes it. If it was the tool's own approval prompt for a shell command, no instruction file can change that. In that case allow `make check` in the tool settings: in Claude Code, `"allow": ["Bash(make check)"]` in `.claude/settings.json`, and the matching approval setting in Codex.

3. **Confirm four things I had to guess or leave out.**
   - The rule for when to run `make e2e` is my wording. If CI already runs the suite on every pull request, change the line to say agents leave it to CI.
   - I described the three documents in `docs/` from their file names. Correct the descriptions if they are off.
   - The old file never gave the command that runs the integration tests. Add it to that line.
   - The old file said to ask before everything, so I couldn't tell which approvals were real. I kept the two that had a reason: deploys go through Priya, and a change in `migrations/` needs a second reviewer. If something else needs a go-ahead (pushing, or anything that writes to the staging stack), add it as one line that names the exact action and the reason.

4. **Look for the same old cautions elsewhere.** Nested `AGENTS.md` or `CLAUDE.md` files, each person's `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`, and any skills or saved notes the agents load. One leftover "always ask first" will bring the behaviour back. `CLAUDE.md` can stay as a one-line import of `AGENTS.md`.

5. **Test it.** Give Claude Code and Codex each a one-line change with the new file in place. Each should run `make check` without asking and leave `make e2e` alone.

## What I removed

The directory layout and the dependency list (the agent reads the repository), "read all three docs before any change" (now a pointer to which document is for what), the 2-space indentation line (the agent matches the surrounding code; put it back if your formatter doesn't enforce it), and the general lines such as "be thorough", "follow best practices" and "think step by step". The file went from 60 lines to 38. The word count is about the same, because each remaining rule now carries its reason.
