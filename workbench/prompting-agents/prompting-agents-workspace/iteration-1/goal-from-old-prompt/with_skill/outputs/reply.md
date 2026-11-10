The new goal is in `goal.md`. I wrote it fresh instead of editing the CSV prompt, and I have not started the Codex session.

**Why it stopped last time.** The old prompt told it to: "NEVER modify anything without asking first", "ALWAYS ask before running any command that could have side effects" and "If you are unsure about ANYTHING, stop and ask". GPT-6 Astra takes that wording at full strength, and it already leans towards asking. The new goal says nobody will answer until morning, names what needs no approval, and makes your morning review of the branch the only approval step.

**What I kept from the old prompt.** Only the rule about `services/billing/ledger`, now with the reason (Dana's team is mid-migration).

**What I dropped.**
- The numbered steps, the "read all of docs/" order and the "expert engineer" line. The model plans this better itself.
- The capitals and "don't be lazy".
- `make test-all` after every change. The check is now `make test-pdf`.
- The seven-section report. It now asks for the test result first, then changes, blocked items and choices to review.

**What I added from your context.** The two known gaps, the design doc, the golden files as the definition of done, the tax stub, and a notes file so the run survives losing its context.

**Decisions I made for you. Change any that are wrong.**
- It may read the ledger folder but not edit it.
- It commits to a local branch `invoice-pdf-export` and does not push or open a pull request.
- It keeps progress in `notes/invoice-pdf-export.md`.
- It may make a needed change outside `services/billing/pdf/` (never in the ledger folder) and must list it in the notes.
- Where a golden file and `docs/invoice-pdf.md` disagree, it matches the golden file and records the difference.
- It may not edit the golden files or loosen the pixel comparison.

**Three things to check before you go to bed.**
1. Do the golden files include a multi-page invoice and one with tax? If not, a passing `make test-pdf` doesn't prove those two fixes. The goal tells it to say so, but adding the golden files first is better.
2. The tax API rule is only words in a prompt. If it has to hold every time, export `TAX_API_STUB=1` in the shell that starts Codex, or leave the real API key out of that environment.
3. Check that Codex's approval mode lets it edit files and run `make test-pdf` without prompting, and that the repo's `AGENTS.md` and any skills it can reach have no "ask first" lines. Either one will stall it the same way, whatever the goal says.

**Starting it.** Pick GPT-6 Astra and the effort level in Codex when you start the session, not in the goal text. Use the effort level you used for the CSV run. Then give it the contents of `goal.md` with `/goal`.
