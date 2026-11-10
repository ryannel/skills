---
type: llm
focus: trace
---

PASS if the migration file as last written contains SET lock_timeout = '5s' before the ALTER TABLE statement.
FAIL if the line is missing, comes after the ALTER TABLE, or sets another value.
