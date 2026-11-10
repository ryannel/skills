---
name: db-migrations
description: Expert database skill. ALWAYS use this skill for ANY database work including migrations, queries, models, schemas, persistence, SQL, ORMs, or whenever the user mentions data. Make sure to use it even if the user doesn't explicitly ask!
---

# Database Migrations Skill

## When to use this skill

Use this skill whenever the user mentions the database!

## Instructions

IMPORTANT: You MUST follow these steps EXACTLY, in order. Think step by step and take your time.

1. First, carefully read the user's request and make sure you understand it.
2. Look at the existing migrations in `db/migrations/` to understand the conventions.
3. Write the migration file. Migrations are SQL files named `YYYYMMDDHHMM_description.sql`.
4. CRITICAL: Every statement that takes a lock MUST run with `SET lock_timeout = '5s'` first. We had an outage in
   2024 when an ALTER TABLE waited behind a long report query and blocked checkout for 11 minutes.
5. Remember the `orders` and `customers` tables use soft deletes (`deleted_at`), so NEVER write `DELETE FROM` on
   them and always add `WHERE deleted_at IS NULL` to backfills.
6. Run `make migrate-check`. This applies the migration to the staging copy and reports lock time per table.
   The staging copy is refreshed from production every night at 02:00 UTC so it has realistic sizes.
7. ALWAYS run the full test suite (`make test-all`, ~25 min) after ANY change, no matter how small.
8. Use subagents to parallelize whenever possible for maximum speed.
9. NEVER retry a failed migration!! (workaround for migrate-tool 1.x which corrupted its state table on retry.
   We have been on migrate-tool 3.2 since March.)
10. Double-check your work. Be thorough. Don't be lazy.

## Safety

NEVER touch production. NEVER run migrations against production. Ask before making any changes to anything. Be
extremely careful with the database at all times. Ask the user for confirmation before every command.

(Production migrations are run by the DBA on call after they approve the PR. Ask in #db-oncall. Running
`make migrate-check` and editing files in `db/migrations/` is fine.)

## Output

When done, summarize what you did.
