# Fable 5.2 design review, 26 Nov 2026

Reviewed from the screenshots in `before/`, `prototype/index.html`, `model.json` and the live page at 1440 px and 375 px, dark and light. Not checked: chip popover, board dependency lines, keyboard navigation, Timeline, Builder runs, open Choices and Plan changes. Note: `panels/plan--modules.png` is a crop of the board, and `pages/plan-desktop.png` stops inside the board.

## The five changes first

1. **Fix the clock every age is measured against.** Ages use `project.snapshot_at` (24 Nov 15:53Z) while the header shows `built_at` (26 Nov), so "last merge <1m", "<1m" ages, "11h 20m" on a two-day block and "Done today 61" are all wrong.
2. **Make Now state the answer in words.** Milestones show a past expected date with no "overdue", and "First waits on No reason recorded".
3. **Fix the work package Items panel.** Statements break into clipped lines with code cut at the left ("IPELINE_CACHE").
4. **Make the program board open cleanly and stay small.** It opens with a column half under the sticky module column, the wide column has tall empty cards, and Whole plan is a 6,400 px scroll in a 700 px box. Default to From here on.
5. **Give the phone its own summary for Plan, Machinery and Retro.** The board is unusable at 390 px, Machinery is 7,400 px of label-value rows, and the module page clips names off the right edge.

## Findings

1. **Wrong clock** (all pages). Line 1927 uses `snapshot_at || built_at`; `elapsed()` clamps negatives to zero so anything after 24 Nov shows "<1m". Fix: one clock (`built_at`), say "History up to 24 Nov" where history is older, show "—" for negative ages. Confirmed in code and data.
2. **Now doesn't say late or stuck.** No overdue branch at lines 683 and 1345 (Plan has it at 1035). "First waits on No reason recorded" reads broken. The Next milestone tile holds a two-line name where others hold numbers. Fix: reuse the overdue logic with an amber pill; "WP12 is waiting, no reason recorded"; tile "2 left" with the name as the note.
3. **Item statements break up** (work package Items). Line 457 nowrap plus line 52 `code{white-space:pre-wrap; overflow-wrap:anywhere}`. Fix: clamp the closed summary to two lines with `white-space:normal`, `code{white-space:normal}`, `summary{align-items:flex-start}`.
4. **Board opens on a half-hidden column.** Line 948 scrolls to `offsetLeft-200-clientWidth*0.35`. Fix: snap to a column edge, or scroll-snap with `scroll-padding-left:200px`.
5. **Board too tall, empty boxes in the wide column.** Whole plan is 6,443 px in a 701 px scroller; `.pb-cell.wide` lacks `align-items:start`; done names cut at ~28 chars; the current column is a 6% tint; the ladder orders milestones by plan and the board by close date. Fix: default From here on; `align-items:start`; collapse done cards to "✓ 12 done" past three; stronger current column with a filled Next tag; one milestone order for both.
6. **Goal ladder has an open step in a done line.** Apple reconstruction is open but eighth of eleven; labels touch; on phones the current step is off screen. Fix: closed first, then open; `padding-right:16px`; scroll the current step into view or replace with a sentence on phones.
7. **Phone breaks on Plan board, Machinery, Retro and the module page.** Board shows a 30 px sliver; Machinery 7,385 px; Retro repeats "Duration · —"; `.wp-title` nowrap runs off the edge; "Built for a large screen" uses the amber notice style; tap targets 14–28 px; 11 px text. Fix: per-milestone list on phones; label/value grid rows hiding "—"; wrap `.wp-title`; neutral desktop note; 44 px rows; 12 px floor.
8. **Colour has several meanings.** Amber for Blocked, Needs you, desktop note, context warning, Stopped. Red on every error bar. Six opacities of one ink in Tokens per day. Waiting and Not started chips look alike; not-started segments equal the track. Red failed-review counts on done work. Fix: amber only for Blocked and Needs you; ink bars with red for the worst; distinct fills or "Other"; tinted Waiting; hatched not-started; muted historic counts.
9. **Words a newcomer can't read.** "Plan map →" (now Program board); "1 decisions"; "Ready for Review" capital; "chain" unexplained; "No active run in the saved output"; empty Depends on / Needed by panels; Delivery "Empty now" line; tags without the thing waited on; 40-word warnings led by a ✓ Done chip; Machinery jargon ("Weighted tokens", "Context at p90") and slow checks named "it"; Codex tile 37% hides "104% projected"; Retro "$30.31 · 6/139 priced" presented as the cost; open milestones listed under "Closed milestones"; disclosure chevron used as a bullet.
10. **Module and milestone pages are thin.** No progress bar on the module page; work package order unexplained; "0 / 6" items beside Done. Milestone page lists modules without open work. Plan Modules table says "Approved" 37 times and has no progress. Fix: bar and "x of y done" in both headers; remaining work by name on the milestone page; progress column in place of Design.
11. **Type and hierarchy.** Panel titles 15 px barely above body; Machinery has 17 equal panels; Now's "Paused" state is a muted pill. Fix: 17 px titles; Machinery grouped into sections with secondary panels folded; Now's state as a sentence under the title.
12. **Accessibility.** No table captions or header `scope`; `:focus-visible` changes radius; chips look like links only on hover; status glyphs ~9.7 px; late board cards marked by colour only.
13. **Smaller layout points.** Empty "Since you last looked" panel; tiles jumping to an empty anchor; Needs you repeats in Not moving; Delivery columns eight cards tall; Pace axis labels unreadable on phones; milestone page empty below; empty Proof summary panel.

## Keep

The Goal panel, the Needs you card, Not moving grouped by reason, the segmented milestone bar, Delivery board cards, the calm surface and light mode, status glyphs with colour, honest labels, the "Not tied to a milestone" column, and no horizontal page overflow at 375 px.
