# Design review and polish, 26 Nov 2026

Two reviewers looked at the observability prototype from full-page and per-panel screenshots plus the code: Fable 5.2 ([fable.md](fable.md)) and Gemini 4 Neon on Antigravity ([neon.md](neon.md)). They agreed on almost every major problem without seeing each other's report. The merged list is [FIXES.md](FIXES.md). Everything on it is done, apart from the three items under "Not taken" at the end.

To look at it, open `http://127.0.0.1:8771/prototype/index.html` (the preview server in `.claude/launch.json`). Compare the screenshots in `before/` and `after/`: `pages/` holds whole pages at desktop and phone width, and `panels/` holds the panels up close. `after/pages/now-desktop-light.png` and `plan-desktop-light.png` show light mode.

## What changed

**The numbers are right now.** Ages were measured against a clock two days older than the snapshot, so everything read "<1m" and "Done today" read 61. Everything now uses the snapshot's own time. "Since you last looked" was always empty for the same reason, and now shows the last day.

**Late reads as late.** A milestone past its estimate now says "Overdue · expected 24 Nov" in amber on Now, the goal header and the milestone page. The Codex tile says when usage is on course for more than 100% before the reset.

**Now answers its question faster.** The Next milestone tile reads "2 left", with the name underneath. Each milestone says "Next up:" with the work package's name and why it waits, in place of "First waits on No reason recorded". The Ready for review tile jumps to the review group. The state line wraps cleanly on phones.

**The program board opens cleanly.** It opens on "From here on", scrolled so the next milestone starts at the edge of the module column. The module column has a visible edge. The next milestone has a solid "Next" tag that doesn't pulse. Long done lists fold. On phones it becomes a list per milestone, folded after five.

**Detail pages lead with what matters.**
- Names come first, with the reference after them.
- The module page has a progress bar in its header, and its work packages come first, in build order.
- The milestone page lists the work left by name.
- The work package page drops the empty dependency panels.
- Item statements no longer break up around inline code.

**Colour means one thing.** Amber is kept for blocked, needs you and overdue. The tokens chart uses distinct colours. Only the worst error bar is red. Failed-review counts on finished work are muted. The pace chart uses ink, not the "ready for review" purple. Waiting and not-started tags look different from each other.

**Words a newcomer can read.**
- "Program board" instead of "Plan map".
- "1 decision waiting", not "1 decisions".
- Retro lists only closed milestones, newest first, each linked to its milestone page. Its costs read "at least $30 · 6 of 139 sessions priced".
- "Design changes" is renamed "Failed design reviews".
- Slow checks are named as package · test, not "it" or "$(rustup which".
- Warnings on finished work fold away under "4 on work that has since finished".

**Smaller things.**
- Links you can click look like links.
- Numbers in tables are right-aligned.
- Panel titles are larger.
- Light-mode faint text passes contrast.
- Long ladder labels hyphenate instead of touching.
- On phones, tables hide "—" cells and work package names wrap.

[SCREENS.md](../SCREENS.md) is updated to match.

## Names first (27 Nov, after your go-ahead)

Modules and work packages now lead with their names everywhere, with codes only as small references; screenshots are in `names/`.
- **Module names** come from the title of each module's design. For example, `RAY-TRACING` is "Ray tracing", `APPLE-PRESENTATION` is "Reconstruction, display and quality governor", and `GAME-UI` is "Game UI". `build_model.py` writes them to `model.json` as `name`.
- **Work packages** show their name, then a small status tag with the short reference (WP14).
- **Waiting reasons** say what is waited on by name, as in On "Apple tile with MetalFX and EDR is compared…", where they used to say "On APPLE-PRESENTATION:WP11".

Two other changes came with this:
- The model was rebuilt from today's Thrum data. Apple reconstruction has closed, so V1 showcase is now the next milestone.
- Thrum has started numbering some work packages `U1` and `U2`, which the builder used to drop. It now reads them.

Some names are long, because the designs' titles are: "Reconstruction, display and quality governor" and "Atmosphere for the V1 outdoor scene". A short `name:` line in each module's design or plan, written by the planner, would be the lasting fix.

## Not done, and why

- **Regrouping Machinery into sections** (Fable). It's 17 panels of equal weight. Regrouping them is a redesign rather than a polish pass, so it's worth deciding what Machinery is for first.
- **Trimming excerpts on word boundaries** (Neon). That's a `build_model.py` change, and it's noted for later.

## Still true of the data

These come from Thrum and aren't UI problems: 187 of 242 work packages are tied to no milestone; the first four milestones closed before milestones recorded their work; Apple reconstruction and V1 showcase are both past their estimates.

Nothing is committed. The workbench folders are still untracked.
