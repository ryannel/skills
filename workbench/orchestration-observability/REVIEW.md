# Design review of the prototype, 24 November 2026

Three Opus reviewers (medium effort) looked at the prototype through 71 screenshots in `review-shots/` and the running page: one on visual design, one on information design (does each screen answer the questions in ACTIVITIES.md), one on interaction and accessibility, who measured contrast and drove the page with Playwright. Their findings, merged and ranked. Where two or three reviewers found the same thing, it is one entry, marked with who found it: **V** visual, **I** information, **A** accessibility.

## Fix first

**1. Connect what's blocked to what it holds up.** (I)
APPLE-PRESENTATION:WP7 is blocked on you and is the head of the remaining chain for both G4 and G7; SHOWCASE, SWARM and MESH-SHADING wait behind it. The page never says so. Each Needs you card gets a "Holds:" line (the milestones and how many work packages wait behind it, followed forward through `needed_by`), and the cards sort by it. Each dependency row says what it waits on ("on APPLE-PRESENTATION:WP11, held by WP7, which needs you").

**2. Status colours mean status and nothing else, and each status has a shape too.** (V, A)
Links, the accent, the "New" badge, the chain outline and the pace pass-rate all reuse the Building blue or Ready for Review purple, so colour stops meaning status. Several statuses are also nearly identical: Blocked and Failed measure 1.01:1 against each other, Done and Ready to build 1.03 to 1.11:1, Building and Reviewing are the same blue, Waiting and Not started differ only by a faint fill. Keep the status hues for status only; links and accent take a neutral. Give each status a glyph as well as a colour (Done ✓, Building ●, Reviewing ◐, Ready for Review ◆, Ready to build ▷, Waiting ⏸, Blocked !, Failed ✕, Not started as a dashed outline), in chips and the legend. WCAG 1.4.1.

**3. Done is the quietest state, not the loudest.** (V)
Three quarters of the chips are filled green at full strength, so the one amber or purple chip is hard to find. Draw Done as a muted outline or low-contrast fill, and keep solid fills for the states that need attention.

**4. What a chip means is visible without hovering.** (A, V, I)
Every chip shows only its id; its name and status live in a `title` tooltip that touch, keyboard and magnifier users never see. All 92 board titles are truncated on the phone. Show the name next to the chip wherever there's room (Needs you, Waiting, Running now, chain lists); let board titles wrap to two lines with the title as the main text and the module small and muted; replace `title` with a popover that opens on hover and focus and closes with Esc, holding name, status, what it waits on and since when, module, milestone, and depends-on and needed-by counts. On the map, the first tap or Enter selects a chip and draws its links; the popover's link opens the page. WCAG 1.4.13, 2.1.1.

**5. Live updates keep your place and say what changed.** (A)
Every re-render replaces the page: focus falls to the body and open disclosures close, which the real `serve` will do every few seconds while agents run. Update in place, or restore focus and open state by id; don't re-render under a focused panel, show "Updated, show changes" instead; announce a one-line summary in a polite `role="status"`; give the live dot words ("Live", "Disconnected, last update 17:06"). WCAG 2.4.3, 4.1.3.

