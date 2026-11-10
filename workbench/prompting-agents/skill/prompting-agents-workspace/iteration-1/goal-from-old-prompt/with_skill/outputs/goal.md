Goal: the invoice PDF export in `services/billing/pdf/` is finished as `docs/invoice-pdf.md` describes it, and
`TAX_API_STUB=1 make test-pdf` passes against the golden files as they are now.

I am starting this run before I go to sleep, and I will read the result in the morning. Nobody will answer a
question during the run, so a question to me stops the work until then. Where the design leaves a choice open,
take the option that fits `docs/invoice-pdf.md` best, write the choice and your reason in the notes file described
below, and carry on. Do all the work you are allowed to do before you stop, so that what I review in the morning
is a finished branch.

## Where the work stands

The renderer is half built. Line items render. I know of two gaps:

- The totals rows and the tax rows don't render.
- An invoice longer than one page is cut off after page 1.

There may be other gaps between the code and the design. Closing them is part of this work.

## What done means

`make test-pdf` renders invoices and compares each one, pixel by pixel, with the golden files in
`tests/golden/invoices/*.pdf`. The golden files define correct output. You are done when all of these are true:

- The totals rows and the tax rows render as the design describes.
- A multi-page invoice renders every one of its pages.
- `TAX_API_STUB=1 make test-pdf` exits 0, with the golden files and the settings of the comparison unchanged.

A version that fails the comparison is not finished. Run the check, look at what differs, fix it, and repeat until
the check passes.

Where a golden file and the design disagree, match the golden file and record the difference in the notes file.
If no golden file covers a multi-page invoice, or none covers an invoice with tax, then a passing `make test-pdf`
doesn't show that those two gaps are closed. In that case show it another way, and say in the notes file which
case has no golden file.

## What to leave alone

Don't edit anything under `services/billing/ledger`. Dana's team is partway through a migration there, and a
change from outside would collide with theirs. You may read it. If finishing the export seems to need a change
there, write the change you would make and the reason in the notes file, and finish everything that doesn't
depend on it.

Don't call the real tax API, because it charges for each call. Setting `TAX_API_STUB=1` makes the code use a stub
in its place, so set it on every command that could reach tax code. If the stub doesn't return something an
invoice needs, record that in the notes file and leave the stub switched on.

Commit your work to a new local branch named `invoice-pdf-export`. Don't push the branch or open a pull request.
My review of that branch in the morning is the approval step.

These need no approval: reading any file, editing code and tests in `services/billing/pdf/`, running
`make test-pdf` and other local commands with `TAX_API_STUB=1` set, and committing to the branch. If the export
needs a change outside `services/billing/pdf/` that is not in the ledger folder, make it and list it in the notes
file with the reason.

## When something gets in the way

There are two kinds of obstacle. An error, a failing test, a command that times out or a pixel difference you
can't yet explain is an ordinary one, and it is yours to work through. Something protected on purpose (the ledger
folder, the real tax API, the golden files, access you were not given) is to be left alone and recorded.

A part of the work is blocked when it can only be finished by crossing one of those lines: for example, the fix
needs an edit under `services/billing/ledger`, or the stub lacks data that only the real tax API has. When one
part is blocked, record it in the notes file with what would unblock it, and carry on with the rest.

## The notes file

Keep `notes/invoice-pdf-export.md` up to date as you work. Create it if it doesn't exist. It holds what is
finished, what you are working on, each choice you made with its reason, and anything blocked. The run may
outlast your context, and this file is what you read to pick the work up again.

## What I want back

When the work is done, or everything left is blocked, write one final message. Put first whether
`TAX_API_STUB=1 make test-pdf` passes, with the command and the end of its output. After that say what you
changed, what is blocked, and which choices you want me to look at. Keep what you confirmed by running something
apart from what you only suspect.
