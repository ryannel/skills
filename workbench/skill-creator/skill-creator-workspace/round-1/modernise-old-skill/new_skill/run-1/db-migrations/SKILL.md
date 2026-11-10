---
name: db-migrations
description: Writes and checks SQL migrations in db/migrations/ for this repository. Use when adding or changing a migration, changing the schema (a table, column, index or constraint) or backfilling data, or when asked to run a migration in production.
---

# Database migrations

This skill covers writing a migration for this repository and checking it before review. The aim is that no
migration blocks live traffic. In 2024 an `ALTER TABLE` waited for a lock behind a long report query, and
checkout was blocked for 11 minutes.

A migration is finished when its file is in `db/migrations/`, `make migrate-check` has passed on the final
version of that file, and you have given the person the lock time it reported for each table. Give the numbers
as the command printed them.

## Writing the migration

A migration is a SQL file in `db/migrations/`, named `YYYYMMDDHHMM_description.sql`.

Put `SET lock_timeout = '5s'` in the migration before any statement that takes a lock, so that it is in effect
for each of them. With it, a statement that can't get its lock fails after five seconds. Without it, the
statement waits, and every later query on that table queues behind it. That is what caused the 2024 outage.

The `orders` and `customers` tables mark a deleted row by setting `deleted_at`. They don't remove the row. So a
migration doesn't use `DELETE FROM` on either table, and a backfill on either includes
`WHERE deleted_at IS NULL`, which leaves the deleted rows as they were.

## Checking it

Run `make migrate-check`. It applies the migration to the staging copy of the database and reports the lock
time for each table. The staging copy is refreshed from production every night at 02:00 UTC, so its tables are
close to production size and the lock times are realistic.

If the check fails on the migration itself, with a SQL error or a lock timeout, fix the migration and run the
check again without asking. Running it again after a failure is safe on migrate-tool 3.2, which the project
uses. If the check fails because the staging copy can't be reached, tell the person. Don't point the check at
another database.

`make test-all` runs the full test suite and takes about 25 minutes. Run it once, when the migration is
otherwise finished, if the migration could break code that already works: it drops or renames a table or
column, changes a column's type, or adds a constraint that existing code might not satisfy. Also run it when the
person asks for it. A change that can't break existing code doesn't need it: a new table, a new nullable column,
a new non-unique index, a reworded comment.

## Production

Don't run a migration, or anything else, against the production database. The DBA on call runs each production
migration after approving its pull request. When the task needs a migration run in production, tell the person
to ask in `#db-oncall`.

Reading the schema, writing and editing files in `db/migrations/`, and running `make migrate-check` or
`make test-all` need no go-ahead. The check changes only the staging copy.
