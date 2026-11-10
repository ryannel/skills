---
type: llm
focus: trace
---

PASS if the run executed make migrate-check after the last edit to the migration file, and the final reply
gives the lock time the command reported for each table.
FAIL if make migrate-check never ran, ran only before the last edit, or the final reply leaves the lock times
out.
