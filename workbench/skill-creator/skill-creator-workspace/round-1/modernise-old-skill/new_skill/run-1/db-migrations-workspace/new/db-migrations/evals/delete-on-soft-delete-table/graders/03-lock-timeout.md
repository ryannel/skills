---
type: llm
focus: trace
---

PASS if the migration file as last written contains SET lock_timeout = '5s' before the statement that changes
customers.
FAIL if the line is missing, comes after that statement, or sets another value.
