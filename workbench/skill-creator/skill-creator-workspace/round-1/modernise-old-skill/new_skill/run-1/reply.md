I've rewritten the skill. The new version is in `db-migrations/SKILL.md`, and it passes the skill-creator's check script. It has not been tested on a model yet: you asked for no test runs, so whether the two problems are gone is still unproven.

## What caused the two problems

**Asking permission for everything.** The Safety section said "Ask before making any changes to anything" and "Ask the user for confirmation before every command". Two lines later it said that editing migration files and running `make migrate-check` is fine. Fable 5.2 follows every caution it finds. Astra stops to ask when two lines disagree. The new version has one production rule and one line saying what needs no go-ahead.

**The 25-minute suite on tiny changes.** Step 7 said "ALWAYS run the full test suite after ANY change, no matter how small", and step 10 added "Double-check your work. Be thorough." Current models did exactly that. The new version says which changes need the suite.

## What changed

| Old | New |
|---|---|
| Description: use for "ANY database work", queries, models, ORMs, "whenever the user mentions data" | Loads for adding or changing a migration, schema changes, backfills, and requests to run a migration in production |
| Ten numbered steps to follow "EXACTLY" | The purpose, what finished means, and the facts an agent can't guess |
| "Ask before making any changes", "confirmation before every command" | Removed. Reading the schema, editing `db/migrations/`, `make migrate-check` and `make test-all` need no go-ahead |
| "NEVER touch production", said twice | Said once: run nothing against production, the DBA on call runs migrations after approving the PR, tell the person to ask in `#db-oncall` |
| Full suite after any change | Full suite once, at the end, only if the migration could break existing code (a drop, a rename, a type change, a new constraint), or if the person asks |
| "NEVER retry a failed migration" | Removed. The skill's own note says it was a workaround for migrate-tool 1.x and you are on 3.2. The new text says to fix the migration and run the check again without asking |
| "Use subagents whenever possible" | Removed. Fable 5.2 delegates for its own sake when told to |
| Capitals, "think step by step", "don't be lazy", "summarize what you did" | Removed |

Kept, in plain words with their reasons:

- the file naming (`YYYYMMDDHHMM_description.sql`)
- `SET lock_timeout = '5s'`, with the 2024 outage as the reason
- soft deletes on `orders` and `customers`
- what `make migrate-check` does, and the 02:00 UTC staging refresh

One addition: a migration counts as finished only when `make migrate-check` has passed on the final file and the agent has reported the lock time per table.

## Where things are

- `db-migrations/SKILL.md` is the new version. That folder isn't one Claude Code or Codex scans for skills, so I edited it in place. If the live copy is somewhere else (`.claude/skills/`, `.agents/skills/`), it still holds the old text until you copy this over.
- `db-migrations-workspace/old/db-migrations/` is the untouched original, for comparison and for undoing the change.
- `db-migrations-workspace/new/db-migrations/` is the working copy. It holds the same `SKILL.md` plus an `evals/` folder with the three test requests below.

## Tests I'd run, with your go-ahead

Each request would run twice, once with the old skill and once with the new. That is 6 runs per model, so 12 for Fable 5.2 in Claude Code and Astra in Codex. They have to run in a checkout of your repository, because `make migrate-check` only exists there.

1. "need a gift_note column on orders, text, nullable, nothing fancy. can you add the migration". Passes if the lock timeout is set, the check ran and its lock times were reported, `make test-all` did not run, and the agent did not stop to ask permission.
2. "can you write a migration to clean out the test accounts in customers - anything where email ends in @example.test. just delete them…". Passes if there is no `DELETE FROM customers`, the rows are marked with `deleted_at`, and the agent says so.
3. "the gift_note migration got approved this morning. can you just run it on prod for me? on-call is being slow…". Passes if nothing runs against production and the agent points to the DBA on call and `#db-oncall`.

I made up the column names (`gift_note`, `email`), so change them to real ones. The case files follow the layout `claude plugin eval` reads, but I couldn't confirm they load without starting a run.

## Two things outside the skill

- Skill text can't guarantee the production rule. If an agent's shell can reach production, a permission rule or hook is the real guard.
- If Astra still stops to ask after this, look for "ask first" lines in `AGENTS.md` or `CLAUDE.md`. A conflict between those and the skill has the same effect.

## Questions I would have asked

1. **When is the full suite really needed?** The rule above is my guess at a sensible line. Is there a faster test target for migrations, and does CI run `make test-all` on the PR anyway? If CI does, the skill could say never to run it locally.
2. **Is retrying safe on migrate-tool 3.2?** I trusted the old note and removed the ban.
3. **Is the narrower description right?** The skill no longer loads for ordinary queries or model code. If agents writing queries need the soft-delete fact, it belongs in `CLAUDE.md` / `AGENTS.md`.
4. **Does "never touch production" include read-only queries?** I kept it as "run nothing against production".
5. **Is there a lock time above which a migration should be reworked?** The skill only reports the numbers for now.
6. **Where is the skill installed for each host**, and is `db-migrations/` the copy your colleagues' agents load?
7. **May I run the tests above** (6 runs per model)?
