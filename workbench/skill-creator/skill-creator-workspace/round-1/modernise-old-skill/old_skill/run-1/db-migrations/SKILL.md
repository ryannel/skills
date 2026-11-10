---
name: db-migrations
description: Writes and checks SQL migrations in db/migrations/ for this repository, covering the lock timeout rule, the soft-delete tables and the staging check. Use when adding, changing or dropping a table, column, index or constraint, backfilling or removing rows in bulk, or when someone asks to run a migration in production.
---

# Database migrations

A migration is a SQL file in `db/migrations/`, named `YYYYMMDDHHMM_description.sql`. Read a few recent ones before
you write a new one, and follow what they do.

## What you may do without asking

Reading the repository, creating and editing files in `db/migrations/`, running `make migrate-check` and running
tests don't need permission or a confirmation first. The check only touches the staging copy, and nothing reaches
production until a DBA has approved the PR.

Production is the one boundary. Don't run a migration against production, even when someone asks you to. The DBA on
call runs it after approving the PR. If someone wants a migration in production, tell them to ask in #db-oncall.

## Two rules for the SQL

Put `SET lock_timeout = '5s';` before every statement that takes a lock. In 2024 an `ALTER TABLE` waited behind a
long report query and blocked checkout for 11 minutes. With the timeout, a statement that can't get its lock fails
after five seconds instead of holding up the queries behind it.

`orders` and `customers` use soft deletes. A row is removed by setting `deleted_at`, and it stays in the table. So
don't write `DELETE FROM` on either table, and add `WHERE deleted_at IS NULL` to any backfill on them.

## Check the migration

Run `make migrate-check`. It applies the migration to the staging copy and reports the lock time per table. The
staging copy is refreshed from production every night at 02:00 UTC, so the table sizes are realistic and the lock
times are a fair guide to what production will see.

Then run tests sized to the change. `make test-all` is the full suite and takes about 25 minutes, so keep it for a
migration that changes something existing code already uses: a dropped, renamed or retyped column, a dropped table,
or a new constraint on a column that's already written to. A migration that only adds something, like a new table, a
nullable column or a non-unique index, can't break code that doesn't know about it yet. For those, run the tests
that cover the tables it touches. An edit that doesn't change what the SQL does, like a comment, needs only the
check.

## When you're finished

The work is finished when the migration file is written, `make migrate-check` passes, and the tests you chose pass.
Stop there. In your report give the file name, the lock time per table from the check, which tests you ran, and
whether you ran `make test-all`. The DBA approving the PR will want the lock times, and the reviewer needs to know
what wasn't tested.
