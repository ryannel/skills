# AGENTS.md

This is the Parcel tracking service, a TypeScript monorepo (Express, zod, Kysely, pino; Vitest and Playwright for tests).

## What you can do without asking

Read anything, edit files in the working tree, and run `make check` and `make codegen` whenever you need to. Do the task, then report what you changed. Don't stop to ask permission for these.

Stop and ask first only when:

- the action reaches outside the local checkout (the staging stack, a shared database, anything in production);
- the action is destructive or hard to undo (deleting data, rewriting git history);
- the request is ambiguous in a way that changes what you would build.

## Testing

| Command | What it is | When to run it |
| --- | --- | --- |
| `make check` | Lint and unit tests. About 40 seconds, no network, in-memory database. | After every change, without asking. Fix failures before you report the work as done. |
| `make e2e` | The full Playwright suite. About 25 minutes, and it needs the staging stack. | Only when the person asks for it, or when you changed files in `tests/e2e/`. Otherwise do not run it. |
| Integration tests | Need `INTEGRATION_DB_URL`, which is not in the repo. | Only if the variable is already set. If it is not, skip them. Don't search for the value or make one up; people get it from #parcel-dev. |

When you changed files in `tests/e2e/`, prefer running only the spec files you touched over the whole suite.

In your final message, say which of these you ran and which you skipped, so the person knows what is still unverified.

## Limits

- **Don't hand-edit `src/gen/`.** It is the generated API client. `make codegen` rebuilds it from `api/schema.yaml`, so a hand edit is overwritten on the next run and leaves the client out of step with the schema in the meantime. To change the client, edit `api/schema.yaml`, run `make codegen`, and include the regenerated files in your change. If the generated output looks wrong, report it as a schema or generator problem; don't patch the output.
- **Don't deploy.** Deploys go through Priya, who owns the release calendar. If a task seems to need a deploy, stop and say so.
- **Flag any change to `migrations/`.** A migration can't be rolled back once it has been applied to production, so each one needs a second human reviewer. Write the migration if the task calls for one, and say at the top of your summary and in the PR description that it needs that second review.

## Conventions

- Handlers validate input with zod before touching the database.
- Use 2-space indentation.

## Layout

- `src/api/handlers/` holds the HTTP handlers, one file per route.
- `src/core/` holds business logic.
- `src/db/` holds database access.
- `src/jobs/` holds background jobs.
- `src/gen/` holds the generated API client (see Limits).
- `api/schema.yaml` is the source for `src/gen/`.
- `migrations/` holds SQL migrations (see Limits).
- `tests/unit/` and `tests/e2e/` hold the tests.

## Docs

Read these when the task touches their subject. You don't need them for small, local changes.

- `docs/architecture.md`: before a change that crosses module boundaries.
- `docs/database.md`: before changing `src/db/` or `migrations/`.
- `docs/deploy.md`: background only, since agents don't deploy.
