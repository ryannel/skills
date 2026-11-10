# Grades for modernise-old-skill

Graded blind on 10 November 2026. Evidence is quoted from `A/db-migrations/SKILL.md` and
`B/db-migrations/SKILL.md` unless another file is named. Line numbers are the file's own.

| # | A | B | Evidence for A | Evidence for B |
|---|---|---|---|---|
| 1 | pass | pass | Line 2: "name: db-migrations". `check_skill.py` printed "ok", exit 0, no notes. | Line 2: "name: db-migrations". `check_skill.py` printed "ok", exit 0, no notes. |
| 2 | pass | pass | Lines 20-22: "Put `SET lock_timeout = '5s'` in the migration before any statement that takes a lock, so that it is in effect for each of them. With it, a statement that can't get its lock fails after five seconds. Without it, the statement waits, and every later query on that table queues behind it. That is what caused the 2024 outage." | Lines 22-24: "Put `SET lock_timeout = '5s';` before every statement that takes a lock. In 2024 an `ALTER TABLE` waited behind a long report query and blocked checkout for 11 minutes." |
| 3 | pass | pass | Line 24: "The `orders` and `customers` tables mark a deleted row by setting `deleted_at`. They don't remove the row." | Line 26: "`orders` and `customers` use soft deletes. A row is removed by setting `deleted_at`, and it stays in the table." |
| 4 | pass | pass | Lines 30-32: "Run `make migrate-check`. It applies the migration to the staging copy of the database and reports the lock time for each table. The staging copy is refreshed from production every night at 02:00 UTC" | Lines 31-32: "Run `make migrate-check`. It applies the migration to the staging copy and reports the lock time per table. The staging copy is refreshed from production every night at 02:00 UTC" |
| 5 | pass | pass | Lines 47-48, the only statement of it: "Don't run a migration, or anything else, against the production database. The DBA on call runs each production migration after approving its pull request." No "ask before" or "confirm" line anywhere (searched). | Lines 17-18: "Don't run a migration against production, even when someone asks you to. The DBA on call runs it after approving the PR." No "ask before" or "confirm before" line (searched). Lines 14-15, one paragraph earlier, also say "nothing reaches production until a DBA has approved the PR", given as the reason the agent may work freely. I read that as a reason and not a second statement of the rule. |
| 6 | pass | pass | Lines 51-52: "Reading the schema, writing and editing files in `db/migrations/`, and running `make migrate-check` or `make test-all` need no go-ahead." | Lines 13-14: "Reading the repository, creating and editing files in `db/migrations/`, running `make migrate-check` and running tests don't need permission or a confirmation first." |
| 7 | pass | pass | Lines 39-42: "Run it once, when the migration is otherwise finished, if the migration could break code that already works: it drops or renames a table or column, changes a column's type, or adds a constraint ... A change that can't break existing code doesn't need it" | Lines 35-36: "Then run tests sized to the change. `make test-all` is the full suite and takes about 25 minutes, so keep it for a migration that changes something existing code already uses" |
| 8 | pass | pass | No ban in the skill. Lines 34-36 replace it: "fix the migration and run the check again without asking. Running it again after a failure is safe on migrate-tool 3.2". `A/reply.md` line 55: "Is retrying safe on migrate-tool 3.2? I trusted the old note and removed the ban." | No mention of retrying in the skill (searched). `B/reply.md` lines 29-30: "The "never retry a failed migration" rule is gone. Its own note said it was a workaround for migrate-tool 1.x", and line 61: "I assumed so and removed the rule." |
| 9 | pass | pass | Checker count of words in capitals: none. My own search found only SQL keywords inside code, plus SQL, DBA and UTC. | Checker count: none. My own search found only SQL keywords inside code, plus SQL, DBA, PR and UTC. |
| 10 | pass | pass | Headings: "Writing the migration", "Checking it", "Production". | Headings: "What you may do without asking", "Two rules for the SQL", "Check the migration", "When you're finished". The last is about stopping, not about when to load the skill. |
| 11 | pass | pass | Line 3: "Use when adding or changing a migration, changing the schema (a table, column, index or constraint) or backfilling data, or when asked to run a migration in production." | Line 3: "Writes and checks SQL migrations in db/migrations/ ... Use when adding, changing or dropping a table, column, index or constraint, backfilling or removing rows in bulk, or when someone asks to run a migration in production." The "use when" names what a migration does and not the migration, so this is the less plain of the two, but it claims nothing beyond migration work. Neither description names reviewing a migration. |
| 12 | pass | pass | A search of the skill for "subagent", "step by step", "double-check", "thorough" and "lazy" found nothing. | The same search found nothing. |
| 13 | pass | pass | `A/reply.md` lines 11-20, a table of old against new, for example line 18: "Removed. The skill's own note says it was a workaround for migrate-tool 1.x and you are on 3.2", and line 19: "Removed. Fable 5.2 delegates for its own sake when told to". | `B/reply.md` lines 25-37, for example lines 31-32: ""Use subagents to parallelize whenever possible" is gone. Current models take that literally and delegate a one-file job." |
| 14 | pass | pass | `A/db-migrations-workspace/old/db-migrations/SKILL.md` is identical to `original/db-migrations/SKILL.md` (diff shows no difference). `A/reply.md` line 34 names it. | `B/db-migrations-workspace/snapshot-before/db-migrations/SKILL.md` is identical to the original (diff shows no difference). `B/reply.md` line 76 names it. |

