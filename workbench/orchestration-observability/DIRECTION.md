# Visual direction, 24 November 2026

The prototype now answers the right questions (REVIEW.md), but it reads as a wall of text: every work package appears as a chip plus its full one-sentence name, every list shows every row, every section is a bordered box, and every row is an underlined link. The result is dense, flat and dated. This pass changes how it looks and how much it shows at once, not what it knows.

The reference point is a current product dashboard such as Linear, Vercel or Raycast: calm neutral surfaces, few borders, generous space, one strong number per idea, and detail one hover or click away.

## Principles

**Summary first, detail on demand.** Each screen opens with the few facts that matter, as large numbers or short phrases. A list shows its first five rows and a "Show all 23" control. Full work package names appear on hover, focus or the detail page, not in every row. A row's main text is the shortest thing that identifies it; the sentence-long name is secondary, one line, truncated, muted.

**Whitespace separates, not borders.** Drop the box around every section. A section is a heading and its content, with 40 to 56px between sections. Cards are kept for things you act on or open (Needs you, board cards, milestones), with 12px corners, a hairline border in dark mode and a soft shadow in light mode.

**One type scale, used strictly.** System UI font (SF Pro on the Mac; no web font fetch), tabular figures for numbers. About five sizes: page title 28/600, section 17/600, body 14/400, secondary 13/400 muted, label 12/500 uppercase-free. Large stat numbers 28 to 32/600. Line height 1.5 for prose, 1.3 for UI. Most text is body or secondary; heavy weights are rare.

**An 8px grid.** Panel padding 20 to 24px, row height at least 40px, gaps in 8px steps. Content max width about 1280px, centred.

**Status as a quiet signal.** Most statuses become a small coloured dot or glyph beside text, not a filled pill. Filled tint is kept for states that need attention: Blocked, Failed, Needs you. Done is muted. Keep each status's glyph (REVIEW.md finding 2) and the measured contrast.

**Names first, IDs as a reference.** A milestone, module or work package is shown by its name. Its ID, such as `milestone/sky-and-atmosphere` or `WP7`, sits after the name in small muted monospace, and never takes the main place, because nobody who doesn't read the plans knows what an ID means.

**Rows, not links.** Rows highlight as a whole on hover and open on click; no underlines in lists. Underlines stay only for links inside prose.

**Progress you can read at a glance.** A milestone shows its progress as a segmented bar by status (done, in review, building, waiting, blocked, not started) with the count beside it, not only a done fraction.

## Per screen

- **Now** opens with a row of four or five stat tiles (needs you, ready for review, not moving, building, last merge) that jump to their lists. Then Needs you as roomy cards: the question as the main text, the work package and what it holds as one line below. Milestones as cards with the segmented bar and "held by you" or the expected date. "Since you last looked" as a compact feed grouped by day, five rows shown. Not moving grouped by reason with counts, each group collapsed to its first three.
- **Plan** opens with the milestone ladder as a horizontal stepper (closed, current, next), then the plan map. On the map, smaller pills, lighter lane separators, module names in a calm label style, no zebra striping.
- **Delivery** board cards show module, id and a two-line name with generous padding; columns get a subtle tinted background instead of borders.
- **Work package page** gets a header block (id, name, status, milestones) with real space around it; the proof grid lays out horizontally or as a compact matrix that fills its width.
- **Machinery and Retro** keep their tables, restyled: no vertical rules, quiet header row, right-aligned tabular numbers, row hover.

## What stays

Everything REVIEW.md fixed: the information on each screen, the glyphs and contrast, focus visibility, keyboard support on the map and timeline, the popovers, reduced motion, reflow at 320px, light and dark modes, and a URL per page.
