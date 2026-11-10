I rewrote AGENTS.md. Two of your three complaints were the agents doing what the old file told them to, and the new file fixes those. The third (`src/gen/`) needs enforcement outside the file, which I could not add because I only had AGENTS.md.

## What was causing each complaint

- **Asking before unit tests:** the old file said "ask before doing anything" five different ways, including "ALWAYS ask for confirmation before running commands". The new file says `make check` runs after every change without asking, and lists the three cases where stopping to ask is right.
- **Full e2e for one-line changes:** the old file said "ALWAYS run `make check` AND `make e2e` after EVERY change, no exceptions". The new file limits `make e2e` to when someone asks for it or when the change is in `tests/e2e/`.
- **Hand-editing `src/gen/`:** the old rule was already the loudest line in the file and it still got broken. It gave no reason and no other way to change the client. The new file explains why and gives the route: edit `api/schema.yaml`, run `make codegen`. That should help, but an instruction alone won't make it stop for good.

## What else to do

1. **Block `src/gen/` edits mechanically.** Add a CI step that runs `make codegen` and fails if the result differs from what is committed. That catches Claude Code, Codex and people. For Claude Code you can also add a deny rule (below), though it only stops the edit tools, not a shell command that writes the file.
2. **Allowlist `make check` in the tools.** Some of the "asking permission" may be the tool's own approval prompt, which AGENTS.md can't change. For Claude Code, commit this as `.claude/settings.json`:

   ```json
   {
     "permissions": {
       "allow": ["Bash(make check)", "Bash(make codegen)"],
       "deny": ["Edit(/src/gen/**)"]
     }
   }
   ```

   Check the rule syntax against the current Claude Code docs before committing; I wrote it from memory. For Codex, check each person's approval policy and sandbox mode. I am less sure of its config details, so I have not given a snippet.
3. **Check for other instruction files.** A personal `~/.claude/CLAUDE.md`, a `~/.codex/AGENTS.md` or a nested AGENTS.md that repeats "ask first" or "run all tests" will keep the old behaviour alive.
4. **Try it once in each tool.** Give Claude Code and Codex the same one-line change and confirm each runs `make check` unprompted and skips e2e.

CLAUDE.md importing AGENTS.md is fine as it is.

## Guesses in the new file to confirm

- **e2e policy:** I assumed something else (CI, or a person before merge) runs the full suite. If nothing does, tell me and I will widen the rule.
- **Running single e2e specs:** the file tells agents to prefer the spec files they touched, but I don't know your command for that. Add it, or delete that line.
- **Integration tests:** the old file never said how to run them. The new one says to skip them when `INTEGRATION_DB_URL` is unset. Add the command if agents should run them.
- **When to stop and ask:** I replaced "anything risky" with three cases: reaching outside the local checkout, destructive or hard-to-undo actions, and real ambiguity. Adjust to your team's line.
- **Docs pointers:** the old file required reading all three docs before any change. I made that conditional and guessed each doc's subject from its filename.

## What I removed

- The lines with no concrete action: "be thorough", "don't be lazy", "think step by step", "follow best practices", "don't break things", "keep code clean", "write good commit messages". If you have a commit message convention, give it to me and I will add it.
- The capitals and exclamation marks.
- Layout entries that only restated the folder name.