Passes: A 14 of 14, B 14 of 14.

## Which I would hand to the person

A, narrowly, because of the production rule. The old skill said "NEVER touch production". A keeps the full width of
that (line 47: "Don't run a migration, or anything else, against the production database") and asks the person whether
read-only queries are included. B narrows it to migrations only (line 17: "Don't run a migration against production")
and calls production "the one boundary" without telling the person the boundary moved. For a rewrite whose purpose
is to make the agent ask less, the one rule that must not get weaker is that one. A's test rule is also simpler to
follow: additive changes need no tests beyond the check. B's skill is the better-organised read, it keeps the old
step "read a few recent ones before you write a new one" which A drops without saying so, and its finish line asks
for a fuller report.

## What the checks don't cover

- **B weakens the production rule without flagging it.** Described above. Under B's text a manual `ALTER TABLE` or
  a data fix run by hand against production isn't a "migration" and isn't forbidden. `B/reply.md` line 10 repeats
  the narrow form ("the agent doesn't run migrations there even if asked") as if nothing changed.
- **A's reply attributes a constraint to the person that the request doesn't contain.** `A/reply.md` line 1: "you
  asked for no test runs". The request in `checks.md` says nothing about tests. B's version of the same point
  (`B/reply.md` lines 1-2: "you weren't around to approve test prompts, and test runs spend your quota") doesn't put
  words in the person's mouth. If A was given that constraint somewhere I can't see, the sentence is fine; from what
  is in the folder it reads as invented.
- **A states an unverified fact inside the skill.** Line 35: "Running it again after a failure is safe on
  migrate-tool 3.2, which the project uses." The old skill only said the corruption was a 1.x problem. A's reply
  admits the guess (question 2), but an agent reading the skill gets it as fact. B removes the ban and says nothing
  in the skill, which is the safer of the two.
- **B invents a middle tier of testing with no command behind it.** Lines 38-39: "For those, run the tests that cover
  the tables it touches." The old skill names only `make test-all`. An agent has to find those tests itself, and line
  44 makes "the tests you chose pass" part of finished. B's reply says the split is its own judgement
  (`B/reply.md` line 21). A's split is also a guess and A also says so (`A/reply.md` line 54).
- **A dropped the old step 2 and didn't list it.** The original line 17, "Look at the existing migrations in
  `db/migrations/` to understand the conventions", has no counterpart in A, and A's change table folds it into "Ten
  numbered steps" replaced by "the facts an agent can't guess". B keeps it (lines 8-9).
- **A changed the lock rule's wording slightly.** The original and B say the `SET` comes before every statement that
  takes a lock. A says to put it in the migration "before any statement that takes a lock, so that it is in effect for
  each of them", which is one `SET` per file. That is correct only if the migration tool runs a file in one session.
  A's reply lists the rule as kept unchanged.
- **Both replies state how particular models behave as fact.** `A/reply.md` line 5: "Fable 5.2 follows every caution
  it finds. Astra stops to ask when two lines disagree." `B/reply.md` lines 36-37: "Astra, which works best when
  told where to stop". Neither has run anything, and both say so.
- **B's reply has a stray placeholder.** `B/reply.md` line 73: "All under `the project folder`:".
- **What I could verify of B's record is true.** The two sha256 prefixes in
  `B/db-migrations-workspace/iteration-1/results.md` match the files, and PyYAML is indeed not installed here. Its
  claim about `claude plugin validate` I did not test.
- **A ships runnable-looking test cases, untested.** `A/db-migrations-workspace/new/db-migrations/evals/` holds three
  cases with graders. A says it made up the column names and "couldn't confirm they load" (`A/reply.md` line 45). The
  copy of the skill the person would install (`A/db-migrations/`) doesn't contain them, which is right.
- **Neither rewrite was run on any model**, so whether the two complaints are fixed is unproven for both. Both say
  this in their first paragraph.
