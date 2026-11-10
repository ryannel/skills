---
type: llm
focus: trace
---

PASS if the run created exactly one new file in db/migrations/ named YYYYMMDDHHMM_description.sql (twelve
digits, an underscore, a description) and that file adds a nullable text column gift_note to orders.
FAIL if no such file was created, the name has another shape, or the column is missing or NOT NULL.
