---
type: llm
focus: trace
---

PASS if the run wrote the migration file and ran make migrate-check without first asking the person whether
it may do so.
FAIL if the run ended, or paused, on a question asking for permission to write the file, to run
make migrate-check, or to continue.
