# Merged fix list, 26 Nov 2026

From [fable.md](fable.md) (F) and [neon.md](neon.md) (N). Both reviews found the same top problems independently; where they differ, the fix taken is noted.

## Both reviewers

- Ages measured against a two-day-old clock, so "<1m" everywhere and "Done today 61" (F1, N2).
- Overdue milestones shown as calm forecasts on Now and the milestone page (F2, N5).
- Item statements garbled by inline code (F3, N1).
- Program board: half-hidden first column, no seam on the sticky column, unusable on phones (F4, F7, N4).
- Goal ladder: an open step inside the green line, labels touching, current step off screen on phones (F6, N8).
- "First waits on No reason recorded", "Plan map" label, "Ready for Review" capital (F2, F9, N11).
- Tokens chart shades indistinguishable; red on every error bar (F8, N13).
- Codex tile hides the projected overrun (F9, N12).
- Retro lists open milestones under "Closed milestones" and presents 4%-priced costs as the cost (F9, N14).
- Warnings on finished work packages read as current (F9, N10).
- Empty Depends on / Needed by / Proof summary panels push Items down (F9, F13, N17).
- "Needed by modules" uses disclosure chevrons as bullets (F9, N17).
- "Next" uses the pulsing Building tag; the ref sits above the name on detail pages (N16).
- Now's state pill wraps badly on phones; the Next milestone tile breaks the number row (F2, F11, N7).

## One reviewer

- Since you last looked is always empty on a snapshot (N3).
- Ready for review tile jumps to an empty panel (F13, N3).
- Links look like plain text (N6).
- Numbers left-aligned in tables (N9).
- Pace chart uses status purple and is unreadable on phones (F13, N15).
- Slow checks named "it"; empty Model column; machine-load chart text too large (F9, N13).
- Panel titles barely larger than body text (F11).
- Module page has no progress at the top; work package order looks random (F10).
- Milestone page lists modules without the work that is left (F10).
- Plan Modules table says "Approved" 37 times with no progress (F10).
- Phone: Machinery and Retro rows full of "—"; work package names run off the module page (F7).
- Light-mode faint text just under AA on subtle surfaces (N18).

## Not taken

- Names first for modules and work packages everywhere: both noted it; it is the agreed next step and needs your go-ahead on how module names are written.
- Redesigning Machinery into grouped sections (F11): a bigger change than a polish pass.
- Extractor trimming of excerpts on word boundaries (N18): a `build_model.py` change, noted for later.
