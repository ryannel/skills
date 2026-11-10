---
tags: [prompting-agents]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

ok I want to kick off a codex session overnight on gpt-6 astra to finish the invoice pdf export. here's the prompt I used last month for the csv export (old-prompt.md), can you update it for this?

context: the pdf renderer is in services/billing/pdf/. it's half done, line items render but the totals + tax rows don't, and multi-page invoices get cut off after page 1. the design is docs/invoice-pdf.md. golden files are tests/golden/invoices/*.pdf and `make test-pdf` compares against them (pixel diff). don't let it touch services/billing/ledger, Dana's team is mid-migration there. it can't hit the real tax API (costs money per call), there's a stub, TAX_API_STUB=1. last time the agent stopped after about an hour and asked me if it should continue, and I was asleep.

write the new one to goal.md

Input files: old-prompt.md
