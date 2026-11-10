I've rewritten `db-migrations/SKILL.md`. It hasn't been tested on either model yet: you weren't around to approve
test prompts, and test runs spend your quota, so I stopped at a checked draft.

## The two problems you saw

**Asking permission for everything.** The old Safety section said "Ask before making any changes to anything" and
"Ask the user for confirmation before every command", and the next paragraph said editing migrations and running
`make migrate-check` was fine. Newer models follow the stricter line. The new version says plainly that reading,
editing files in `db/migrations/`, running `make migrate-check` and running tests need no confirmation. Production
is the one boundary: the agent doesn't run migrations there even if asked, and points people to #db-oncall.

**The 25-minute suite on tiny changes.** The old step 7 said to always run `make test-all` "after ANY change, no
matter how small", and the agent did exactly that. The new rule sizes the tests to the change:

- `make test-all` when the migration changes something existing code already uses: a dropped, renamed or retyped
  column, a dropped table, or a new constraint on a column that's already written to.
- Only the tests covering the touched tables when the migration just adds something (a new table, a nullable
  column, a non-unique index).
- Only `make migrate-check` for an edit that doesn't change what the SQL does.

That split is my judgement, not something from your repo, so please check it (question 1).

## What else changed

- **The description is narrower.** It used to claim "ANY database work… whenever the user mentions data", which
  loads the skill on tasks it has nothing to say about. It now fires on migrations, schema changes, bulk backfills
  and deletes, and requests to run something in production. It will no longer load for ordinary queries or ORM
  model work (question 3).
- **The "never retry a failed migration" rule is gone.** Its own note said it was a workaround for migrate-tool 1.x
  and that you've been on 3.2 since March (question 2).
- **"Use subagents to parallelize whenever possible" is gone.** Current models take that literally and delegate a
  one-file job.
- **The filler is gone:** "think step by step", "be thorough", "don't be lazy", "read the request carefully", and
  the capitals. Current models do these unprompted, and the shouting makes them apply rules too widely.
- **A definition of finished is new.** The file is written, the check passes, the chosen tests pass, then stop. The
  report gives the file name, the lock time per table, and which tests ran. This is mainly for Astra, which works
  best when told where to stop.

Kept, with their reasons attached: the file naming, the 5-second lock timeout and the 2024 checkout outage behind
it, soft deletes on `orders` and `customers`, and what `make migrate-check` does and why its lock times can be
trusted. I carried these facts over from the old skill and couldn't verify any of them against your repo.

## Where things stand

- The format checker passed. A second validator, `claude plugin validate`, couldn't run on a bare skill folder.
- Nothing is installed or published. I only edited the copy in `db-migrations/`. If Codex and Claude Code load
  separate copies on people's machines, each needs the update.
- Three draft test prompts with pass/fail statements are in `db-migrations-workspace/iteration-1/results.md`: a
  small index, a backfill on `customers`, and a column drop with "get it run on prod today". They need a checkout of
  your repo to run in.
- If the agent still stops for approval after this, that's the harness's own permission prompt, not the skill.
  Allowing `make migrate-check` in Claude Code's permission settings, or Codex's approval settings, fixes that.
- The production rule is still only prose, which agents weigh against the request in front of them. If the agent's
  environment can reach production at all, withholding the credentials or adding a permission rule is the only
  reliable block.

## Questions

1. Is the test split right? In particular, is there a narrower make target than `make test-all` I should name, and
   does CI run the full suite on every PR? If CI does, the skill could drop `make test-all` altogether.
2. Is re-running a failed migration safe on migrate-tool 3.2? I assumed so and removed the rule.
3. Should the skill still load for non-migration database work? If the soft-delete rule matters for everyday
   queries on `orders` and `customers`, it belongs in the repo's `AGENTS.md` or `CLAUDE.md`, where it's always in
   view.
4. Is there a lock time above which a migration shouldn't go ahead? Right now the agent only reports the numbers.
5. Should a backfill ever include soft-deleted rows, for example when filling a column that will become `NOT NULL`?
   I kept the old rule: always filter on `deleted_at IS NULL`.
6. Do you want me to run the three test prompts, old version against new, on Fable 5.2 and on Astra? Are the
   prompts realistic for your team?

## Files

All under `/Users/ryannel/Workspace/skills/workbench/skill-creator/skill-creator-workspace/round-1/modernise-old-skill/old_skill/run-1/`:

- `db-migrations/SKILL.md`: the new version
- `db-migrations-workspace/snapshot-before/db-migrations/SKILL.md`: the old version, untouched, for comparison
- `db-migrations-workspace/iteration-1/results.md`: draft test cases and the "nothing run yet" record
