I wrote the new prompt to `goal.md`. It is a rewrite, not an edit, because the old prompt's own rules are the likely cause of the agent stopping after an hour.

**Check the Codex approval setting before you go to bed.** The prompt cannot stop Codex from pausing on a permission prompt. If the session asks for approval before running commands, it will stall at the first `make test-pdf` whatever the goal says.

## What I changed from the old prompt

- **Asking:** the old prompt said "NEVER modify anything without asking first" and "if you are unsure about ANYTHING, stop and ask". The new one says nobody is awake, so it should decide, record the decision and carry on.
- **Finish line:** done is now `TAX_API_STUB=1 make test-pdf` passing, `make test-all` passing once at the end, and work committed locally.
- **Current state:** it says line items work, totals and tax rows don't render, and multi-page invoices are cut off after page 1.
- **Golden files:** it may not edit or regenerate them, loosen the pixel diff or skip tests. Otherwise the easiest way to make a pixel-diff test pass is to change the test.
- **Ledger:** no changes under `services/billing/ledger`, with the reason. If a fix seems to need one, it describes the change in the report instead of making it.
- **Tax API:** `TAX_API_STUB=1` on every command that runs billing code, with the reason (cost per call).
- **Dropped:** the persona line, the capitals, "read all of docs/ and every file in services/billing/", `make test-all` after every change, and the seven-section report. The report is now four short items, including the decisions it made without you.

## Assumptions to check

- **No push:** I told it to commit locally and not push or open a pull request. Change that line if you want a branch pushed.
- **Reading the ledger:** I allowed it to read `services/billing/ledger` but not change it. Tighten that if "don't touch" meant don't read either.
- **Golden files win:** if a golden file disagrees with `docs/invoice-pdf.md`, it matches the golden file and notes it.
- **`make test-all` with the stub:** I assumed this target is safe to run with `TAX_API_STUB=1`. If it reaches the real tax API some other way, remove that line.
