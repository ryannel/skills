# Parcel tracking service

## Checking a change

- `make check` runs the linter and the unit tests. It takes about 40 seconds, uses an in-memory database and
  never touches the network. Run it, fix what your change broke and run it again, all without asking. A change
  is ready when it passes.
- `make e2e` runs the Playwright suite. It takes about 25 minutes and needs the staging stack, so it is not part
  of checking an ordinary change. Run it when your change alters a flow that a test in `tests/e2e/` covers, or
  when the person asks. Otherwise say in your summary that you left it out.
- The integration tests need `INTEGRATION_DB_URL`. The value is not in the repository; the team shares it in
  #parcel-dev. If it isn't set, skip those tests and say so in your summary.

## Generated code

`make codegen` writes `src/gen/` from `api/schema.yaml`, and the next run overwrites any hand edit there. To
change something in `src/gen/`, edit `api/schema.yaml` and run `make codegen`. If the schema is right and the
output is still wrong, tell the person and leave the output as it is.

## What involves a person

Reading files, editing hand-written code and running `make check` or `make codegen` need no approval.

- Leave deploys to Priya, who owns the release calendar. When the work needs one, finish the change and tell the
  person it is ready for her.
- A change in `migrations/` needs a second human reviewer before it merges, because a migration can't be rolled
  back once it is applied to production. Write the migration when the task calls for one, and say in your
  summary that it needs the second review.

## Conventions

A handler validates its input with zod before it touches the database.

## Documents

- `docs/architecture.md`: how the parts of the service fit together.
- `docs/database.md`: read it before you change the schema or the database access code.
- `docs/deploy.md`: how a release happens.