**6. The plan map shows the whole plan and the next milestone by default.** (V, I, A)
It sits in a fixed-height box showing 13 of 36 modules, draws no links until a hover, its 1px lines and 35%-dimmed chips fail contrast (1.6 to 2.5:1), and focus is invisible on the chain chips because the chain outline overrides the focus ring. Show it at full height; open it on the next open milestone (the G4 view is the page's best view); dim outside chips by switching to the outline style with muted text, not opacity; draw links at 1.5 to 2px in a colour that reaches 3:1, routed in the gutters; draw the chain as a solid ink line; move the legend to the top; note that lanes follow plan order. Make the map one tab stop with arrow keys inside it and a skip link past it. Drop the duplicate chip strips from the Modules table. WCAG 1.4.3, 1.4.11, 2.4.7.

## Now

**7. Now leads with what needs action.** (V, I)
Needs you goes first and full width. Closed milestones fold into one line ("5 closed · last G3s, 23 Nov", linking to Retro); open milestones show their remaining chain inline as chips, marking what the first one waits on. The state strip and the amber banner merge into one line ("Paused · 0/10 builders · 0 reviews · nothing merged for 10h 26m · supervisor stopped"). An empty Running now folds into that line.

**8. "Since you last looked" opens with a count and puts status first.** (I, V)
One line first ("Since 23 Nov 17:38: 17 done, 6 ready for review, 1 blocked, 2 review failures, 4 plan changes"), then status events, with bulk tooling commits folded into one line. Rows on a fixed grid: kind, text, time right-aligned in tabular figures.

**9. One word for "not moving".** (I)
Now's Waiting panel is every stalled work package grouped by reason; the board's Waiting column is one status. Rename the Now panel "Not moving"; give board cards in Waiting and Blocked a small reason tag; one plain label for "no reason recorded" on both.

**10. Milestones say when they'll close.** (I)
Each open milestone row gets "expected around …" from its remaining chain and recent pace, or "held by you" when its chain is blocked on you.

## Plan

**11. About the project is enough to start from cold.** (I)
The V1 exit sentence, the milestone ladder G0 to G7 with closed and open marked, where things stand in one sentence, and the vision and scope document's still-open decisions.

**12. Plan changes lists only plan changes.** (I)
Show commits that changed definitions or the design, vision or architecture files, led by the changed work packages as chips; everything else behind an "all commits" toggle.

**13. Choices made for you lead with what's new.** (I, V)
A flat "New since you last looked" list across modules first, each with its module; the rest newest first within each module, in a compact layout.

## Work package and module pages

**14. The work package page summarises its proof at the top.** (I, V)
A small grid of items against reviews (a pass or fail cell each, clicking jumps to the item) with "15/15 passed · 2 reviews · 1 failed"; verdict dots beside the item id and larger, with a red rule on items whose last verdict failed; statements collapsed to their first line; the reviewer question in a smaller tinted block; evidence paths shown relative to the work package folder; the milestones whose chain it's on in the header; the title wider. One item id format everywhere.

**15. The module page's table says why.** (I)
Status plus reason ("Waiting · on WATERS:WP8"); drop all-empty columns; waiting-on modules as the exact work packages.

## Delivery, Machinery and Retro

**16. Board columns earn their width.** (V)
Empty columns collapse to a narrow header; one column of cards per status on the phone.

**17. Pace is two small charts with axes.** (I, A)
Done per day with a seven-day average, and pass rate as a 0 to 100% line. The chart gets `role="img"` and a one-sentence summary, the daily counts table stays as the fallback.

**18. Warnings are plain sentences.** (I)
One line per work package with its chip, no internal names ("next try uses a fresh builder", not "same_builder"), duplicates merged, and the same line in that work package's header.

**19. Machinery diagnoses rather than lists.** (V, I)
Slow checks as the top ten by time against usual ("3.7× usual"), with a short name, the module, and the full command on expand; machine load as a 24-hour trend with only agent processes named; every count with its time window and a one-line definition; unpriced cost rows behind a disclosure; errors linked to their sessions.

**20. Cost shows what it covers.** (I)
Tokens or sessions as the main measure, known for every host; dollars only where priced, with coverage next to each figure; the weekly limit as used against projected up to the reset.

**21. Retro is a table.** (V, I)
A row per milestone: closed, duration, cost with coverage, planned and added, failed reviews, design reviews asking for changes, failed reviews by kind of task and host. The basis for "planned" stated once. Cards become drill-downs.

## Keyboard, screen readers and the phone

**22. Navigation moves focus and keeps your place.** (A)
A skip link; focus to the `h1` after each route change; Back and Forward restore scroll and focus; in-page jumps move focus to the target. WCAG 2.4.1, 2.4.3.

**23. Names and roles that screen readers drop.** (A)
`role="region"` on the map, board and timeline scrollers; board cards keep their visible duration and announce their status; the timeline is one tab stop with arrow keys and a list view; the file dialog gets `aria-labelledby`; the legend is a list. WCAG 4.1.2, 1.3.1, 1.1.1.

**24. The phone and zoom.** (A, V)
`scroll-padding-bottom` so the bottom bar doesn't hide focused items; the header scrolls away on short screens; the More menu closes on Esc and outside taps; chips and summaries at least 32px tall with 8px gaps; the plan map reachable at narrow widths (a desktop at 200% zoom loses it today). On the phone, Modules is one line per module, Choices and Plan changes start collapsed, and Now shows only open milestones.

**25. Small consistency fixes.** (V)
Module and work package pages highlight the Plan tab; an extra type step for group heads (about 13px semibold muted); chip text at weight 600; module names in small caps rather than heavy capitals in prose; work package titles in ink, not link blue.

## Keep

All three named these as working: the work package chip as the one unit across every screen; Needs you with the builder's own question; the one-reason grouping of stalled work; the G4 milestone view of the plan map; review cards with findings tied to items and an honest "Generated" label; light mode; the calm panel structure; text contrast (5.4 to 7.5:1 everywhere outside the map), the focus ring, reduced motion, reflow at 320px, heading and landmark structure, and a URL for every page.
