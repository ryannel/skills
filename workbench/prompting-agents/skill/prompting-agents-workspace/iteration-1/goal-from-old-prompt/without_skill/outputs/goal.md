# Goal: finish the invoice PDF export

Finish the invoice PDF renderer in `services/billing/pdf/` so that `TAX_API_STUB=1 make test-pdf` passes.

You are running overnight and unattended. Nobody will read a question until morning, so a question costs the whole night. Do not stop to ask whether to continue or to confirm a choice. When something is unclear, pick the option that best fits the design doc and the golden files, write down what you chose and why, and keep going.

## Where things stand

The renderer is half built. Line items render correctly. Two things are broken:

- The totals rows and the tax rows do not render.
- Invoices longer than one page are cut off after page 1.

The design is in `docs/invoice-pdf.md`. Read it and the existing code in `services/billing/pdf/` before changing anything, because the remaining work should follow the patterns the working line-item code already uses.

## What done means

- `TAX_API_STUB=1 make test-pdf` passes. This target renders invoices and compares them pixel by pixel against the golden files in `tests/golden/invoices/*.pdf`.
- `TAX_API_STUB=1 make test-all` still passes, run once at the end, so you know nothing else in the repository broke.
- Your work is committed locally. Do not push, open a pull request or deploy.

Getting totals working is not a stopping point, and neither is getting pagination working. Carry on until all of it is done or you have hit one of the blockers described below.

## Limits

**Do not change anything under `services/billing/ledger`.** Another team is partway through a migration there and any edit will collide with their work. You may read it to see what data the renderer receives. If the only correct fix seems to need a ledger change, do not make it. Describe the change you would have wanted in your report and do the best you can from the PDF side.

**Never call the real tax API.** It charges money per call. Set `TAX_API_STUB=1` on every command that runs billing code, including one-off scripts and single tests, not only the two make targets. If something seems to need the real API, treat that as a blocker.

**The golden files define correct output.** Do not edit, regenerate, replace or delete anything in `tests/golden/invoices/`, and do not loosen the diff tolerance, skip tests or change how the comparison works. If a golden file seems to disagree with the design doc, match the golden file and note the disagreement in your report.

Keep your changes inside `services/billing/pdf/` and its tests where you can. A small change elsewhere in `services/billing/` (outside the ledger) is fine if the fix needs it. List any such change in your report.

## If you get stuck

- If one part is blocked, finish the other parts first. Come back to the blocked part afterwards with a different approach.
- If a pixel diff still fails after the layout looks right, check whether the cause is the environment (fonts, antialiasing, the PDF library version) before changing more code. If it is, say so in the report with the evidence. Do not tune the code to chase it.
- Stop early only when everything left needs a ledger change, the real tax API, or a change to the golden files or the comparison. Then commit what works and write the report.

## Report

Finish with a short report in your final message that I can read in a few minutes:

- Whether `make test-pdf` and `make test-all` pass. Give the failing cases if not.
- What you changed, in a few lines.
- The decisions you made where you would otherwise have asked me.
- Anything you left undone or worked around, and why.
