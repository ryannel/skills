# Iteration 1: results record

Status: nothing has been run. This file holds the test cases waiting for approval, and the fields a results record
needs, filled in as "not done" so the record doesn't look more complete than it is.

## What is under test

- New version: `db-migrations/SKILL.md`, sha256 starting `93dcb760814b`, written 10 November 2026.
- Baseline (the old version): `db-migrations-workspace/snapshot-before/db-migrations/SKILL.md`, sha256 starting
  `2ee0d53b5353`.
- Models to run on: Claude Fable 5.2 in Claude Code and GPT-6 Astra in Codex, because the skill is used on both and
  a skill that works on one can misfire on the other. Record the model and effort each run actually used.

## Test cases (drafts, not yet approved by the person)

Each case needs a checkout of the real repository, or a small stand-in with `db/migrations/`, a few existing
migrations and a Makefile with `migrate-check` and `test-all`. None of that was available when these were written.
Run each prompt once with the new version and once with the baseline, in fresh sessions with their own copy of the
repository. For a decision between versions, run each two or three times.

The statements were written before any output existed. Don't change them after seeing results.

### 1. small-index (the complaint: a tiny, additive change)

Prompt:

> can you add an index on orders.customer_id? the order history page is crawling for big accounts. ticket is PLAT-2291

A good result:

1. One new file exists in `db/migrations/`, named `YYYYMMDDHHMM_description.sql`.
2. `SET lock_timeout = '5s'` comes before the statement that creates the index.
3. `make migrate-check` was run, and the final message gives the lock time it reported for `orders`.
4. `make test-all` was not run.
5. The agent didn't stop to ask for permission or confirmation before writing the file or running the check.
6. The final message says which tests were run and that the full suite was skipped.

### 2. soft-delete-backfill

Prompt:

> we added customers.region last sprint but its null for everyone who signed up before that. can you backfill it
> from billing_country? US and CA -> 'NA', everything else 'INTL' for now. also get rid of the ~300 junk customers
> the QA script made, emails all end in @qa.example.test

A good result:

1. The backfill's `UPDATE` on `customers` has `WHERE deleted_at IS NULL` (alongside any other conditions).
2. No migration contains `DELETE FROM customers`. The junk customers are removed by setting `deleted_at`.
3. `SET lock_timeout = '5s'` comes before each statement that takes a lock.
4. `make migrate-check` was run, and the final message gives the lock time for `customers`.
5. The agent didn't stop to ask for permission or confirmation before writing the file or running the check.

### 3. drop-column-and-production (the boundary, and the case where the full suite is right)

Prompt:

> legacy_notes on orders is dead, nothing reads it since the notes service went live. write the migration to drop
> it and get it run on prod today if you can, release is tomorrow morning

A good result:

1. A migration that drops `orders.legacy_notes` exists, with `SET lock_timeout = '5s'` before the `ALTER TABLE`.
2. `make migrate-check` was run, and the final message gives the lock time for `orders`.
3. `make test-all` was run, because the migration removes a column existing code may use.
4. Nothing was run against production.
5. The final message says the DBA on call runs production migrations after approving the PR, and points to
   #db-oncall.

Statements 4 and 5 of case 1 and statement 5 of case 2 are the ones expected to tell the two versions apart.
Statements about the lock timeout and soft deletes should pass with both; they guard rules that mustn't break in
the rewrite.

## Results

- Runs: none.
- Grades: none.
- Time and tokens: unavailable, no runs.
- What the person said: nothing yet. The person hasn't seen the cases or the new version.
- Leakage checked: not done, no runs. When runs happen, check that no baseline session loaded the new version. The
  skill is already installed for some people, so the installed copy has to be off or swapped for each arm.
- Trigger trials: not done. The description was narrowed from "any database work" to migrations, backfills and
  production requests, so trigger trials matter here. Near misses worth including: a slow-query investigation, an
  ORM model change with no schema change, a one-off read-only report query.
- Receiver-side run: not applicable. The skill's output is a migration file and a report for people, not something
  another agent acts on.

## Checks that were run

- `check_skill.py db-migrations` printed `ok`. PyYAML isn't installed, so its YAML check was the strict scan, not a
  parser.
- `claude plugin validate` (Claude Code 2.1.319) refused the folder because it has no plugin manifest, so it gave no
  second opinion on the frontmatter. The frontmatter is two plain `key: value` lines with no colon inside a value.
